"""Text splitter used before building the retrieval index."""

from __future__ import annotations

from typing import List


class TextSplitter:
    """A small dependency-free character splitter with overlap."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        text = " ".join((text or "").split())
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = min(len(text), start + self.chunk_size)
            chunks.append(text[start:end])
            if end == len(text):
                break
            start = end - self.chunk_overlap
        return chunks
