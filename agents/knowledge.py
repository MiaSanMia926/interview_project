from typing import Dict, List


class KnowledgeAgent:
    """知识检索Agent —— 纯本地RAG检索，不调用LLM，不需要API Key"""

    def __init__(self):
        self._rag_engine = None
        try:
            from rag.engine import RAGEngine  # 成员C的产出
            self._rag_engine = RAGEngine()
        except ImportError:
            # RAG模块尚未就绪，先降级为空检索，不阻塞其他Agent开发
            self._rag_engine = None

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        检索相关知识/题目

        返回：
            [{"content": "...", "source": "...", "score": 0.9}, ...]
            若RAG引擎未就绪，返回空列表
        """
        if self._rag_engine is None:
            return []
        return self._rag_engine.search(query, top_k=top_k)