# contracts/policy.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str = ""
