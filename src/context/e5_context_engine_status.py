from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from contracts.context import InferenceContext


@dataclass(frozen=True, slots=True)
class E5ContextEngineStatusPolicy:
    """Politique de projection d'état E5 depuis ContextEngine.

    Cette projection est passive : elle ne lit aucun fichier, ne déclenche aucun
    intake, ne lance aucun Scheduler et ne modifie pas le contexte.
    """

    component_name: str = "e5_local_context"

    def __post_init__(self) -> None:
        if not self.component_name.strip():
            raise ValueError("component_name must not be empty")


@dataclass(frozen=True, slots=True)
class E5ContextEngineStatus:
    """Projection stable et sérialisable de l'état E5 visible depuis ContextEngine."""

    component_name: str
    feature_count: int
    priority_count: int
    attached: bool
    ready: bool
    priority: int | None = None
    query: str | None = None
    selected_item_count: int | None = None
    used_context_chars: int | None = None
    prompt_chars: int | None = None
    snapshot_available: bool = False
    snapshot_component_count: int | None = None

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "schema": "missipy.e5.context_engine_status.v1",
            "component_name": self.component_name,
            "feature_count": self.feature_count,
            "priority_count": self.priority_count,
            "attached": self.attached,
            "ready": self.ready,
            "priority": self.priority,
            "query": self.query,
            "selected_item_count": self.selected_item_count,
            "used_context_chars": self.used_context_chars,
            "prompt_chars": self.prompt_chars,
            "snapshot_available": self.snapshot_available,
            "snapshot_component_count": self.snapshot_component_count,
        }

    def to_text(self) -> str:
        lines = [
            "schema: missipy.e5.context_engine_status.v1",
            f"component: {self.component_name}",
            f"attached: {str(self.attached).lower()}",
            f"ready: {str(self.ready).lower()}",
            f"feature_count: {self.feature_count}",
            f"priority_count: {self.priority_count}",
        ]
        if self.priority is not None:
            lines.append(f"priority: {self.priority}")
        if self.query is not None:
            lines.append(f"query: {self.query}")
        if self.selected_item_count is not None:
            lines.append(f"selected_item_count: {self.selected_item_count}")
        if self.used_context_chars is not None:
            lines.append(f"used_context_chars: {self.used_context_chars}")
        if self.prompt_chars is not None:
            lines.append(f"prompt_chars: {self.prompt_chars}")
        lines.append(f"snapshot_available: {str(self.snapshot_available).lower()}")
        if self.snapshot_component_count is not None:
            lines.append(f"snapshot_component_count: {self.snapshot_component_count}")
        return "\n".join(lines)


def inspect_e5_context_engine(
    engine: object,
    policy: E5ContextEngineStatusPolicy | None = None,
) -> E5ContextEngineStatus:
    """Inspecte passivement un ContextEngine ou un objet compatible."""
    inference_context = getattr(engine, "current_inference_context", None)
    if inference_context is None:
        inference_context = getattr(engine, "last_inference_context", None)
    if not isinstance(inference_context, InferenceContext):
        raise ValueError("engine must expose an InferenceContext")
    snapshot = getattr(engine, "last_snapshot", None)
    return inspect_e5_inference_context(inference_context, policy, snapshot=snapshot)


def inspect_e5_inference_context(
    inference_context: InferenceContext,
    policy: E5ContextEngineStatusPolicy | None = None,
    *,
    snapshot: object | None = None,
) -> E5ContextEngineStatus:
    """Inspecte passivement un InferenceContext sans modifier ses mappings."""
    effective = policy or E5ContextEngineStatusPolicy()
    feature = inference_context.features.get(effective.component_name)
    attached = isinstance(feature, Mapping)
    priority = _int_or_none(inference_context.priorities.get(effective.component_name))
    return E5ContextEngineStatus(
        component_name=effective.component_name,
        feature_count=len(inference_context.features),
        priority_count=len(inference_context.priorities),
        attached=attached,
        ready=_is_ready(feature),
        priority=priority,
        query=_str_or_none(_mapping_value(feature, "query")),
        selected_item_count=_int_or_none(_mapping_value(feature, "selected_item_count")),
        used_context_chars=_int_or_none(_mapping_value(feature, "used_context_chars")),
        prompt_chars=_int_or_none(_mapping_value(feature, "prompt_chars")),
        snapshot_available=snapshot is not None,
        snapshot_component_count=_snapshot_component_count(snapshot),
    )


def _is_ready(feature: object) -> bool:
    if not isinstance(feature, Mapping):
        return False
    return feature.get("status") == "ready"


def _mapping_value(feature: object, key: str) -> object | None:
    if not isinstance(feature, Mapping):
        return None
    return feature.get(key)


def _str_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _int_or_none(value: object | None) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    return None


def _snapshot_component_count(snapshot: object | None) -> int | None:
    if snapshot is None:
        return None
    components = getattr(snapshot, "components", None)
    if isinstance(components, Mapping):
        return len(components)
    if isinstance(snapshot, Mapping):
        return len(snapshot)
    return None
