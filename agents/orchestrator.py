"""
Agent协调器 - 基于 LangGraph 状态机管理 Multi-Agent 协作

v2 升级：
    - 用 LangGraph StateGraph 替代手写 if-else 分支
    - 5 个节点：generate_question / evaluate_answer / decide_next / generate_followup / summarize
    - 条件边实现追问循环 + 动态换题
    - 保持 run_interview_round() 接口不变（向后兼容）
    - 新增 compile_graph() 暴露底层 graph 供高级使用
"""

from typing import Dict, List, Optional, Literal, Any, TypedDict

from langgraph.graph import StateGraph, START, END

from agents.interviewer import InterviewerAgent
from agents.evaluator import EvaluatorAgent
from agents.knowledge import KnowledgeAgent
from agents.planner import PlannerAgent
from agents.memory import ConversationMemory

# 追问触发阈值：低于该分数才考虑追问
FOLLOWUP_SCORE_THRESHOLD = 70


# ──────────────────────────────────────────────
#  LangGraph 状态定义
# ──────────────────────────────────────────────

class InterviewState(TypedDict, total=False):
    """面试状态 — LangGraph 的全局 State"""

    # 面试元信息
    interview_id: str
    target_company: str
    target_position: str
    tech_stack: List[str]
    interview_mode: str

    # 进度控制
    current_question_index: int
    max_questions: int
    max_followups: int
    current_followup_count: int

    # 当前轮次数据
    current_question: str
    current_answer: str
    current_category: str

    # 历史
    previous_qa: List[Dict[str, Any]]

    # 输出
    action: str  # "next" | "followup" | "end"
    message: str
    evaluation: Optional[Dict[str, Any]]

    # 记忆（可选，由外部注入）
    memory: Any  # ConversationMemory 实例


# ──────────────────────────────────────────────
#  AgentOrchestrator
# ──────────────────────────────────────────────

