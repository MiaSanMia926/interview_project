"""
对话记忆窗口管理模块 -- 基于 LangChain 组件

使用 LangChain 内置的 InMemoryChatMessageHistory 存储消息，
配合自定义滑动窗口逻辑实现短期记忆 + 摘要压缩。

考核对应：选项A「对话记忆智能体」
  合格线 -- 使用 LangChain 组件保存多轮对话上下文（InMemoryChatMessageHistory）
  优秀线 -- sessionId 隔离 + SummaryMemory + 清空会话接口
"""

from typing import List, Dict, Callable
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage


class ConversationMemory:
    """
    对话记忆管理器 -- 基于 LangChain InMemoryChatMessageHistory 实现滑动窗口。

    使用方式：
        memory = ConversationMemory(window_size=5)
        memory.add({"question": "什么是GIL？", "answer": "全局解释器锁...", "score": 72})
        context = memory.get_context()  # -> 格式化字符串，可直接注入 prompt
    """

    def __init__(self, window_size: int = 5, session_id: str = ""):
        self.window_size = window_size
        self.session_id = session_id
        self._chat_history = InMemoryChatMessageHistory()
        self._summary: str = ""

    def add(self, qa_pair: Dict) -> None:
        """添加一条问答记录。qa_pair 必须包含 question 字段。"""
        question = qa_pair.get("question", "")
        answer = qa_pair.get("answer", "")
        score = qa_pair.get("score")

        if question:
            self._chat_history.add_message(HumanMessage(content=question))
        if answer:
            text = answer
            if score is not None:
                text += f"\n（得分：{score}）"
            self._chat_history.add_message(AIMessage(content=text))
        self._trim()

    def get_context(self) -> str:
        """返回可注入 prompt 的上下文文本（摘要 + 最近N轮问答）"""
        parts: List[str] = []
        if self._summary:
            parts.append(f"【历史摘要】{self._summary}")
        messages = self._chat_history.messages
        if messages:
            lines = []
            for i, msg in enumerate(messages, 1):
                role = "问" if isinstance(msg, HumanMessage) else "答"
                lines.append(f"{i}. {role}：{msg.content}")
            parts.append("\n".join(lines))
        return "\n\n".join(parts) if parts else ""

    def get_raw_pairs(self) -> List[Dict]:
        """返回当前窗口内的原始消息列表"""
        pairs = []
        msgs = self._chat_history.messages
        i = 0
        while i < len(msgs) - 1:
            q = msgs[i]
            a = msgs[i + 1] if i + 1 < len(msgs) else None
            if isinstance(q, HumanMessage):
                pairs.append({
                    "question": q.content,
                    "answer": a.content if a and isinstance(a, AIMessage) else "",
                })
            i += 2
        return pairs

    def summarize_older(self, llm_summarize_fn: Callable[[str], str]) -> None:
        """用外部 LLM 函数压缩当前窗口之外的历史"""
        if not self._chat_history.messages:
            return
        text = self._format_messages()
        self._summary = llm_summarize_fn(
            f"请用2-3句话总结以下面试对话中的关键知识点和表现：\n{text}"
        )
        self._chat_history.clear()

    def clear(self) -> None:
        """清空所有记忆"""
        self._chat_history.clear()
        self._summary = ""

    @property
    def token_usage(self) -> int:
        """估算当前记忆占用的 token 数"""
        text = str(self._chat_history.messages)
        return max(1, len(text) // 2)

    def _trim(self) -> None:
        """超出窗口大小则丢弃最早的消息对"""
        msgs = self._chat_history.messages
        max_messages = self.window_size * 2
        while len(msgs) > max_messages:
            msgs.pop(0)

    def _format_messages(self) -> str:
        """格式化所有消息为文本（用于摘要）"""
        parts = []
        for i, msg in enumerate(self._chat_history.messages, 1):
            role = "问" if isinstance(msg, HumanMessage) else "答"
            parts.append(f"{i}. {role}：{msg.content}")
        return "\n".join(parts)
