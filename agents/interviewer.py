"""
面试官Agent - 负责生成问题和追问

依赖关系：
    InterviewerAgent 不直接访问 RAG，而是通过 KnowledgeAgent 检索相关题目/知识片段，
    作为出题的参考素材（见架构图：KnowledgeAgent 唯一负责和 RAG 打交道）。

v2 升级：
    - 集成 ConversationMemory：token 窗口管理对话历史，避免无上限拼接
    - 使用 _invoke_with_retry 替代 _invoke_text，提升 API 调用稳定性
    - 新增 generate_question_async / generate_followup_async 异步方法
"""

from typing import List, Dict, Optional, Union

from langchain_core.prompts import ChatPromptTemplate

from agents.base import BaseAgent
from agents.knowledge import KnowledgeAgent
from agents.memory import ConversationMemory


class InterviewerAgent(BaseAgent):
    """面试官Agent"""

    def __init__(
        self,
        knowledge_agent: Optional[KnowledgeAgent] = None,
        memory: Optional[ConversationMemory] = None,
    ):
        super().__init__(temperature=0.7)

        # 允许外部注入（AgentOrchestrator统一持有并传入），
        # 不传时自愿创建一个，方便单独测试 InterviewerAgent
        self.knowledge_agent = knowledge_agent or KnowledgeAgent()

        # 记忆管理器（可选，用于 token 感知的窗口管理）
        self.memory = memory

        self.question_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深技术面试官，正在面试「{target_position}」岗位的候选人。

目标公司：{target_company}
技术栈：{tech_stack}

参考资料（来自真实题库检索，若为空则忽略此部分，凭你的专业知识出题）：
{reference_material}

要求：
1. 生成一个高质量的面试问题，只输出问题本身，不要输出多余说明、编号或引号
2. 如果参考资料中有相关内容，优先基于参考资料出题或改编，避免凭空编造
3. 问题应考察候选人的实际能力和理解深度，避免过于基础或过于偏门
4. 结合之前的问答历史（如果有），避免重复提问相同的知识点
5. 当前是第{question_index}题（从0开始计数）

