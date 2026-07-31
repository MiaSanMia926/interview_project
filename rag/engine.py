"""RAG retrieval engine -- Embedding+Chroma 主路径，TF-IDF 降级。

主路径：OpenAIEmbeddings + Chroma 向量数据库（满足考核"向量化入库、相似度检索"）。
降级路径：Embedding 不可用时自动回退到 TF-IDF + 余弦相似度，保证离线环境仍可检索。
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from rag.loader import QuestionLoader


class PromptCache:
    """Track prompt cache hits and estimated token savings."""

    def __init__(self, price_per_1k_tokens: float = 0.002):
        self.price_per_1k_tokens = price_per_1k_tokens
        self.hits = 0
        self.misses = 0
        self.saved_tokens = 0

    def mark_hit(self, prompt_text: str) -> None:
        self.hits += 1
        self.saved_tokens += estimate_tokens(prompt_text)

    def mark_miss(self) -> None:
        self.misses += 1

    def stats(self) -> Dict[str, float]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "saved_tokens": self.saved_tokens,
            "estimated_saved_usd": round(self.saved_tokens / 1000 * self.price_per_1k_tokens, 6),
        }


# ──────────────────────────────────────────────
# 向量后端抽象
# ──────────────────────────────────────────────

class _VectorBackend:
    """统一向量后端接口"""
    def build(self, documents: List[Dict]) -> None: ...
    def search(self, query: str, docs: List[Dict], top_k: int) -> List[tuple]: ...
    def mmr(self, query: str, docs: List[Dict], k: int, lambda_mult: float) -> List[tuple]: ...
    @property
    def name(self) -> str: ...


class _ChromaBackend(_VectorBackend):
    """Embedding 模型 + Chroma 向量数据库（主路径）"""

    name = "embedding-chroma"

    def __init__(self, persist_directory: Path):
        import warnings
        warnings.filterwarnings("ignore", message="`langchain-community` is being sunset")
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import Chroma

        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("MIMO_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        if not api_key:
            raise ValueError("Embedding backend requires an API key")

        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        embed_kwargs = {"model": model, "api_key": api_key}
        if base_url:
            embed_kwargs["base_url"] = base_url
        self._embeddings = OpenAIEmbeddings(**embed_kwargs)
        self._Chroma = Chroma
        self._persist_directory = str(persist_directory)
        self._store = None

    def build(self, documents: List[Dict]) -> None:
        if not documents:
            self._store = None
            return
        texts = [_doc_text(d) for d in documents]
        metadatas = [{"doc_id": str(d.get("id", ""))} for d in documents]
        ids = [str(d.get("id", f"doc_{i}")) for i, d in enumerate(documents)]
        self._store = self._Chroma.from_texts(
            texts=texts, embedding=self._embeddings,
            metadatas=metadatas, ids=ids,
            persist_directory=self._persist_directory,
        )

    def search(self, query: str, docs: List[Dict], top_k: int) -> List[tuple]:
        if self._store is None:
            return []
        results = self._store.similarity_search_with_relevance_scores(query, k=top_k)
        out = []
        for doc, score in results:
            doc_id = doc.metadata.get("doc_id")
            matched = next((d for d in docs if str(d.get("id")) == doc_id), None)
            if matched:
                out.append((matched, float(score)))
        return out

    def mmr(self, query: str, docs: List[Dict], k: int, lambda_mult: float) -> List[tuple]:
        if self._store is None:
            return []
        retrieved = self._store.max_marginal_relevance_search(
            query, k=k, fetch_k=max(k * 4, k), lambda_mult=lambda_mult
        )
        out = []
        for doc in retrieved:
            doc_id = doc.metadata.get("doc_id")
            matched = next((d for d in docs if str(d.get("id")) == doc_id), None)
            if matched:
                out.append((matched, 0.0))
        return out


class _TfidfBackend(_VectorBackend):
    """TF-IDF 降级后端（离线环境使用）"""

    name = "tfidf-fallback"

    def __init__(self):
        self._vectors: List[Counter] = []
        self._df: Counter = Counter()

    def build(self, documents: List[Dict]) -> None:
        token_lists = [tokenize(_doc_text(d)) for d in documents]
        self._df = Counter()
        for tokens in token_lists:
            self._df.update(set(tokens))
        self._vectors = [self._tfidf(tokens) for tokens in token_lists]

    def search(self, query: str, docs: List[Dict], top_k: int) -> List[tuple]:
        scored = self._score(query, docs)
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def mmr(self, query: str, docs: List[Dict], k: int, lambda_mult: float) -> List[tuple]:
        scored = self._score(query, docs)
        # 先按相关性分数排序，再从最相关的一批里做多样性重排序
        # （之前这里没排序，等于在任意顺序的文档里选候选，MMR形同虚设）
        ranked = sorted(scored, key=lambda x: x[1], reverse=True)
        pool = ranked[: max(k * 4, k)]

        # doc 在 self._vectors 里的真实位置，用 id() 做映射（而不是误把 doc 本身当下标）
        doc_vec_idx = {id(doc): i for i, doc in enumerate(docs)}

        selected: List[tuple] = []
        chosen_vec_idx: List[int] = []
        while pool and len(selected) < k:
            if not selected:
                doc, sc = pool.pop(0)
                selected.append((doc, sc))
                chosen_vec_idx.append(doc_vec_idx[id(doc)])
                continue
            best_i, best_val = 0, -float("inf")
            for j, (doc, rel) in enumerate(pool):
                cand_idx = doc_vec_idx[id(doc)]
                if self._vectors and chosen_vec_idx:
                    div = max(cosine(self._vectors[cand_idx], self._vectors[c]) for c in chosen_vec_idx)
                else:
                    div = 0.0
                val = lambda_mult * rel - (1 - lambda_mult) * div
                if val > best_val:
                    best_val, best_i = val, j
            doc, sc = pool.pop(best_i)
            selected.append((doc, sc))
            chosen_vec_idx.append(doc_vec_idx[id(doc)])
        return selected

    def _score(self, query: str, docs: List[Dict]) -> List[tuple]:
        q_vec = self._tfidf(tokenize(query))
        out = []
        for i, doc in enumerate(docs):
            if i < len(self._vectors):
                sem = cosine(q_vec, self._vectors[i])
            else:
                sem = cosine(q_vec, self._tfidf(tokenize(_doc_text(doc))))
            kw = keyword_overlap(query, doc)
            score = 0.7 * sem + 0.3 * kw
            out.append((doc, round(score, 6)))
        return out

    def _tfidf(self, tokens: List[str]) -> Counter:
        tf = Counter(tokens)
        total = max(len(self._vectors) + 1, 1)
        vec = Counter()
        for token, count in tf.items():
            idf = math.log((total + 1) / (self._df.get(token, 0) + 1)) + 1
            vec[token] = count * idf
        return vec


# ──────────────────────────────────────────────
# RAGEngine
# ──────────────────────────────────────────────

class RAGEngine:
    """RAG 检索引擎 -- Embedding+Chroma 主路径，TF-IDF 降级"""

    def __init__(self, persist_directory: str = "./data/chroma"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.index_path = self.persist_directory / "question_index.json"
        self.loader = QuestionLoader()
        self.prompt_cache = PromptCache()
        self.documents: List[Dict] = []
        self._backend: Optional[_VectorBackend] = None
        self._load_index()

        if not self.documents:
            self._auto_load_questions()

    @property
    def backend_name(self) -> str:
        return self._init_backend().name

    def _init_backend(self) -> _VectorBackend:
        if self._backend is not None:
            return self._backend
        try:
            self._backend = _ChromaBackend(self.persist_directory)
            if self.documents:
                self._backend.build(self.documents)
        except Exception:
            self._backend = _TfidfBackend()
            if self.documents:
                self._backend.build(self.documents)
        return self._backend

    def load_documents(self, file_path: str) -> int:
        docs = self.loader.load(file_path)
        return self.build_index(docs)

    def build_index(self, docs: Iterable[Dict]) -> int:
        merged = {str(doc["id"]): doc for doc in self.documents}
        for doc in docs:
            merged[str(doc["id"])] = doc
        self.documents = list(merged.values())
        self._persist_index()
        self._backend = None
        backend = self._init_backend()
        try:
            backend.build(self.documents)
        except Exception:
            self._backend = _TfidfBackend()
            self._backend.build(self.documents)
        return len(self.documents)

    def search(self, query, tech_stack=None, category=None, difficulty_min=None,
               difficulty_max=None, k=5, top_k=None) -> List[Dict]:
        limit = top_k or k
        candidates = self._filter_documents(tech_stack, category, difficulty_min, difficulty_max)
        backend = self._init_backend()
        scored = backend.search(query, candidates, limit)
        return [self._format_result(doc, score) for doc, score in scored[:limit]]

    def search_with_mmr(self, query: str, k: int = 5, lambda_mult: float = 0.7) -> List[Dict]:
        backend = self._init_backend()
        scored = backend.mmr(query, self.documents, k, lambda_mult)
        return [self._format_result(doc, score) for doc, score in scored]

    def cached_prompt(self, prompt_key: str, prompt_text: str) -> Dict[str, object]:
        cache_path = self.persist_directory / "prompt_cache.json"
        cache = {}
        if cache_path.exists():
            with cache_path.open("r", encoding="utf-8") as f:
                cache = json.load(f)
        if prompt_key in cache:
            self.prompt_cache.mark_hit(prompt_text)
            return {"cached": True, "value": cache[prompt_key], "stats": self.prompt_cache.stats()}
        cache[prompt_key] = {"prompt": prompt_text, "cache_mark": f"CACHE::{prompt_key}"}
        with cache_path.open("w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        self.prompt_cache.mark_miss()
        return {"cached": False, "value": cache[prompt_key], "stats": self.prompt_cache.stats()}

    def cache_stats(self) -> Dict[str, float]:
        return self.prompt_cache.stats()

    # ── 内部方法 ──

    def _filter_documents(self, tech_stack, category, difficulty_min, difficulty_max) -> List[Dict]:
        docs = self.documents
        if tech_stack:
            wanted = {item.lower() for item in tech_stack}
            docs = [d for d in docs if wanted.intersection({str(v).lower() for v in d.get("tech_stack", [])})]
        if category:
            docs = [d for d in docs if str(d.get("category", "")).lower() == category.lower()]
        if difficulty_min is not None:
            docs = [d for d in docs if int(d.get("difficulty", 0)) >= difficulty_min]
        if difficulty_max is not None:
            docs = [d for d in docs if int(d.get("difficulty", 10)) <= difficulty_max]
        return docs

    def _format_result(self, doc: Dict, score: float) -> Dict:
        return {
            "id": doc.get("id"), "question": doc.get("question"),
            "category": doc.get("category"), "difficulty": doc.get("difficulty"),
            "tech_stack": doc.get("tech_stack", []), "score": score,
            "reference_answer": doc.get("reference_answer", ""),
            "key_points": doc.get("key_points", []),
            "metadata": {"source": doc.get("source", ""), "company": doc.get("company", ""), "type": doc.get("type", "technical")},
            "content": doc.get("reference_answer") or doc.get("question"),
            "source": doc.get("source", ""),
        }

    def _persist_index(self) -> None:
        with self.index_path.open("w", encoding="utf-8") as f:
            json.dump({"documents": self.documents}, f, ensure_ascii=False, indent=2)

    def _load_index(self) -> None:
        if not self.index_path.exists():
            return
        with self.index_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        self.documents = payload.get("documents", [])

    def _auto_load_questions(self) -> None:
        questions_dir = Path("data/questions")
        if not questions_dir.exists():
            return
        for file_path in sorted(questions_dir.glob("*.json")):
            try:
                docs = self.loader.load(str(file_path))
                if docs:
                    self.documents.extend(docs)
            except Exception:
                pass
        if self.documents:
            self._persist_index()


# ──────────────────────────────────────────────
# TF-IDF 辅助函数
# ──────────────────────────────────────────────

def _doc_text(doc: Dict) -> str:
    return " ".join([
        str(doc.get("question", "")), str(doc.get("category", "")),
        " ".join(map(str, doc.get("tech_stack", []))),
        " ".join(map(str, doc.get("key_points", []))),
        str(doc.get("reference_answer", "")),
    ])

def tokenize(text: str) -> List[str]:
    text = (text or "").lower()
    words = re.findall(r"[a-z0-9_+#.-]+|[\u4e00-\u9fff]", text)
    return [w for w in words if w.strip()]

def cosine(left: Counter, right: Counter) -> float:
    if not left or not right:
        return 0.0
    common = set(left) & set(right)
    numerator = sum(left[t] * right[t] for t in common)
    ln = math.sqrt(sum(v * v for v in left.values()))
    rn = math.sqrt(sum(v * v for v in right.values()))
    if ln == 0 or rn == 0:
        return 0.0
    return numerator / (ln * rn)

def keyword_overlap(query: str, doc: Dict) -> float:
    qt = set(tokenize(query))
    dt = set(tokenize(" ".join([str(doc.get("category", "")), " ".join(doc.get("tech_stack", [])), str(doc.get("question", ""))])))
    if not qt:
        return 0.0
    return len(qt & dt) / len(qt)

def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text or "") / 2))
