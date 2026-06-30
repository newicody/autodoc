from __future__ import annotations

import json
from pathlib import Path

from context.e5_artifact_loader import (
    E5RuntimeArtifactDirectoryLoader,
    E5RuntimeArtifactDirectoryPolicy,
    build_e5_runtime_bridge_from_directory,
    load_e5_runtime_artifacts_from_directory,
)
from context.e5_runtime_bridge import E5RuntimeBridgePolicy


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _artifact_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "artifacts"
    directory.mkdir()
    _write_json(
        directory / "report.json",
        {
            "query": "je me suis fait baiser",
            "prefixed_query": "query: je me suis fait baiser",
            "index": "/tmp/corpus.json",
            "model": "fake-e5",
            "backend": "fake-backend",
            "tokenizer": "fake-tokenizer",
            "dimension": 384,
            "hit_count": 1,
            "hits": [{"id": "chunk-1"}],
        },
    )
    _write_json(
        directory / "context.json",
        {
            "query": "je me suis fait baiser",
            "prefixed_query": "query: je me suis fait baiser",
            "index": "/tmp/corpus.json",
            "item_count": 1,
            "items": [{"id": "chunk-1", "excerpt": "arnaque vendeur"}],
        },
    )
    _write_json(
        directory / "consumed_context.json",
        {
            "query": "je me suis fait baiser",
            "prefixed_query": "query: je me suis fait baiser",
            "max_chars": 500,
            "used_chars": 42,
            "available_item_count": 1,
            "selected_item_count": 1,
            "skipped_item_count": 0,
            "context_text": "[1] notes.md\narnaque vendeur",
            "items": [{"id": "chunk-1", "text": "[1] notes.md\narnaque vendeur"}],
        },
    )
    _write_json(
        directory / "prompt.json",
        {
            "query": "je me suis fait baiser",
            "prefixed_query": "query: je me suis fait baiser",
            "selected_item_count": 1,
            "prompt_text": "[QUESTION]\nje me suis fait baiser\n\n[CONTEXT]\narnaque vendeur",
        },
    )
    return directory


def test_loader_reads_phase4_artifact_directory(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path)

    result = E5RuntimeArtifactDirectoryLoader().load(directory)

    assert result.artifact_dir == directory
    assert result.report_path == directory / "report.json"
    assert result.context_path == directory / "context.json"
    assert result.consumed_context_path == directory / "consumed_context.json"
    assert result.prompt_path == directory / "prompt.json"
    assert result.artifacts.report["query"] == "je me suis fait baiser"
    assert result.artifacts.context["item_count"] == 1
    assert result.to_json_dict()["loaded"] == {
        "report": True,
        "context": True,
        "consumed_context": True,
        "prompt": True,
    }


def test_load_shortcut_returns_artifact_bundle(tmp_path: Path) -> None:
    artifacts = load_e5_runtime_artifacts_from_directory(_artifact_dir(tmp_path))

    assert artifacts.report["dimension"] == 384
    assert artifacts.prompt["selected_item_count"] == 1


def test_directory_bridge_builds_inference_context(tmp_path: Path) -> None:
    result = build_e5_runtime_bridge_from_directory(
        _artifact_dir(tmp_path),
        bridge_policy=E5RuntimeBridgePolicy(component_name="artifact_context", priority=9),
    )

    assert result.component_name == "artifact_context"
    assert result.inference_context.priorities["artifact_context"] == 9
    feature = result.inference_context.features["artifact_context"]
    assert feature["schema"] == "missipy.e5.runtime_bridge.v1"
    assert feature["status"] == "ready"
    assert feature["query"] == "je me suis fait baiser"


def test_loader_accepts_custom_filenames(tmp_path: Path) -> None:
    directory = tmp_path / "custom"
    directory.mkdir()
    _write_json(directory / "a.json", {"query": "q", "hits": []})
    _write_json(directory / "b.json", {"items": []})
    _write_json(directory / "c.json", {"selected_item_count": 0, "context_text": ""})
    _write_json(directory / "d.json", {"prompt_text": "[CONTEXT]"})

    policy = E5RuntimeArtifactDirectoryPolicy(
        report_filename="a.json",
        context_filename="b.json",
        consumed_context_filename="c.json",
        prompt_filename="d.json",
    )

    result = E5RuntimeArtifactDirectoryLoader(policy).load(directory)

    assert result.report_path.name == "a.json"
    assert result.artifacts.prompt["prompt_text"] == "[CONTEXT]"


def test_loader_rejects_non_directory(tmp_path: Path) -> None:
    try:
        E5RuntimeArtifactDirectoryLoader().load(tmp_path / "missing")
    except NotADirectoryError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected NotADirectoryError")


def test_loader_rejects_non_object_json(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path)
    _write_json(directory / "report.json", [])

    try:
        E5RuntimeArtifactDirectoryLoader().load(directory)
    except TypeError as exc:
        assert "report artifact must be a JSON object" in str(exc)
    else:
        raise AssertionError("expected TypeError")


def test_loader_policy_rejects_nested_filenames() -> None:
    try:
        E5RuntimeArtifactDirectoryPolicy(report_filename="nested/report.json")
    except ValueError as exc:
        assert "report_filename" in str(exc)
    else:
        raise AssertionError("expected ValueError")
