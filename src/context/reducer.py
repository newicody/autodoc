from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping

from contracts.context import GlobalContextSnapshot, freeze_mapping


@dataclass(slots=True)
class ContextReducer:
    """Réduit les réponses de contexte en snapshot immuable."""

    def reduce(self, contexts: Mapping[str, Mapping[str, Any]]) -> GlobalContextSnapshot:
        frozen_components = {
            name: freeze_mapping(context)
            for name, context in contexts.items()
        }
        return GlobalContextSnapshot(
            timestamp=time.time(),
            components=freeze_mapping(frozen_components),
        )
