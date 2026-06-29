from __future__ import annotations

from dataclasses import dataclass

from contracts.context import GlobalContextSnapshot, InferenceContext, freeze_mapping


@dataclass(slots=True)
class InferenceContextBuilder:
    """Construit la projection consommable par les futurs décideurs."""

    def build(self, snapshot: GlobalContextSnapshot) -> InferenceContext:
        priorities = {
            name: self._priority_for_context(context)
            for name, context in snapshot.components.items()
        }
        return InferenceContext(
            features=freeze_mapping({"component_count": len(snapshot.components)}),
            priorities=freeze_mapping(priorities),
        )

    @staticmethod
    def _priority_for_context(context: object) -> int:
        if isinstance(context, dict) and "error" in context:
            return -10
        return 0
