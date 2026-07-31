"""
学习规划Agent（P2 可选）
职责：基于评估历史，识别薄弱知识点，生成学习路径建议。

依赖关系：
    PlannerAgent 不直接访问 RAG，而是通过 KnowledgeAgent 检索薄弱知识点相关的学习资料，
    作为规划建议的参考（见架构图：KnowledgeAgent 唯一负责和 RAG 打交道）。

v2 升级：
    - 使用 Pydantic 结构化输出 StudyPlan，替代 JSON 正则解析
    - 使用 _invoke_with_retry 提升稳定性
    - 集成 ConversationMemory（可选）
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from agents.base import BaseAgent
from agents.knowledge import KnowledgeAgent
from agents.memory import ConversationMemory


# ──────────────────────────────────────────────
#  Pydantic 结构化输出 Schema
# ──────────────────────────────────────────────

class StudyPlanItem(BaseModel):
    """学习计划中的一项"""
    topic: str = Field(description="学习主题")
    priority: str = Field(description="优先级：high/medium/low")
    suggestion: str = Field(description="具体学习建议")


class StudyPlan(BaseModel):
    """学习规划 — 用于 with_structured_output"""
    strengths: List[str] = Field(description="核心优势列表，2-3条，每条包含具体领域和表现")
    weak_points: List[str] = Field(description="核心薄弱点列表，2-3条，每条包含具体领域和问题")
    study_plan: List[StudyPlanItem] = Field(description="学习计划列表")
    summary: str = Field(description="整体总结，2-3句话")


# ──────────────────────────────────────────────
#  PlannerAgent
# ──────────────────────────────────────────────

class PlannerAgent(BaseAgent):
    """学习规划Agent"""

    def __init__(self, knowledge_agent: Optional[KnowledgeAgent] = None):
        super().__init__(temperature=0.5)

        self.knowledge_agent = knowledge_agent or KnowledgeAgent()

        self.plan_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深技术总监和职业发展导师，请根据候选人的面试历史，生成个性化诊断报告。

参考学习资料（来自知识库检索，若为空则忽略此部分）：
{reference_material}

请深入分析候选人的表现，识别其核心优势和薄弱点，并给出针对性的学习建议。

请严格按照以下JSON格式输出，不要输出任何JSON以外的文字或代码块标记：
{{
    "strengths": ["核心优势1（具体领域+表现）", "核心优势2"],
    "weak_points": ["核心薄弱点1（具体领域+问题）", "核心薄弱点2"],
    "study_plan": [
        {{"topic": "学习主题", "priority": "high/medium/low", "suggestion": "具体学习建议"}}
    ],
    "summary": "整体总结，2-3句话"
}}

要求：
- strengths：列出2-3条核心优势，每条需包含具体技术领域和表现亮点（如"系统架构设计：能清晰描述微服务拆分原则"）
- weak_points：列出2-3条核心薄弱点，每条需包含具体技术领域和问题（如"Redis持久化机制：混淆了RDB和AOF的触发时机"）
- study_plan：针对薄弱点给出具体学习建议，优先级 high 对应最需要立即攻克的短板
- 所有描述必须基于面试历史中的实际表现，不要泛泛而谈
"""),
            ("human", "面试历史：\n{qa_history}\n\n请生成个性化诊断报告，严格按照JSON格式输出。"),
        ])

    # ──────────────────────────────────────────────
    #  公开接口
    # ──────────────────────────────────────────────

    def generate_plan(self, qa_history: List[Dict]) -> Dict:
        """
        根据问答历史生成学习规划（JSON prompt 主路径 + _extract_json 解析）。

        返回：
            {"weak_points": [...], "study_plan": [...], "summary": "..."}
            study_plan 中每项为 {"topic": str, "priority": str, "suggestion": str}
        """
        history_text = "\n".join(
            f"- 问：{qa.get('question')} | 得分：{qa.get('score')}"
            for qa in qa_history
        )

        # 用低分题目的问题文本去检索相关学习资料
        weak_queries = " ".join(
            qa.get("question", "") for qa in qa_history if qa.get("score", 100) < 70
        )
        reference_docs = self.knowledge_agent.retrieve(weak_queries or "面试常见薄弱知识点", top_k=3)
        reference_material = self._format_reference(reference_docs)

        messages = self.plan_prompt.format_messages(
            qa_history=history_text or "（无历史记录）",
            reference_material=reference_material,
        )

        # 主路径：LLM 返回 JSON 文本，用 _extract_json 解析
        try:
            raw_text = self._invoke_with_retry(messages)
            parsed = self._extract_json(raw_text)
            result = self._dict_to_plan(parsed)
        except Exception:
            # 降级：尝试 structured output
            try:
                result = self._invoke_structured(messages, StudyPlan)
            except Exception:
                return {"weak_points": [], "study_plan": [], "summary": "未能生成学习规划，请稍后重试"}

        return self._plan_to_dict(result)

    def generate_plan_structured(self, qa_history: List[Dict]) -> StudyPlan:
        """
        生成学习规划 — 返回强类型 Pydantic 对象。
        """
        history_text = "\n".join(
            f"- 问：{qa.get('question')} | 得分：{qa.get('score')}"
            for qa in qa_history
        )

        weak_queries = " ".join(
            qa.get("question", "") for qa in qa_history if qa.get("score", 100) < 70
        )
        reference_docs = self.knowledge_agent.retrieve(weak_queries or "面试常见薄弱知识点", top_k=3)
        reference_material = self._format_reference(reference_docs)

        messages = self.plan_prompt.format_messages(
            qa_history=history_text or "（无历史记录）",
            reference_material=reference_material,
        )

        try:
            return self._invoke_structured(messages, StudyPlan)
        except Exception:
            raw_text = self._invoke_with_retry(messages)
            return self._parse_fallback(raw_text)

    # ──────────────────────────────────────────────
    #  内部方法
    # ──────────────────────────────────────────────

    def _parse_fallback(self, raw_text: str) -> StudyPlan:
        """从 LLM 原始文本解析学习规划（兜底）"""
        try:
            parsed = self._extract_json(raw_text)
        except ValueError:
            return StudyPlan(
                strengths=[],
                weak_points=[],
                study_plan=[],
                summary=raw_text[:500],
            )

        plan_items = []
        for item in parsed.get("study_plan", []):
            plan_items.append(StudyPlanItem(
                topic=item.get("topic", "未知"),
                priority=item.get("priority", "medium"),
                suggestion=item.get("suggestion", ""),
            ))

        return StudyPlan(
            strengths=parsed.get("strengths", []),
            weak_points=parsed.get("weak_points", []),
            study_plan=plan_items,
            summary=str(parsed.get("summary", "")),
        )

    @staticmethod
    def _plan_to_dict(plan: StudyPlan) -> Dict:
        """将 Pydantic 对象转为 dict（向后兼容）"""
        return {
            "strengths": plan.strengths,
            "weak_points": plan.weak_points,
            "study_plan": [
                {"topic": item.topic, "priority": item.priority, "suggestion": item.suggestion}
                for item in plan.study_plan
            ],
            "summary": plan.summary,
        }

    @staticmethod
    def _dict_to_plan(parsed: Dict) -> StudyPlan:
        """将 JSON 解析结果转为 StudyPlan"""
        plan_items = []
        for item in parsed.get("study_plan", []):
            plan_items.append(StudyPlanItem(
                topic=item.get("topic", "未知"),
                priority=item.get("priority", "medium"),
                suggestion=item.get("suggestion", ""),
            ))
        return StudyPlan(
            strengths=parsed.get("strengths", []),
            weak_points=parsed.get("weak_points", []),
            study_plan=plan_items,
            summary=str(parsed.get("summary", "")),
        )

    @staticmethod
    def _format_reference(docs: List[Dict]) -> str:
        if not docs:
            return "（无检索结果）"
        lines = []
        for i, doc in enumerate(docs, 1):
            lines.append(f"{i}. {doc.get('content', '')}（来源：{doc.get('source', '未知')}）")
        return "\n".join(lines)
