from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class InferenceRequest:
    prompt: str
    context: dict[str, Any] | None = None
    model: str | None = None


@dataclass(frozen=True, slots=True)
class InferenceResult:
    text: str
    confidence: float = 0.0
    metadata: dict[str, Any] | None = None


class InferenceBackend(Protocol):
    async def infer(self, request: InferenceRequest) -> InferenceResult:
        ...
