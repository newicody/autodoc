from __future__ import annotations

import json
from pathlib import Path

import pytest

from contracts.context import InferenceContext, freeze_mapping
from context.e5_context_attachment import (
    E5ContextAttachment,
    E5ContextAttachmentPolicy,
    attach_e5_artifact_dir_to_context,
    attach_e5_runtime_context,
)
from context.e5_local_context_runtime import build_e5_local_context_from_artifact_dir


def _empty_context() -> InferenceContext:
    return InferenceContext(features=freeze_mapping({}), priorities=freeze_mapping({}))


def _base_context() -> InferenceContext:
    return InferenceContext(
        features=freeze_mapping({"manual_note": {"status": "kept", "text": "stable"}}),
        priorities=freeze_mapping({"manual_note": 3}),
    )


def _write_artifacts(directory: Path, *, selected: int = 1) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    payloads = {
        "report.json": {
            "query": "OpenVINO local",
            "prefixed_query": "query: OpenVINO local",
            "index": "/tmp/autodoc_e5_corpus.json",
            "model": "openvino.embedding.e5-small",
            "backend": "openvino.embedding.e5-small",
            "tokenizer": "transformers.multilingual-e5-small",
            "dimension": 384,
            "hit_count": 1,
            "hits": [{"id": "a", "score": 0.9}],
        },
        "context.json": {
            "query": "OpenVINO local",
            "prefixed_query": "query: OpenVINO local",
            "index": "/tmp/autodoc_e5_corpus.json",
            "model": "openvino.embedding.e5-small",
            "backend": "openvino.embedding.e5-small",
            "tokenizer": "transformers.multilingual-e5-small",
            "dimension": 384,
            "item_count": 1,
            "items": [{"rank": 1, "excerpt": "OpenVINO E5 local"}],
        },
        "consumed_context.json": {
            "query": "OpenVINO local",
            "prefixed_query": "query: OpenVINO local",
            "max_chars": 4000,
            "used_chars": 18 if selected else 0,
            "available_item_count": 1,
            "selected_item_count": selected,
            "skipped_item_count": 0 if selected else 1,
            "context_text": "OpenVINO E5 local" if selected else "",
            "items": [{"rank": 1}] if selected else [],
        },
        "prompt.json": {
            "query": "OpenVINO local",
            "prefixed_query": "query: OpenVINO local",
            "prompt_text": "[QUESTION]\nOpenVINO local\n\n[CONTEXT]\nOpenVINO E5 local",
        },
    }
    for filename, payload in payloads.items():
        (directory / filename).write_text(json.dumps(payload), encoding="utf-8")


def test_attach_runtime_context_preserves_existing_features(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    runtime_result = build_e5_local_context_from_artifact_dir(tmp_path)

    result = attach_e5_runtime_context(_base_context(), runtime_result)

    assert result.ready is True
    assert result.component_names == ("e5_local_context",)
    assert result.replaced_components == ()
    assert result.inference_context.features["manual_note"]["status"] == "kept"
    assert result.inference_context.features["e5_local_context"]["status"] == "ready"
    assert result.inference_context.priorities["manual_note"] == 3
    assert result.inference_context.priorities["e5_local_context"] == 20


def test_attach_runtime_context_json_projection_is_stable(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    runtime_result = build_e5_local_context_from_artifact_dir(tmp_path)

    payload = attach_e5_runtime_context(_empty_context(), runtime_result).to_json_dict()

    assert payload["schema"] == "missipy.e5.context_attachment.v1"
    assert payload["component_names"] == ["e5_local_context"]
    assert payload["replaced_components"] == []
    assert payload["ready"] is True
    assert payload["features"]["e5_local_context"]["query"] == "OpenVINO local"
    assert payload["priorities"]["e5_local_context"] == 20


def test_attach_runtime_context_rejects_conflict_when_replace_is_disabled(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    runtime_result = build_e5_local_context_from_artifact_dir(tmp_path)
    existing = InferenceContext(
        features=freeze_mapping({"e5_local_context": {"status": "old"}}),
        priorities=freeze_mapping({"e5_local_context": 1}),
    )

    with pytest.raises(ValueError, match="already contains E5 component"):
        attach_e5_runtime_context(
            existing,
            runtime_result,
            E5ContextAttachmentPolicy(replace_existing=False),
        )


def test_attach_runtime_context_replaces_existing_component_by_default(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    runtime_result = build_e5_local_context_from_artifact_dir(tmp_path)
    existing = InferenceContext(
        features=freeze_mapping({"e5_local_context": {"status": "old"}}),
        priorities=freeze_mapping({"e5_local_context": 1}),
    )

    result = attach_e5_runtime_context(existing, runtime_result)

    assert result.replaced_components == ("e5_local_context",)
    assert result.inference_context.features["e5_local_context"]["status"] == "ready"
    assert result.inference_context.priorities["e5_local_context"] == 20


def test_attach_runtime_context_can_require_ready_context(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, selected=0)
    runtime_result = build_e5_local_context_from_artifact_dir(tmp_path)

    with pytest.raises(ValueError, match="status must be ready"):
        E5ContextAttachment(E5ContextAttachmentPolicy(require_ready=True)).attach(_empty_context(), runtime_result)


def test_attach_runtime_context_can_raise_priority_floor(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    runtime_result = build_e5_local_context_from_artifact_dir(tmp_path)

    result = attach_e5_runtime_context(
        _empty_context(),
        runtime_result,
        E5ContextAttachmentPolicy(minimum_priority=50),
    )

    assert result.inference_context.priorities["e5_local_context"] == 50


def test_attach_artifact_dir_shortcut_loads_runtime_then_attaches(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)

    result = attach_e5_artifact_dir_to_context(_base_context(), tmp_path)

    assert result.inference_context.features["manual_note"]["text"] == "stable"
    assert result.inference_context.features["e5_local_context"]["query"] == "OpenVINO local"
