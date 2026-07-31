"""Standard answer store used by evaluator agents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class StandardAnswerDB:
    """Load reference answers from a JSON file."""

    def __init__(self, db_path: str = "./data/standard_answers.json"):
        self.db_path = Path(db_path)
        self._answers = self._load()

    def get_standard_answer(self, question_id: str) -> Optional[Dict]:
        return self._answers.get(question_id)

    def get_by_category(self, category: str) -> List[Dict]:
        target = category.lower()
        return [
            answer
            for answer in self._answers.values()
            if str(answer.get("category", "")).lower() == target
        ]

    def _load(self) -> Dict[str, Dict]:
        if not self.db_path.exists():
            return {}
        with self.db_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("answers", data)
            if isinstance(data, dict):
                return {str(k): v for k, v in data.items()}
        if isinstance(data, list):
            return {
                str(item.get("question_id") or item.get("id")): item
                for item in data
                if item.get("question_id") or item.get("id")
            }
        return {}
