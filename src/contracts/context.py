from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


def freeze_mapping(data: Mapping[str, Any]) -> Mapping[str, Any]:
    """Gel léger pour éviter les mutations accidentelles du snapshot."""
    return MappingProxyType(dict(data))


@dataclass(frozen=True, slots=True)
class GlobalContextSnapshot:
    """Image immuable de l'état observable des composants."""

    timestamp: float
    components: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class InferenceContext:
    """Projection du contexte global vers les décideurs/backends."""

    features: Mapping[str, Any]
    priorities: Mapping[str, int] = field(default_factory=dict)
