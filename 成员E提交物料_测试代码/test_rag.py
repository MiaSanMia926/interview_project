from pathlib import Path

from rag.engine import RAGEngine
from rag.standard_answers import StandardAnswerDB


ROOT = Path(__file__).resolve().parents[1]


def test_rag_load_and_search(tmp_path):
    engine = RAGEngine(persist_directory=str(tmp_path / "chroma"))
    count = engine.load_documents(str(ROOT / "data" / "questions" / "interview_questions.json"))
    assert count > 0

    results = engine.search(query="Redis 缓存穿透 怎么解决", tech_stack=["Redis"], k=3)
    assert results
    assert {"id", "question", "category", "difficulty", "score"}.issubset(results[0])
    assert results[0]["category"] == "Redis"


def test_rag_mmr_and_prompt_cache(tmp_path):
    engine = RAGEngine(persist_directory=str(tmp_path / "chroma"))
    engine.load_documents(str(ROOT / "data" / "questions" / "interview_questions.json"))

    results = engine.search_with_mmr("系统设计 Redis 高并发", k=3)
    assert len(results) == 3

    first = engine.cached_prompt("redis-cache", "请生成 Redis 缓存问题")
    second = engine.cached_prompt("redis-cache", "请生成 Redis 缓存问题")
    assert first["cached"] is False
    assert second["cached"] is True
    assert second["stats"]["saved_tokens"] > 0


def test_standard_answers():
    db = StandardAnswerDB(str(ROOT / "data" / "standard_answers.json"))
    answer = db.get_standard_answer("redis_002")
    assert answer is not None
    assert db.get_by_category("Redis")
