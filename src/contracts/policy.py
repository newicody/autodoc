from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Decision:
    """Décision minimale d'une politique explicite."""

    allowed: bool
    reason: str = ""
