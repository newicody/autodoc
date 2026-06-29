from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class InferenceRequest:
    """Demande d'inférence indépendante de tout backend concret.

    Le Scheduler ne lit pas cette structure. Il la route uniquement via Event.
    Les backends comme DummyInferenceBackend ou OpenVINOBackend l'interprètent.
    """

    prompt: str
    context: Mapping[str, Any] = field(default_factory=_empty_mapping)
    model: str = "dummy"
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)


@dataclass(frozen=True, slots=True)
class InferenceResult:
    """Résultat d'inférence retourné via Request.reply et observé par EventBus."""

    text: str
    confidence: float = 0.0
    backend: str = "unknown"
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)


class InferenceBackend(Protocol):
    """Interface minimale d'un backend d'inférence."""

    name: str

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        """Exécute une inférence sans exposer le backend au Scheduler."""
        ...
