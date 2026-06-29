from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


def freeze_mapping(data: Mapping[str, Any]) -> Mapping[str, Any]:
    """Gèle récursivement un mapping pour produire un snapshot non mutable."""

    frozen: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, Mapping):
            frozen[key] = freeze_mapping(value)
        else:
            frozen[key] = value
    return MappingProxyType(frozen)


@dataclass(frozen=True, slots=True)
class GlobalContextSnapshot:
    """Image immuable de l'état de tous les composants à un instant T."""

    timestamp: float
    components: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class InferenceContext:
    """Version transformée pour les décideurs et backends d'inférence."""

    features: Mapping[str, Any]
    priorities: Mapping[str, int] = field(default_factory=lambda: MappingProxyType({}))
