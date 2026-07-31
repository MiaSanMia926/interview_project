"""
评估Agent - 负责评估用户回答

依赖关系：
    EvaluatorAgent 不直接访问 RAG，而是通过 KnowledgeAgent 检索相关知识/标准答案片段，
    作为评分依据的参考（见架构图：KnowledgeAgent 唯一负责和 RAG 打交道）。

v2 升级：
    - Pydantic 结构化输出 EvaluationResult
    - evaluate_structured() 使用 with_structured_output（适用于支持 tool-calling 的模型）
    - evaluate() 保持向后兼容，主路径用 JSON-prompt + _extract_json（最稳定），
      结构化输出作为可选增强路径
    - 内部使用 _invoke_with_retry 提升 API 调用稳定性
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser

from agents.base import BaseAgent
from agents.knowledge import KnowledgeAgent


# ──────────────────────────────────────────────
#  Pydantic 结构化输出 Schema
# ──────────────────────────────────────────────

class DimensionScores(BaseModel):
    """四维度评分"""
    accuracy: float = Field(description="准确性：技术概念是否正确，0-100")
    completeness: float = Field(description="完整性：是否覆盖关键知识点，0-100")
    logic: float = Field(description="逻辑性：表达是否有条理、层次清晰，0-100")
    expression: float = Field(description="表达能力：语言是否流畅、专业，0-100")


class EvaluationResult(BaseModel):
    """评估结果 — 用于 with_structured_output"""
    score: float = Field(description="总分，四个维度的加权平均，0-100")
    dimensions: DimensionScores = Field(description="四维度详细得分")
    strengths: List[str] = Field(description="优点列表，2-3条")
    improvements: List[str] = Field(description="改进建议列表，2-3条")
    feedback: str = Field(description="详细反馈文字，1-3句话")


# ──────────────────────────────────────────────
#  EvaluatorAgent
# ──────────────────────────────────────────────

class EvaluatorAgent(BaseAgent):
    """评估Agent"""

    def __init__(self, knowledge_agent: Optional[KnowledgeAgent] = None):
        # 评估用低温度，保证稳定性和可复现性
        super().__init__(temperature=0.3)

        self.knowledge_agent = knowledge_agent or KnowledgeAgent()
        self._json_parser = JsonOutputParser()
        self._pydantic_parser = PydanticOutputParser(pydantic_object=EvaluationResult)

        # JSON 格式 prompt — 主路径，最稳定（带明确 JSON 格式指令）
        self.evaluate_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是资深技术面试评估专家。请对候选人的回答进行深入、细致、严格的逐维度评估。

问题类型：{question_type}
问题分类：{category}

参考资料（来自真实题库/知识库检索，若为空则忽略此部分，凭你的专业知识评估）：
{reference_material}

━━━━━━━━━━━━━━━━
评估维度（每项 0-100 分，请根据下述细分标准严格打分）：
━━━━━━━━━━━━━━━━

1. accuracy（准确性）：
   - 90-100：技术概念完全正确，术语使用精准，无任何事实性错误
   - 70-89：主要概念正确，有 1-2 处轻微偏差或不精确表述
   - 50-69：部分正确但有明显错误或混淆
   - 0-49：核心概念错误或答非所问

2. completeness（完整性）：
   - 90-100：覆盖所有关键知识点，有深度展开和延伸
   - 70-89：覆盖主要知识点，但缺少部分细节或边缘场景
   - 50-69：只涉及部分要点，遗漏明显的关键内容
   - 0-49：只触及皮毛或完全遗漏核心内容

3. logic（逻辑性）：
   - 90-100：条理清晰，层层递进，因果关系明确，有"总-分-总"结构
   - 70-89：逻辑基本通顺，但部分段落衔接可优化
   - 50-69：逻辑跳跃，缺乏连贯性或存在自相矛盾
   - 0-49：逻辑混乱，无法形成有效论证

4. expression（表达能力）：
   - 90-100：语言精炼专业，善用技术术语，举例恰当，有量化数据支撑
   - 70-89：表达清晰但略显平淡，缺少亮点
   - 50-69：表达模糊或冗余，专业术语使用不当
   - 0-49：表达困难，严重影响理解

如果参考资料中有相关标准内容，请重点参考它来判断 accuracy 和 completeness。

总分 score = (accuracy × 0.35 + completeness × 0.30 + logic × 0.20 + expression × 0.15)，四舍五入保留 1 位小数。

━━━━━━━━━━━━━━━━
输出要求：
━━━━━━━━━━━━━━━━

strengths：列出 2-3 个具体优点，每条需包含"做到了什么 + 为什么是亮点"，每条 15-40 字。
improvements：列出 2-3 条具体改进建议，每条需包含"当前不足 + 如何改进 + 预期效果"，每条 15-50 字。
feedback：写一段 80-200 字的总结性评语，需包含：
  ① 整体评价（一句话总结表现水平）
  ② 最突出的亮点（引用 strengths 中的内容具体展开）
  ③ 最需要改进的点（引用 improvements 中的内容，给出具体学习方向）

请严格按照以下JSON格式输出，不要输出任何JSON以外的文字、说明或代码块标记：
{{
    "score": 数字,
    "dimensions": {{
        "accuracy": 数字,
        "completeness": 数字,
        "logic": 数字,
        "expression": 数字
    }},
    "strengths": ["具体优点1", "具体优点2"],
    "improvements": ["具体改进建议1", "具体改进建议2"],
    "feedback": "详细评语，80-200字"
}}
"""),
            ("human", """问题：{question}

候选人回答：{user_answer}

请对这个回答做逐维度深度评估，严格按照要求的 JSON 格式输出。"""),
        ])

        # 结构化输出 prompt — 增强路径，用于 with_structured_output（无需 JSON 格式指令）
        self.evaluate_structured_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是资深技术面试评估专家。请对候选人的回答进行客观、严格的评估。