class AgentOrchestrator:
    """
    Agent协调器 - 基于 LangGraph 管理多个Agent协作

    架构：KnowledgeAgent 是唯一直接对接 RAG 的Agent。
    Orchestrator 只创建一个 KnowledgeAgent 实例，注入给
    Interviewer / Evaluator / Planner 共用，避免每个Agent各自
    重复初始化一份RAG连接。

    使用方式（向后兼容）：
        orchestrator = AgentOrchestrator()
        result = orchestrator.run_interview_round(state)

    高级用法（直接操作 graph）：
        graph = orchestrator.compile_graph()
        result = graph.invoke(state)
    """

    def __init__(self):
        self.knowledge = KnowledgeAgent()
        self.interviewer = InterviewerAgent(knowledge_agent=self.knowledge)
        self.evaluator = EvaluatorAgent(knowledge_agent=self.knowledge)
        self.planner = PlannerAgent(knowledge_agent=self.knowledge)
        self._graph = self._build_graph()

    # ──────────────────────────────────────────────
    #  公开接口（向后兼容）
    # ──────────────────────────────────────────────

    def run_interview_round(self, state: Dict) -> Dict:
        """
        执行一轮面试（生成问题 + 评估回答 + 决定下一步）

        参数 state 需要包含：
            interview_id, target_company, target_position, tech_stack,
            interview_mode, current_question_index, max_questions,
            max_followups, previous_qa

        以及当前这一轮的问答（如果是评估阶段，需要传入）：
            current_question: 当前问题
            current_answer: 用户刚提交的回答
            current_followup_count: 当前问题已追问次数（默认0）

        返回：
            {
                "action": "followup" / "next" / "end",
                "message": 追问内容 或 新问题 或 结束语,
                "evaluation": {...}  # 评估结果，start阶段为None
            }
        """
        # 规范化输入状态
        normalized = self._normalize_state(state)

        # 通过 LangGraph 执行
        result = self._graph.invoke(normalized)

        return {
            "action": result.get("action", "end"),
            "message": result.get("message", ""),
            "evaluation": result.get("evaluation"),
        }

    def compile_graph(self):
        """
        返回编译后的 LangGraph StateGraph，供高级用户直接操作。
        """
        return self._graph

    # ──────────────────────────────────────────────
    #  构建 LangGraph
    # ──────────────────────────────────────────────

    def _build_graph(self):
        """构建并编译 StateGraph"""
        builder = StateGraph(InterviewState)

        # 添加节点
        builder.add_node("generate_question", self._node_generate_question)
        builder.add_node("evaluate_answer", self._node_evaluate_answer)
        builder.add_node("decide_next", self._node_decide_next)
        builder.add_node("generate_followup", self._node_generate_followup)
        builder.add_node("summarize", self._node_summarize)

        # 入口路由：根据状态决定第一步走哪个节点
        builder.add_conditional_edges(
            START,
            self._route_entry,
            {
                "generate": "generate_question",
                "evaluate": "evaluate_answer",
                "end": "summarize",
            },
        )

        # generate_question 后直接结束（返回问题给用户）
        builder.add_edge("generate_question", END)

        # evaluate_answer → decide_next
        builder.add_edge("evaluate_answer", "decide_next")

        # decide_next 条件路由
        builder.add_conditional_edges(
            "decide_next",
            self._route_after_decision,
            {
                "followup": "generate_followup",
                "next": "generate_question",
                "end": "summarize",
            },
        )

        # generate_followup 后结束（返回追问给用户）
        builder.add_edge("generate_followup", END)

        # summarize 后结束
        builder.add_edge("summarize", END)

        return builder.compile()

    # ──────────────────────────────────────────────
    #  路由函数（纯逻辑，不调 LLM）
    # ──────────────────────────────────────────────

    @staticmethod
    def _route_entry(state: InterviewState) -> Literal["generate", "evaluate", "end"]:
        """入口路由：判断当前应该做什么"""
        current_question = state.get("current_question", "")
        current_answer = state.get("current_answer", "")

        if current_question and current_answer:
            return "evaluate"

        if not current_question:
            idx = state.get("current_question_index", 0)
            max_q = state.get("max_questions", 5)
            if idx >= max_q:
                return "end"
            return "generate"

        # 有问题但没回答 → 状态异常，直接结束
        return "end"

    @staticmethod
    def _route_after_decision(state: InterviewState) -> Literal["followup", "next", "end"]:
        """评估后的条件路由"""
        return state.get("action", "end")  # type: ignore[return-value]

    # ──────────────────────────────────────────────
    #  节点函数（在 LangGraph 中被调用）
    # ──────────────────────────────────────────────

    def _node_generate_question(self, state: InterviewState) -> InterviewState:
        """节点：生成下一道面试题"""
        question = self.interviewer.generate_question(
            target_company=state.get("target_company", ""),
            target_position=state.get("target_position", ""),
            tech_stack=state.get("tech_stack", []),
            question_index=state.get("current_question_index", 0),
            previous_qa=state.get("previous_qa", []),
        )
        return {
            **state,
            "current_question": question,
            "current_answer": "",
            "current_followup_count": 0,
            "action": "next",
            "message": question,
            "evaluation": None,
        }

    def _node_evaluate_answer(self, state: InterviewState) -> InterviewState:
        """节点：评估用户回答"""
        evaluation = self.evaluator.evaluate(
            question=state.get("current_question", ""),
            user_answer=state.get("current_answer", ""),
            question_type=state.get("interview_mode", "technical"),
            category=state.get("current_category", "综合"),
        )
        return {
            **state,
            "evaluation": evaluation,
        }

    @staticmethod
    def _node_decide_next(state: InterviewState) -> InterviewState:
        """节点：纯逻辑决策（不调 LLM）"""
        evaluation = state.get("evaluation", {})
        score = evaluation.get("score", 0)
        followup_count = state.get("current_followup_count", 0)
        max_followups = state.get("max_followups", 2)
        question_index = state.get("current_question_index", 0)
        max_questions = state.get("max_questions", 5)

        # 条件 1：分数低于阈值 且 追问未达上限 → 追问
        if score < FOLLOWUP_SCORE_THRESHOLD and followup_count < max_followups:
            return {
                **state,
                "action": "followup",
                "current_followup_count": followup_count + 1,
            }

        # 条件 2：还有下一题 → 换题
        next_index = question_index + 1
        if next_index < max_questions:
            return {
                **state,
                "action": "next",
                "current_question_index": next_index,
                "current_question": "",
                "current_answer": "",
                "current_followup_count": 0,
            }

        # 条件 3：全部完成 → 结束
        return {
            **state,
            "action": "end",
        }

    def _node_generate_followup(self, state: InterviewState) -> InterviewState:
        """节点：生成追问"""
        followup = self.interviewer.generate_followup(
            original_question=state.get("current_question", ""),
            user_answer=state.get("current_answer", ""),
            evaluation_result=state.get("evaluation", {}),
            followup_count=state.get("current_followup_count", 0),
        )
        return {
            **state,
            "action": "followup",
            "message": followup,
        }

    @staticmethod
    def _node_summarize(state: InterviewState) -> InterviewState:
        """节点：生成结束语"""
        return {
            **state,
            "action": "end",
            "message": "面试已完成，感谢你的参与！正在生成总结报告...",
        }

    # ──────────────────────────────────────────────
    #  辅助方法
    # ──────────────────────────────────────────────

    @staticmethod
    def _normalize_state(raw: Dict) -> InterviewState:
        """将外部传入的松散 dict 规范化为 InterviewState"""
        return {
            "interview_id": raw.get("interview_id", ""),
            "target_company": raw.get("target_company", ""),
            "target_position": raw.get("target_position", ""),
            "tech_stack": raw.get("tech_stack", []),
            "interview_mode": raw.get("interview_mode", "technical"),
            "current_question_index": raw.get("current_question_index", 0),
            "max_questions": raw.get("max_questions", 5),
            "max_followups": raw.get("max_followups", 2),
            "current_followup_count": raw.get("current_followup_count", 0),
            "current_question": raw.get("current_question", ""),
            "current_answer": raw.get("current_answer", ""),
            "current_category": raw.get("current_category", "综合"),
            "previous_qa": raw.get("previous_qa", []),
            "action": raw.get("action", ""),
            "message": raw.get("message", ""),
            "evaluation": raw.get("evaluation"),
        }

    # ──────────────────────────────────────────────
    #  图可视化（调试用）
    # ──────────────────────────────────────────────

    def render_graph(self, path: Optional[str] = None) -> str:
        """
        将状态图渲染为 Mermaid 文本。
        如果提供 path，写入文件；否则返回 Mermaid 字符串。
        """
        mermaid = self._graph.get_graph().draw_mermaid()
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(mermaid)
        return mermaid  # type: ignore[no-any-return]