之前的问答历史：
{previous_qa_text}
"""),
            ("human", "请生成第{question_index}题的面试问题。"),
        ])

        self.followup_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深技术面试官，正在针对候选人的回答进行追问。

原始问题：{original_question}
候选人回答：{user_answer}
评估结果：{evaluation_result}
已追问次数：{followup_count}

要求：
1. 针对候选人回答中模糊、不完整或值得深挖的地方进行追问
2. 只输出追问问题本身，不要输出多余说明或引号
3. 追问应该有针对性，不要问和原问题无关的内容
"""),
            ("human", "请生成追问问题。"),
        ])

    # ──────────────────────────────────────────────
    #  公开接口 — 同步
    # ──────────────────────────────────────────────

    def generate_question(
        self,
        target_company: str,
        target_position: str,
        tech_stack: List[str],
        question_index: int,
        previous_qa: List[Dict],
    ) -> str:
        """
        生成面试问题（LCEL 管道：prompt | llm | StrOutputParser）。

        返回：
            面试问题文本（纯字符串）
        """
        previous_qa_text = self._format_previous_qa(previous_qa)

        # 向 KnowledgeAgent 请求参考资料（RAG尚未就绪时会返回空列表，不影响出题）
        query = f"{target_position} {' '.join(tech_stack)} 面试题"
        reference_docs = self.knowledge_agent.retrieve(query, top_k=3)
        reference_material = self._format_reference(reference_docs)

        # 构建 LCEL 管道并在带重试的入口调用
        chain = self._build_chain(self.question_prompt, self._str_parser)
        question = self._invoke_chain(chain, {
            "target_company": target_company,
            "target_position": target_position,
            "tech_stack": "、".join(tech_stack),
            "question_index": question_index,
            "previous_qa_text": previous_qa_text,
            "reference_material": reference_material,
        })
        return self._strip_quotes(question)

    async def generate_question_stream(
        self,
        target_company: str,
        target_position: str,
        tech_stack: List[str],
        question_index: int,
        previous_qa: List[Dict],
    ):
        """
        生成面试问题（流式版）。

        和 generate_question 用同一套prompt和检索逻辑，唯一区别是
        通过 _astream_chain 逐块产出文本，而不是等LLM整段生成完再返回。

        注意：流式模式下不做 generate_question 那样的 _strip_quotes 收尾
        清理（因为文本是一块一块吐出来的，没法在中途知道"最终结果"长什
        么样），前端展示时如果偶尔看到引号属于正常现象，不影响使用。

        用法（在异步生成器/路由里）：
            async for piece in interviewer.generate_question_stream(...):
                yield piece
        """
        previous_qa_text = self._format_previous_qa(previous_qa)

        query = f"{target_position} {' '.join(tech_stack)} 面试题"
        reference_docs = self.knowledge_agent.retrieve(query, top_k=3)
        reference_material = self._format_reference(reference_docs)

        chain = self._build_chain(self.question_prompt, self._str_parser)
        async for piece in self._astream_chain(chain, {
            "target_company": target_company,
            "target_position": target_position,
            "tech_stack": "、".join(tech_stack),
            "question_index": question_index,
            "previous_qa_text": previous_qa_text,
            "reference_material": reference_material,
        }):
            yield piece

    def generate_followup(
        self,
        original_question: str,
        user_answer: str,
        evaluation_result: Dict,
        followup_count: int,
    ) -> str:
        """
        生成追问问题（LCEL 管道：prompt | llm | StrOutputParser）。

        返回：
            追问问题文本（纯字符串）
        """
        chain = self._build_chain(self.followup_prompt, self._str_parser)
        followup = self._invoke_chain(chain, {
            "original_question": original_question,
            "user_answer": user_answer,
            "evaluation_result": evaluation_result,
            "followup_count": followup_count,
        })
        return self._strip_quotes(followup)

    # ──────────────────────────────────────────────
    #  公开接口 - 异步
    # ──────────────────────────────────────────────

    async def generate_question_async(
        self,
        target_company: str,
        target_position: str,
        tech_stack: List[str],
        question_index: int,
        previous_qa: List[Dict],
    ) -> str:
        """异步版 generate_question（同样走 LCEL 管道）"""
        previous_qa_text = self._format_previous_qa(previous_qa)

        query = f"{target_position} {' '.join(tech_stack)} 面试题"
        reference_docs = self.knowledge_agent.retrieve(query, top_k=3)
        reference_material = self._format_reference(reference_docs)

        chain = self._build_chain(self.question_prompt, self._str_parser)
        question = await self._ainvoke_chain(chain, {
            "target_company": target_company,
            "target_position": target_position,
            "tech_stack": "、".join(tech_stack),
            "question_index": question_index,
            "previous_qa_text": previous_qa_text,
            "reference_material": reference_material,
        })
        return self._strip_quotes(question)

    async def generate_followup_async(
        self,
        original_question: str,
        user_answer: str,
        evaluation_result: Dict,
        followup_count: int,
    ) -> str:
        """异步版 generate_followup（LCEL 管道）"""
        chain = self._build_chain(self.followup_prompt, self._str_parser)
        followup = await self._ainvoke_chain(chain, {
            "original_question": original_question,
            "user_answer": user_answer,
            "evaluation_result": evaluation_result,
            "followup_count": followup_count,
        })
        return self._strip_quotes(followup)

    # ──────────────────────────────────────────────
    #  记忆管理
    # ──────────────────────────────────────────────

    def set_memory(self, memory: ConversationMemory) -> None:
        """注入记忆管理器（在 __init__ 之后）"""
        self.memory = memory

    def record_qa(self, question: str, answer: str, score: Optional[float] = None) -> None:
        """向记忆中添加一条问答记录（如果已绑定 memory）"""
        if self.memory:
            record: Dict[str, Union[str, float]] = {"question": question, "answer": answer}
            if score is not None:
                record["score"] = score
            self.memory.add(record)

    # ──────────────────────────────────────────────
    #  内部辅助
    # ──────────────────────────────────────────────

    @staticmethod
    def _format_reference(docs: List[Dict]) -> str:
        if not docs:
            return "（无检索结果）"
        lines = []
        for i, doc in enumerate(docs, 1):
            lines.append(f"{i}. {doc.get('content', '')}（来源：{doc.get('source', '未知')}）")
        return "\n".join(lines)

    def _format_previous_qa(self, previous_qa: List[Dict]) -> str:
        """
        格式化问答历史。如果绑定了 ConversationMemory，使用 token 感知的窗口管理；
        否则回退到原始拼接方式。
        """
        # 优先使用 memory 的 token 感知格式化
        if self.memory and previous_qa:
            return self.memory.get_context()

        # 回退：直接拼接（保持向后兼容）
        if not previous_qa:
            return "（无）"
        lines = []
        for i, qa in enumerate(previous_qa, 1):
            lines.append(
                f"{i}. 问：{qa.get('question', '')}\n"
                f"   答：{qa.get('answer', '')}\n"
                f"   得分：{qa.get('score', '未知')}"
            )
        return "\n".join(lines)

    @staticmethod
    def _strip_quotes(text: str) -> str:
        text = text.strip()
        if len(text) >= 2 and text[0] in "\"'“" and text[-1] in "\"'”":
            text = text[1:-1].strip()
        return text
