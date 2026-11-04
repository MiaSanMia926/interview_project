"""
Agent 单元测试 —— 直接测试 agents/ 模块，不经过 backend/chains 包装层。

注意：这些测试会真实调用 LLM，属于集成测试。
需要 DEEPSEEK_API_KEY 配置在 .env 中，且网络可达才能通过。
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.interviewer import InterviewerAgent
from agents.evaluator import EvaluatorAgent
from agents.memory import ConversationMemory
from langchain_core.runnables import RunnableSequence

class TestInterviewerAgent:
    """面试官 Agent 测试"""

    def setup_method(self):
        self.agent = InterviewerAgent()

    def test_generate_question(self):
        result = self.agent.generate_question(
            target_company="字节跳动",
            target_position="后端工程师",
            tech_stack=["Python", "Redis"],
            question_index=0,
            previous_qa=[],
        )
        assert isinstance(result, str)
        assert len(result) > 10

    def test_uses_lcel_pipeline(self):
        """验证核心链路真的是 LCEL 管道（RunnableSequence），不是裸 llm.invoke()"""
        chain = self.agent._build_chain(self.agent.question_prompt, self.agent._str_parser)
        assert isinstance(chain, RunnableSequence)
    
    def test_generate_followup(self):
        result = self.agent.generate_followup(
            original_question="请介绍Redis持久化",
            user_answer="Redis有RDB和AOF两种方式",
            evaluation_result={"score": 75},
            followup_count=0,
        )
        assert isinstance(result, str)
        assert len(result) > 5

    

    @pytest.mark.asyncio
    async def test_generate_question_stream(self):
        """验证流式生成问题：能收到多个文本片段，拼接后是一段有意义的文字"""
        pieces = []
        async for piece in self.agent.generate_question_stream(
            target_company="字节跳动",
            target_position="后端工程师",
            tech_stack=["Python", "Redis"],
            question_index=0,
            previous_qa=[],
        ):
            pieces.append(piece)

        assert len(pieces) > 1  # 真正的流式应该是分成好几块，不是一次性吐出一整段
        full_text = "".join(pieces)
        assert len(full_text) > 10
        
class TestEvaluatorAgent:
    """评估 Agent 测试"""

    def setup_method(self):
        self.agent = EvaluatorAgent()

    def test_evaluate(self):
        result = self.agent.evaluate(
            question="请介绍Python",
            user_answer="Python是一种解释型语言，具有动态类型特性",
            question_type="technical",
            category="Python",
        )
        assert "score" in result
        assert "dimensions" in result
        score = result["score"]
        if score is not None:
            assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_generate_feedback_stream(self):
                    """验证流式生成点评：先有真实评分，再流式吐出点评文字"""
                    evaluation = self.agent.evaluate(
                        question="请介绍Python",
                        user_answer="Python是一种解释型语言，具有动态类型特性",
                        question_type="technical",
                        category="Python",
                    )
            
                    pieces = []
                    async for piece in self.agent.generate_feedback_stream(
                        question="请介绍Python",
                        user_answer="Python是一种解释型语言，具有动态类型特性",
                        evaluation=evaluation,
                    ):
                        pieces.append(piece)
            
                    assert len(pieces) > 1
                    full_text = "".join(pieces)
                    assert len(full_text) > 10        

class TestMemoryManager:
    """对话记忆管理器测试"""

    def setup_method(self):
        self.memory = ConversationMemory(window_size=5)

    def test_add_and_context(self):
        self.memory.add({"question": "什么是GIL？", "answer": "全局解释器锁...", "score": 72})
        context = self.memory.get_context()
        assert "GIL" in context

    def test_window_trim(self):
        """超出窗口大小（window_size轮）后，应该只保留最近的记录，丢弃最早的"""
        for i in range(10):  # 加10轮，超过window_size=5
            self.memory.add({"question": f"Q{i}", "answer": f"A{i}"})

        pairs = self.memory.get_raw_pairs()
        assert len(pairs) <= 5  # 不应该超过窗口大小
        # 最早的问答（Q0）应该已经被丢弃
        questions = [p["question"] for p in pairs]
        assert "Q0" not in questions
        # 最新的问答（Q9）应该还在
        assert "Q9" in questions

    def test_clear(self):
        """验证清空接口能真正清掉记忆"""
        self.memory.add({"question": "测试问题", "answer": "测试回答"})
        assert self.memory.get_context() != ""
        self.memory.clear()
        assert self.memory.get_context() == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
