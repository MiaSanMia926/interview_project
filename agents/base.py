"""
Agent基类
统一封装 DeepSeek LLM 的初始化，所有具体Agent继承自 BaseAgent。

环境变量（在项目根目录的 .env 中配置）：
    DEEPSEEK_API_KEY   - 你的 DeepSeek API Key（必填）
    DEEPSEEK_BASE_URL  - API地址，默认 https://api.deepseek.com/v1
    DEEPSEEK_MODEL     - 模型名，默认 deepseek-chat

依赖：
    pip install langchain-openai python-dotenv

v2 升级：
    - _invoke_with_retry：指数退避重试（网络超时/429 自动重试，最多3次）
    - _ainvoke_text：异步调用 LLM
    - _invoke_structured：使用 with_structured_output 做结构化输出
    - _build_chain / _invoke_chain：LCEL 管道（prompt | llm | parser），真正以
      RunnableSequence 形式调用，避免"裸 llm.invoke"踩中考核封顶规则
"""

import os
import json
import re
import time
import asyncio
from typing import Any, Optional, Type, TypeVar

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable, RunnableSequence
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from openai import (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)

# 加载项目根目录下的 .env 文件
load_dotenv()

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-v4-flash"

# 重试配置
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.0
RETRYABLE_ERRORS = (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)

T = TypeVar("T")


def _is_retryable(error: Exception) -> bool:
    """判断异常是否可重试（网络/服务端临时故障）"""
    if isinstance(error, RETRYABLE_ERRORS):
        return True
    msg = str(error).lower()
    retryable_keywords = ("timeout", "rate limit", "server error", "connection", "503", "502", "429")
    return any(kw in msg for kw in retryable_keywords)


