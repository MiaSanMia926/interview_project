"""Document loading and cleaning utilities for the interview question bank."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List


Question = Dict[str, object]


class QuestionLoader:
    """Load, normalize, and deduplicate interview questions."""

    REQUIRED_FIELDS = {"id", "question", "category", "difficulty", "tech_stack"}

    def load(self, file_path: str | Path) -> List[Question]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Question data file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".json":
            with path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                raw = raw.get("questions", [])
            return self.clean(raw)

        if suffix == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                return self.clean(csv.DictReader(f))

        if suffix in {".jsonl", ".ndjson"}:
            rows = []
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
            return self.clean(rows)

        raise ValueError(f"Unsupported data file type: {path.suffix}")

    def load_directory(self, directory: str | Path) -> List[Question]:
        path = Path(directory)
        docs: List[Question] = []
        for file_path in sorted(path.glob("*")):
            if file_path.suffix.lower() in {".json", ".csv", ".jsonl", ".ndjson"}:
                docs.extend(self.load(file_path))
        return self.deduplicate(docs)

    def clean(self, rows: Iterable[Dict[str, object]]) -> List[Question]:
        cleaned = []
        for row in rows:
            item = dict(row)
            question = str(item.get("question", "")).strip()
            if not question:
                continue

            item["question"] = " ".join(question.split())
            item["category"] = str(item.get("category") or "General").strip()
            item["difficulty"] = self._safe_int(item.get("difficulty"), default=5)
            item["tech_stack"] = self._as_list(item.get("tech_stack") or item.get("tags"))
            item["type"] = str(item.get("type") or "technical")
            item["source"] = str(item.get("source") or "local_dataset")
            item["company"] = str(item.get("company") or "")
            item["key_points"] = self._as_list(item.get("key_points"))
            item["reference_answer"] = str(item.get("reference_answer") or "")

            if not item.get("id"):
                digest = hashlib.md5(item["question"].encode("utf-8")).hexdigest()[:10]
                item["id"] = f"question_{digest}"

            cleaned.append(item)

        return self.deduplicate(cleaned)

    def deduplicate(self, docs: Iterable[Question]) -> List[Question]:
        seen = set()
        unique = []
        for doc in docs:
            fingerprint = str(doc.get("question", "")).lower()
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            unique.append(doc)
        return unique

    def save_clean_dataset(self, docs: Iterable[Question], output_path: str | Path) -> int:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        items = list(self.deduplicate(docs))
        with path.open("w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        return len(items)

    @staticmethod
    def _safe_int(value: object, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_list(value: object) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            try:
                decoded = json.loads(value)
                if isinstance(decoded, list):
                    return [str(v).strip() for v in decoded if str(v).strip()]
            except json.JSONDecodeError:
                pass
            return [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
        return [str(value).strip()]
