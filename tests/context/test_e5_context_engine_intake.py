from __future__ import annotations

import json
from pathlib import Path

import pytest

from contracts.context import InferenceContext, freeze_mapping
from context.engine import ContextEngine, E5ContextEngineIntakePolicy
from context.e5_context_attachment import E5ContextAttachmentPolicy
from context.e5_local_context_runtime import E5LocalContextRuntimePolicy, build_e5_local_context_from_artifact_dir


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


def test_context_engine_starts_with_empty_inference_context() -> None:
    engine = ContextEngine()

    assert engine.current_inference_context.features == {}
    assert engine.current_inference_context.priorities == {}


def test_context_engine_attaches_e5_artifact_dir_and_updates_current_context(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    engine = ContextEngine(_base_context())

    result = engine.attach_e5_artifact_dir(tmp_path)

    assert result.ready is True
    assert result.previous_feature_count == 1
    assert result.feature_count == 2
    assert result.changed is True
    assert engine.current_inference_context is result.inference_context
    assert engine.current_inference_context.features["manual_note"]["status"] == "kept"
    assert engine.current_inference_context.features["e5_local_context"]["query"] == "OpenVINO local"


def test_context_engine_intake_json_projection_is_stable(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)

    payload = ContextEngine().attach_e5_artifact_dir(tmp_path).to_json_dict()

    assert payload["schema"] == "missipy.e5.context_engine_intake.v1"
    assert payload["ready"] is True
    assert payload["changed"] is True
    assert payload["previous_feature_count"] == 0
    assert payload["feature_count"] == 1
    assert payload["attachment"]["schema"] == "missipy.e5.context_attachment.v1"


def test_context_engine_can_attach_runtime_result_directly(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    runtime_result = build_e5_local_context_from_artifact_dir(tmp_path)
    engine = ContextEngine()

    result = engine.attach_e5_runtime_context(runtime_result)

    assert result.ready is True
    assert engine.current_inference_context.features["e5_local_context"]["status"] == "ready"


def test_context_engine_respects_intake_policy(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    engine = ContextEngine()
    policy = E5ContextEngineIntakePolicy(
        runtime_policy=E5LocalContextRuntimePolicy(require_ready=True),
        attachment_policy=E5ContextAttachmentPolicy(minimum_priority=50),
    )

    result = engine.attach_e5_artifact_dir(tmp_path, policy)

    assert result.inference_context.priorities["e5_local_context"] == 50


def test_context_engine_can_reject_non_ready_context_when_policy_requires_ready(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, selected=0)
    engine = ContextEngine()
    policy = E5ContextEngineIntakePolicy(
        runtime_policy=E5LocalContextRuntimePolicy(require_ready=True),
    )

    with pytest.raises(ValueError, match="status must be ready"):
        engine.attach_e5_artifact_dir(tmp_path, policy)
