"""Build the local RAG index from cleaned question data."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag.engine import RAGEngine
from rag.loader import QuestionLoader

QUESTION_DIR = ROOT / "data" / "questions"
CLEAN_DATASET = QUESTION_DIR / "clean_questions.json"
INDEX_DIR = ROOT / "data" / "chroma"


def main() -> None:
    loader = QuestionLoader()
    docs = loader.load_directory(QUESTION_DIR)
    count = loader.save_clean_dataset(docs, CLEAN_DATASET)

    engine = RAGEngine(persist_directory=str(INDEX_DIR))
    indexed = engine.build_index(docs)

    print(f"clean_dataset={CLEAN_DATASET}")
    print(f"clean_count={count}")
    print(f"index_directory={INDEX_DIR}")
    print(f"indexed_count={indexed}")


if __name__ == "__main__":
    main()