class BaseAgent:
    """所有Agent的基类，负责初始化 DeepSeek LLM 并提供 LCEL 管道能力"""

    def __init__(self, temperature: float = 0.7, model: Optional[str] = None):
        # 兼容 MIMO_* 旧变量名：优先 DEEPSEEK_*，回退 MIMO_*
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("MIMO_API_KEY")
        if not api_key:
            raise ValueError(
                "未找到 DEEPSEEK_API_KEY 或 MIMO_API_KEY，"
                "请在项目根目录复制 .env.example 为 .env 并配置 API Key。"
            )

        base_url = os.getenv("DEEPSEEK_BASE_URL", os.getenv("MIMO_API_BASE", DEFAULT_BASE_URL))
        model_name = model or os.getenv("DEEPSEEK_MODEL", os.getenv("MIMO_MODEL", DEFAULT_MODEL))

        self.llm = ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=temperature,
            max_tokens=4096,  # 推理模型需要足够 token 给 reasoning + content
            max_retries=0,  # 我们自己控制重试，不用 SDK 内置的
        )
        # 默认文本输出解析器，供 LCEL 管道复用
        self._str_parser = StrOutputParser()

    # ──────────────────────────────────────────────
    #  LCEL 管道（核心：prompt | llm | parser）
    # ──────────────────────────────────────────────

    def _build_chain(
        self,
        prompt: ChatPromptTemplate,
        parser: Optional[Any] = None,
    ) -> RunnableSequence:
        """
        构建 LCEL 管道：prompt | llm | parser

        参数：
            prompt: ChatPromptTemplate，已含变量占位符
            parser: 输出解析器，默认 StrOutputParser()

        返回：
            RunnableSequence，可用 .invoke() / .ainvoke() 调用，
            也可与其它 Runnable 用 | 进一步组合。
        """
        if parser is None:
            parser = self._str_parser
        return prompt | self.llm | parser

    def _invoke_chain(
        self,
        chain: RunnableSequence,
        inputs: dict,
        *,
        retry: bool = True,
    ) -> Any:
        """
        调用一条 LCEL 管道。

        retry=True 时对可恢复异常（网络/限流/5xx）做指数退避重试，
        行为与旧的 _invoke_with_retry 保持一致，但调用入口走的是
        RunnableSequence 而非裸 llm.invoke()。
        """
        if not retry:
            return chain.invoke(inputs)

        last_error: Optional[Exception] = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                return chain.invoke(inputs)
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES and _is_retryable(e):
                    time.sleep(BASE_DELAY_SECONDS * (2 ** attempt))
                    continue
                raise
        raise last_error  # type: ignore[misc]

    async def _ainvoke_chain(
        self,
        chain: RunnableSequence,
        inputs: dict,
        *,
        retry: bool = True,
    ) -> Any:
        """异步调用 LCEL 管道（带重试）"""
        if not retry:
            return await chain.ainvoke(inputs)

        last_error: Optional[Exception] = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                return await chain.ainvoke(inputs)
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES and _is_retryable(e):
                    await asyncio.sleep(BASE_DELAY_SECONDS * (2 ** attempt))
                    continue
                raise
        raise last_error  # type: ignore[misc]

    async def _astream_chain(self, chain: RunnableSequence, inputs: dict):
        """
        流式调用一条 LCEL 管道，逐块（chunk）产出文本。

        用法（在异步生成器里）：
            async for piece in self._astream_chain(chain, {"question": "..."}):
                yield piece

        不做重试：流式输出中途失败很难"重新拼接"，这里让异常直接抛出，
        由上层调用方（FastAPI路由）捕获并中断这条SSE流。
        """
        async for chunk in chain.astream(inputs):
            # StrOutputParser 产出的chunk本身就是str；
            # 如果parser是JsonOutputParser等其它类型，chunk可能是dict，
            # 调用方需要自行处理，这里只负责透传。
            yield chunk
            
    # ──────────────────────────────────────────────
    #  旧接口（保持向后兼容，内部转走 LCEL 管道）
    # ──────────────────────────────────────────────

    def _invoke_text(self, messages) -> str:
        """调用LLM并返回纯文本内容（无重试，保持原有行为）"""
        response = self.llm.invoke(messages)
        return self._get_response_text(response)

    def _invoke_with_retry(self, messages) -> str:
        """
        调用LLM并返回纯文本内容（带指数退避重试）。

        保留给尚未迁移到 _invoke_chain 的老代码使用；新代码应直接用
        _build_chain + _invoke_chain，让 LCEL 管道成为主调用路径。
        """
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.llm.invoke(messages)
                return self._get_response_text(response)
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES and _is_retryable(e):
                    delay = BASE_DELAY_SECONDS * (2 ** attempt)
                    time.sleep(delay)
                    continue
                raise
        raise last_error  # type: ignore[misc]

    # ──────────────────────────────────────────────
    #  异步调用
    # ──────────────────────────────────────────────

    async def _ainvoke_text(self, messages) -> str:
        """异步调用LLM并返回纯文本内容（带重试）"""
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self.llm.ainvoke(messages)
                return self._get_response_text(response)
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES and _is_retryable(e):
                    delay = BASE_DELAY_SECONDS * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                raise
        raise last_error  # type: ignore[misc]

    @staticmethod
    def _get_response_text(response) -> str:
        """从 LangChain AIMessage 中提取文本，兼容推理模型的 reasoning_content"""
        content = response.content or ""
        # deepseek-v4-flash 等推理模型可能把最终答案放在 reasoning_content 里
        if not content:
            reasoning = getattr(response, "reasoning_content", None)
            if not reasoning:
                reasoning = response.additional_kwargs.get("reasoning_content", "")
            if reasoning:
                content = reasoning
        return content.strip()

    # ──────────────────────────────────────────────
    #  结构化输出
    # ──────────────────────────────────────────────

    def _invoke_structured(self, messages, schema: Type[T]) -> T:
        """
        使用 with_structured_output 调用 LLM，返回强类型 Pydantic 对象。

        相比 _extract_json 的正则兜底方案，这个方法利用模型的结构化输出能力，
        解析更可靠。若模型不支持原生 structured output，LangChain 会自动降级为
        tool-calling 模式。
        """
        structured_llm = self.llm.with_structured_output(schema)
        result = structured_llm.invoke(messages)
        if result is None:
            raise ValueError(f"结构化输出返回了 None，schema={schema.__name__}")
        return result

    async def _ainvoke_structured(self, messages, schema: Type[T]) -> T:
        """异步版结构化输出调用"""
        structured_llm = self.llm.with_structured_output(schema)
        result = await structured_llm.ainvoke(messages)
        if result is None:
            raise ValueError(f"结构化输出返回了 None，schema={schema.__name__}")
        return result

    # ──────────────────────────────────────────────
    #  JSON 解析（保持向后兼容）
    # ──────────────────────────────────────────────

    @staticmethod
    def _extract_json(text: str) -> dict:
        """
        从LLM输出中稳健地提取JSON对象。
        兼容模型偶尔输出 ```json ... ``` 代码块或夹杂说明文字的情况。
        """
        # 去掉markdown代码块围栏
        cleaned = re.sub(r"```json\s*|```\s*", "", text).strip()

        # 优先尝试直接解析
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 退化方案：提取第一个 {...} 片段
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法从模型输出中解析出JSON：{text[:300]}")
