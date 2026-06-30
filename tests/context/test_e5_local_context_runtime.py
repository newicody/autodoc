from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.e5_local_context_runtime import (
    E5LocalContextRuntime,
    E5LocalContextRuntimePolicy,
    build_e5_local_context_from_artifact_dir,
    build_e5_local_inference_context_from_artifact_dir,
)
from context.e5_runtime_bridge import E5RuntimeBridgePolicy


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


def test_local_context_runtime_builds_ready_result(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)

    result = build_e5_local_context_from_artifact_dir(tmp_path)

    assert result.status == "ready"
    assert result.is_ready is True
    assert result.component_name == "e5_local_context"
    assert result.feature["query"] == "OpenVINO local"
    assert result.feature["selected_item_count"] == 1
    assert result.inference_context.priorities["e5_local_context"] == 20


def test_local_context_runtime_json_projection_is_stable(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)

    payload = build_e5_local_context_from_artifact_dir(tmp_path).to_json_dict()

    assert payload["schema"] == "missipy.e5.local_context_runtime.v1"
    assert payload["artifact_dir"] == str(tmp_path)
    assert payload["status"] == "ready"
    assert payload["ready"] is True
    assert payload["read"]
    assert payload["bridge"]


def test_local_context_runtime_can_return_inference_context_directly(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)

    inference_context = build_e5_local_inference_context_from_artifact_dir(tmp_path)

    assert "e5_local_context" in inference_context.features
    assert inference_context.features["e5_local_context"]["status"] == "ready"


def test_local_context_runtime_respects_bridge_policy(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    policy = E5LocalContextRuntimePolicy(
        bridge_policy=E5RuntimeBridgePolicy(
            component_name="local_e5_probe",
            priority=7,
            include_prompt_text=False,
        )
    )

    result = E5LocalContextRuntime(policy).build_from_directory(tmp_path)

    assert result.component_name == "local_e5_probe"
    assert result.inference_context.priorities["local_e5_probe"] == 7
    assert "prompt_text" not in result.feature


def test_local_context_runtime_can_require_ready_context(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, selected=0)
    policy = E5LocalContextRuntimePolicy(require_ready=True)

    with pytest.raises(ValueError, match="status must be ready"):
        E5LocalContextRuntime(policy).build_from_directory(tmp_path)
