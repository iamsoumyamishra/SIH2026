"""Lightweight agent memory (working memory / scratchpad).

Stores structured observations accumulated during a run for the MVP. This is
an explicit, bounded structure rather than an unbounded free-form loop state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Memory:
    observations: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def observe(self, source: str, data: Any) -> None:
        self.observations.append({"source": source, "data": data})

    def note(self, text: str) -> None:
        self.notes.append(text)

    def observations_text(self, source: str | None = None) -> str:
        items = (
            [o for o in self.observations if o["source"] == source]
            if source
            else self.observations
        )
        parts = []
        for i, o in enumerate(items, 1):
            parts.append(f"[{o['source']}] {o['data']}")
        return "\n".join(parts)

    def clear(self) -> None:
        self.observations.clear()
        self.notes.clear()
