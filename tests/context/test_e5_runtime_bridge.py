from __future__ import annotations

from context.e5_runtime_bridge import (
    E5RuntimeArtifactBundle,
    E5RuntimeBridge,
    E5RuntimeBridgePolicy,
    build_e5_runtime_inference_context,
)


def _artifacts() -> E5RuntimeArtifactBundle:
    return E5RuntimeArtifactBundle(
        report={
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
        context={
            "query": "je me suis fait baiser",
            "prefixed_query": "query: je me suis fait baiser",
            "index": "/tmp/corpus.json",
            "item_count": 1,
            "items": [{"id": "chunk-1", "excerpt": "arnaque vendeur"}],
        },
        consumed_context={
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
        prompt={
            "query": "je me suis fait baiser",
            "prefixed_query": "query: je me suis fait baiser",
            "selected_item_count": 1,
            "prompt_text": "[QUESTION]\nje me suis fait baiser\n\n[CONTEXT]\narnaque vendeur",
        },
    )


def test_bridge_builds_inference_context_from_phase4_artifacts() -> None:
    result = E5RuntimeBridge().build(_artifacts())

    assert result.component_name == "e5_local_context"
    assert result.inference_context.priorities["e5_local_context"] == 20

    feature = result.inference_context.features["e5_local_context"]
    assert feature["schema"] == "missipy.e5.runtime_bridge.v1"
    assert feature["status"] == "ready"
    assert feature["query"] == "je me suis fait baiser"
    assert feature["prefixed_query"] == "query: je me suis fait baiser"
    assert feature["index"] == "/tmp/corpus.json"
    assert feature["dimension"] == 384
    assert feature["hit_count"] == 1
    assert feature["context_item_count"] == 1
    assert feature["selected_item_count"] == 1
    assert feature["prompt_chars"] > 0
    assert "prompt_text" in feature
    assert "context_text" not in feature


def test_bridge_policy_can_hide_prompt_and_rename_component() -> None:
    policy = E5RuntimeBridgePolicy(
        component_name="project_context",
        priority=7,
        include_prompt_text=False,
        include_context_text=True,
    )

    context = build_e5_runtime_inference_context(_artifacts(), policy)

    assert context.priorities["project_context"] == 7
    feature = context.features["project_context"]
    assert "prompt_text" not in feature
    assert feature["context_text"] == "[1] notes.md\narnaque vendeur"


def test_bridge_marks_empty_context_without_selected_items() -> None:
    artifacts = E5RuntimeArtifactBundle(
        report={"query": "OpenVINO", "hits": []},
        context={"items": []},
        consumed_context={"selected_item_count": 0, "context_text": ""},
        prompt={"prompt_text": "[CONTEXT]\nAucun contexte"},
    )

    context = build_e5_runtime_inference_context(artifacts)

    feature = context.features["e5_local_context"]
    assert feature["status"] == "empty"
    assert feature["hit_count"] == 0
    assert feature["context_item_count"] == 0


def test_bridge_rejects_empty_component_name() -> None:
    try:
        E5RuntimeBridgePolicy(component_name=" ")
    except ValueError as exc:
        assert "component_name" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_artifact_bundle_rejects_non_mapping_payload() -> None:
    try:
        E5RuntimeArtifactBundle(report=[], context={}, consumed_context={}, prompt={})  # type: ignore[arg-type]
    except TypeError as exc:
        assert "report must be a mapping" in str(exc)
    else:
        raise AssertionError("expected TypeError")