问题类型：{question_type}
问题分类：{category}

参考资料（来自真实题库/知识库检索，若为空则忽略此部分，凭你的专业知识评估）：
{reference_material}

评估维度（每项0-100分）：
1. accuracy - 准确性：技术概念是否正确
2. completeness - 完整性：是否覆盖关键知识点
3. logic - 逻辑性：表达是否有条理、层次清晰
4. expression - 表达能力：语言是否流畅、专业

如果参考资料中有相关标准内容，请重点参考它来判断 accuracy 和 completeness。
"""),
            ("human", """问题：{question}

候选人回答：{user_answer}

请评估这个回答。"""),
        ])

    # ──────────────────────────────────────────────
    #  公开接口
    # ──────────────────────────────────────────────

    def evaluate(
        self,
        question: str,
        user_answer: str,
        question_type: str,
        category: str,
    ) -> Dict:
        """
        评估用户回答（LCEL 管道：prompt | llm | JsonOutputParser）。

        主路径：JSON-prompt + JsonOutputParser，模型输出直接被解析成 dict，
        省去 _extract_json 的正则兜底；解析失败再走 _parse_from_raw 兜底。
        返回：评估结果字典，包含 score / dimensions / strengths / improvements / feedback
        """
        reference_docs = self.knowledge_agent.retrieve(question, top_k=2)
        reference_material = self._format_reference(reference_docs)

        # 构建 LCEL 管道并在带重试的入口调用
        chain = self._build_chain(self.evaluate_prompt, self._json_parser)
        try:
            parsed = self._invoke_chain(chain, {
                "question": question,
                "user_answer": user_answer,
                "question_type": question_type,
                "category": category,
                "reference_material": reference_material,
            })
            if isinstance(parsed, dict) and parsed.get("score") is not None:
                result = self._dict_to_result(parsed)
                return self._result_to_dict(result)
        except Exception:
            pass

        # 兜底：管道解析失败时回退到原始文本提取
        raw_text = self._invoke_with_retry(
            self.evaluate_prompt.format_messages(
                question=question,
                user_answer=user_answer,
                question_type=question_type,
                category=category,
                reference_material=reference_material,
            )
        )
        result = self._parse_from_raw(raw_text)
        return self._result_to_dict(result)

    def evaluate_structured(
        self,
        question: str,
        user_answer: str,
        question_type: str,
        category: str,
    ) -> EvaluationResult:
        """
        评估用户回答 - 返回强类型 Pydantic 对象。

        使用 with_structured_output（依赖模型的 tool-calling 能力）。
        若模型不支持，自动降级为 JSON-prompt + 解析。
        """
        reference_docs = self.knowledge_agent.retrieve(question, top_k=2)
        reference_material = self._format_reference(reference_docs)

        # 优先尝试结构化输出（clean prompt，不包含 JSON 格式指令）
        try:
            messages = self.evaluate_structured_prompt.format_messages(
                question=question,
                user_answer=user_answer,
                question_type=question_type,
                category=category,
                reference_material=reference_material,
            )
            return self._invoke_structured(messages, EvaluationResult)
        except Exception:
            pass

        # 降级：LCEL 管道（JsonOutputParser）+ 文本兜底
        chain = self._build_chain(self.evaluate_prompt, self._json_parser)
        try:
            parsed = self._invoke_chain(chain, {
                "question": question,
                "user_answer": user_answer,
                "question_type": question_type,
                "category": category,
                "reference_material": reference_material,
            })
            if isinstance(parsed, dict) and parsed.get("score") is not None:
                return self._dict_to_result(parsed)
        except Exception:
            pass

        raw_text = self._invoke_with_retry(
            self.evaluate_prompt.format_messages(
                question=question,
                user_answer=user_answer,
                question_type=question_type,
                category=category,
                reference_material=reference_material,
            )
        )
        return self._parse_from_raw(raw_text)

    def evaluate_pydantic(
        self,
        question: str,
        user_answer: str,
        question_type: str,
        category: str,
    ) -> EvaluationResult:
        """
        使用 PydanticOutputParser 约束模型输出标准 JSON（考核选项 D 合格线要求）。

        构建 prompt | llm | PydanticOutputParser 管道，
        直接返回 EvaluationResult Pydantic 对象。
        失败则降级到 _parse_from_raw 兜底。
        """
        reference_docs = self.knowledge_agent.retrieve(question, top_k=2)
        reference_material = self._format_reference(reference_docs)

        chain = self._build_chain(self.evaluate_prompt, self._pydantic_parser)
        try:
            result = self._invoke_chain(chain, {
                "question": question,
                "user_answer": user_answer,
                "question_type": question_type,
                "category": category,
                "reference_material": reference_material,
            })
            if isinstance(result, EvaluationResult):
                return result
        except Exception:
            pass

        raw_text = self._invoke_with_retry(
            self.evaluate_prompt.format_messages(
                question=question,
                user_answer=user_answer,
                question_type=question_type,
                category=category,
                reference_material=reference_material,
            )
        )
        return self._parse_from_raw(raw_text)

    # ──────────────────────────────────────────────
    #  内部方法
    # ──────────────────────────────────────────────

    def _parse_from_raw(self, raw_text: str) -> EvaluationResult:
        """
        从 LLM 原始文本解析评估结果。
        先用 _extract_json 尝试，失败则返回 0 分兜底。
        """
        try:
            parsed = self._extract_json(raw_text)
        except ValueError:
            return EvaluationResult(
                score=0,
                dimensions=DimensionScores(accuracy=0, completeness=0, logic=0, expression=0),
                strengths=[],
                improvements=["评估结果解析失败，请重试"],
                feedback=raw_text[:500],
            )
        return self._dict_to_result(parsed)

    @staticmethod
    def _dict_to_result(parsed: Dict) -> EvaluationResult:
        """把已经解析好的 dict 封装成 EvaluationResult Pydantic 对象"""
        dims = parsed.get("dimensions", {}) or {}
        return EvaluationResult(
            score=float(parsed.get("score", 0)),
            dimensions=DimensionScores(
                accuracy=float(dims.get("accuracy", 0)),
                completeness=float(dims.get("completeness", 0)),
                logic=float(dims.get("logic", 0)),
                expression=float(dims.get("expression", 0)),
            ),
            strengths=parsed.get("strengths", []),
            improvements=parsed.get("improvements", []),
            feedback=str(parsed.get("feedback", "")),
        )

    @staticmethod
    def _result_to_dict(result: EvaluationResult) -> Dict:
        """将 Pydantic 对象转为 dict（向后兼容）"""
        return {
            "score": result.score,
            "dimensions": {
                "accuracy": result.dimensions.accuracy,
                "completeness": result.dimensions.completeness,
                "logic": result.dimensions.logic,
                "expression": result.dimensions.expression,
            },
            "strengths": result.strengths,
            "improvements": result.improvements,
            "feedback": result.feedback,
        }

    @staticmethod
    def _format_reference(docs: List[Dict]) -> str:
        if not docs:
            return "（无检索结果）"
        lines = []
        for i, doc in enumerate(docs, 1):
            lines.append(f"{i}. {doc.get('content', '')}（来源：{doc.get('source', '未知')}）")
        return "\n".join(lines)

    async def generate_feedback_stream(
        self,
        question: str,
        user_answer: str,
        evaluation: Dict,
    ):
        """
        基于已计算出的评估结果，流式生成一段自然语言点评。

        用法：先调用 evaluate() 拿到分数和各维度得分，
        再调用这个方法，边生成边把点评文字传给前端展示打字机效果。
        """
        feedback_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位资深技术面试官，请针对候选人的这次回答，
用自然、口语化、有温度的方式写一段详细点评（3-5句话）。

问题：{question}
候选人回答：{user_answer}
评分结果：总分{score}分，准确性{accuracy}，完整性{completeness}，逻辑性{logic}，表达能力{expression}
优点：{strengths}
待改进：{improvements}

要求：像面试官当面反馈一样自然，不要机械地复述分数，
要结合候选人的具体回答内容给出有针对性的点评。"""),
            ("human", "请生成点评。"),
        ])

        chain = self._build_chain(feedback_prompt, self._str_parser)
        dimensions = evaluation.get("dimensions", {})
        async for piece in self._astream_chain(chain, {
            "question": question,
            "user_answer": user_answer,
            "score": evaluation.get("score", 0),
            "accuracy": dimensions.get("accuracy", 0),
            "completeness": dimensions.get("completeness", 0),
            "logic": dimensions.get("logic", 0),
            "expression": dimensions.get("expression", 0),
            "strengths": "、".join(evaluation.get("strengths", [])),
            "improvements": "、".join(evaluation.get("improvements", [])),
        }):
            yield piece
