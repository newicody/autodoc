from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from contracts.context import InferenceContext, freeze_mapping

from .e5_local_context_runtime import (
    E5LocalContextRuntimePolicy,
    E5LocalContextRuntimeResult,
    build_e5_local_context_from_artifact_dir,
)


@dataclass(frozen=True, slots=True)
class E5ContextAttachmentPolicy:
    """Politique explicite d'attachement du contexte E5 local à un InferenceContext."""

    replace_existing: bool = True
    require_ready: bool = False
    minimum_priority: int | None = None

    def __post_init__(self) -> None:
        if self.minimum_priority is not None and self.minimum_priority < 0:
            raise ValueError("minimum_priority must not be negative")


@dataclass(frozen=True, slots=True)
class E5ContextAttachmentResult:
    """Résultat stable d'une fusion InferenceContext + runtime E5 local."""

    inference_context: InferenceContext
    component_names: tuple[str, ...]
    replaced_components: tuple[str, ...]
    ready: bool

    def __post_init__(self) -> None:
        if not self.component_names:
            raise ValueError("E5ContextAttachmentResult.component_names must not be empty")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": "missipy.e5.context_attachment.v1",
            "component_names": list(self.component_names),
            "replaced_components": list(self.replaced_components),
            "ready": self.ready,
            "features": _plain_mapping(self.inference_context.features),
            "priorities": dict(self.inference_context.priorities),
        }


class E5ContextAttachment:
    """Attache explicitement un résultat E5 local à un InferenceContext existant."""

    def __init__(self, policy: E5ContextAttachmentPolicy | None = None) -> None:
        self._policy = policy or E5ContextAttachmentPolicy()

    def attach(
        self,
        base_context: InferenceContext,
        runtime_result: E5LocalContextRuntimeResult,
    ) -> E5ContextAttachmentResult:
        runtime_context = runtime_result.inference_context
        component_names = tuple(str(name) for name in runtime_context.features.keys())
        if not component_names:
            raise ValueError("runtime_result must contain at least one feature")
        if self._policy.require_ready and not runtime_result.is_ready:
            raise ValueError("e5_local_context status must be ready")

        base_features = dict(base_context.features)
        base_priorities = dict(base_context.priorities)
        runtime_features = dict(runtime_context.features)
        runtime_priorities = dict(runtime_context.priorities)

        conflicts = tuple(name for name in component_names if name in base_features)
        if conflicts and not self._policy.replace_existing:
            joined = ", ".join(conflicts)
            raise ValueError(f"context already contains E5 component: {joined}")

        merged_features: dict[str, Any] = dict(base_features)
        merged_priorities: dict[str, int] = dict(base_priorities)

        for name, feature in runtime_features.items():
            merged_features[str(name)] = feature
        for name, priority in runtime_priorities.items():
            merged_priorities[str(name)] = _effective_priority(priority, self._policy)

        merged_context = InferenceContext(
            features=freeze_mapping(merged_features),
            priorities=freeze_mapping(merged_priorities),
        )
        return E5ContextAttachmentResult(
            inference_context=merged_context,
            component_names=component_names,
            replaced_components=conflicts,
            ready=runtime_result.is_ready,
        )


def attach_e5_runtime_context(
    base_context: InferenceContext,
    runtime_result: E5LocalContextRuntimeResult,
    policy: E5ContextAttachmentPolicy | None = None,
) -> E5ContextAttachmentResult:
    """Raccourci pur : InferenceContext existant + résultat E5 local -> contexte fusionné."""
    return E5ContextAttachment(policy).attach(base_context, runtime_result)


def attach_e5_artifact_dir_to_context(
    base_context: InferenceContext,
    artifact_dir: str | Path,
    *,
    runtime_policy: E5LocalContextRuntimePolicy | None = None,
    attachment_policy: E5ContextAttachmentPolicy | None = None,
) -> E5ContextAttachmentResult:
    """Raccourci contrôlé : artifact-dir Phase 4 -> runtime 5.4 -> attachement explicite."""
    runtime_result = build_e5_local_context_from_artifact_dir(artifact_dir, runtime_policy)
    return attach_e5_runtime_context(base_context, runtime_result, attachment_policy)


def _effective_priority(priority: object, policy: E5ContextAttachmentPolicy) -> int:
    value = priority if isinstance(priority, int) and not isinstance(priority, bool) else 0
    if policy.minimum_priority is not None and value < policy.minimum_priority:
        return policy.minimum_priority
    return value


def _plain_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, Mapping):
            result[key] = _plain_mapping(item)
        else:
            result[key] = item
    return result
