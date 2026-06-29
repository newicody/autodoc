from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class InferenceRequest:
    """Contrat futur d'une demande d'inférence."""

    prompt: str
    context: Mapping[str, Any] | None = None
    model: str | None = None


@dataclass(frozen=True, slots=True)
class InferenceResult:
    """Contrat futur d'un résultat d'inférence."""

    text: str
    confidence: float = 0.0
    metadata: Mapping[str, Any] | None = None


class InferenceBackend(Protocol):
    """Interface minimale d'un backend d'inférence."""

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        """Exécute une inférence sans exposer le backend au Scheduler."""

        ...
