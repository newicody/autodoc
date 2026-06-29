# contracts/context.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class GlobalContextSnapshot:
    """Image immuable de l’état de tous les composants à un instant T."""
    timestamp: float
    components: Dict[str, dict]  # nom -> état

@dataclass(frozen=True)
class InferenceContext:
    """Version transformée pour les décideurs (OpenVINO, MCTS, etc.)."""
    features: Dict[str, Any]
    priorities: Dict[str, int] = field(default_factory=dict)
