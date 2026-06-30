from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from contracts.context import InferenceContext, freeze_mapping

JsonPayload = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class E5RuntimeBridgePolicy:
    """Politique explicite du pont entre artefacts E5 et InferenceContext."""

    component_name: str = "e5_local_context"
    priority: int = 20
    include_prompt_text: bool = True
    include_context_text: bool = False

    def __post_init__(self) -> None:
        if not self.component_name.strip():
            raise ValueError("component_name must not be empty")


@dataclass(frozen=True, slots=True)
class E5RuntimeArtifactBundle:
    """Artefacts Phase 4 déjà chargés, sans IO et sans dépendance au CLI."""

    report: JsonPayload
    context: JsonPayload
    consumed_context: JsonPayload
    prompt: JsonPayload

    def __post_init__(self) -> None:
        _require_mapping(self.report, "report")
        _require_mapping(self.context, "context")
        _require_mapping(self.consumed_context, "consumed_context")
        _require_mapping(self.prompt, "prompt")


@dataclass(frozen=True, slots=True)
class E5RuntimeBridgeResult:
    """Résultat stable du pont local E5 -> InferenceContext."""

    component_name: str
    inference_context: InferenceContext

    def __post_init__(self) -> None:
        if not self.component_name.strip():
            raise ValueError("E5RuntimeBridgeResult.component_name must not be empty")

    def to_json_dict(self) -> dict[str, object]:
        """Projection JSON stable pour audit humain ou test."""
        return {
            "component_name": self.component_name,
            "features": _plain_mapping(self.inference_context.features),
            "priorities": dict(self.inference_context.priorities),
        }


class E5RuntimeBridge:
    """Pont pur entre artefacts E5 déterministes et contrat InferenceContext."""

    def __init__(self, policy: E5RuntimeBridgePolicy | None = None) -> None:
        self._policy = policy or E5RuntimeBridgePolicy()

    def build(self, artifacts: E5RuntimeArtifactBundle) -> E5RuntimeBridgeResult:
        """Construit un InferenceContext sans lire de fichier et sans appeler de backend."""
        feature = _build_feature_payload(artifacts, self._policy)
        context = InferenceContext(
            features=freeze_mapping({self._policy.component_name: feature}),
            priorities=freeze_mapping({self._policy.component_name: self._policy.priority}),
        )
        return E5RuntimeBridgeResult(
            component_name=self._policy.component_name,
            inference_context=context,
        )


def build_e5_runtime_inference_context(
    artifacts: E5RuntimeArtifactBundle,
    policy: E5RuntimeBridgePolicy | None = None,
) -> InferenceContext:
    """Fonction courte pour obtenir directement le contexte d'inférence local."""
    return E5RuntimeBridge(policy).build(artifacts).inference_context


def _build_feature_payload(
    artifacts: E5RuntimeArtifactBundle,
    policy: E5RuntimeBridgePolicy,
) -> dict[str, object]:
    report = artifacts.report
    context = artifacts.context
    consumed = artifacts.consumed_context
    prompt = artifacts.prompt

    prompt_text = _text(prompt, "prompt_text")
    context_text = _text(consumed, "context_text")
    selected_item_count = _integer(consumed, "selected_item_count", default=0)

    feature: dict[str, object] = {
        "schema": "missipy.e5.runtime_bridge.v1",
        "component": policy.component_name,
        "status": "ready" if selected_item_count > 0 else "empty",
        "query": _first_text(report, context, consumed, prompt, key="query"),
        "prefixed_query": _first_text(report, context, consumed, prompt, key="prefixed_query"),
        "index": _first_text(report, context, key="index"),
        "model": _first_text(report, context, key="model"),
        "backend": _first_text(report, context, key="backend"),
        "tokenizer": _first_text(report, context, key="tokenizer"),
        "dimension": _first_integer(report, context, key="dimension"),
        "hit_count": _integer(report, "hit_count", default=_sequence_count(report, "hits")),
        "context_item_count": _integer(context, "item_count", default=_sequence_count(context, "items")),
        "available_item_count": _integer(consumed, "available_item_count", default=0),
        "selected_item_count": selected_item_count,
        "skipped_item_count": _integer(consumed, "skipped_item_count", default=0),
        "max_context_chars": _integer(consumed, "max_chars", default=0),
        "used_context_chars": _integer(consumed, "used_chars", default=len(context_text)),
        "prompt_chars": len(prompt_text),
        "artifacts": {
            "report": True,
            "context": True,
            "consumed_context": True,
            "prompt": True,
        },
    }

    if policy.include_prompt_text:
        feature["prompt_text"] = prompt_text
    if policy.include_context_text:
        feature["context_text"] = context_text

    return feature


def _require_mapping(value: object, field_name: str) -> None:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")


def _text(payload: JsonPayload, key: str) -> str:
    value = payload.get(key)
    if isinstance(value, str):
        return value
    return ""


def _first_text(*payloads: JsonPayload, key: str) -> str:
    for payload in payloads:
        value = _text(payload, key)
        if value:
            return value
    return ""


def _integer(payload: JsonPayload, key: str, *, default: int) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default


def _first_integer(*payloads: JsonPayload, key: str) -> int:
    for payload in payloads:
        value = _integer(payload, key, default=0)
        if value > 0:
            return value
    return 0


def _sequence_count(payload: JsonPayload, key: str) -> int:
    value = payload.get(key)
    if isinstance(value, (tuple, list)):
        return len(value)
    return 0


def _plain_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, Mapping):
            result[key] = _plain_mapping(item)
        else:
            result[key] = item
    return result
