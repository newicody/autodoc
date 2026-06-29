from __future__ import annotations

import pytest

from inference.model_profile import (
    OpenVINOModelProfile,
    OpenVINOModelProfileRegistry,
    SUPPORTED_OPENVINO_TASKS,
)


def test_openvino_model_profile_builds_backend_config() -> None:
    profile = OpenVINOModelProfile(
        name="openvino.embedding.bge-m3",
        model_path="/models/bge-m3/openvino_model.xml",
        task="embedding",
        device="GPU",
        input_names=("input_ids", "attention_mask"),
        output_names=("embeddings",),
        metadata={"dimension": 1024},
    )

    config = profile.to_backend_config()

    assert config.backend_name == "openvino.embedding.bge-m3"
    assert config.model_path == "/models/bge-m3/openvino_model.xml"
    assert config.device == "GPU"
    assert config.metadata["task"] == "embedding"
    assert config.metadata["profile_backend"] == "openvino"
    assert config.metadata["input_names"] == ("input_ids", "attention_mask")
    assert config.metadata["output_names"] == ("embeddings",)
    assert config.metadata["dimension"] == 1024


def test_openvino_model_profile_rejects_unknown_task() -> None:
    with pytest.raises(ValueError, match="Unsupported OpenVINO task"):
        OpenVINOModelProfile(
            name="bad",
            model_path="/models/bad.xml",
            task="classification",
        )


def test_openvino_model_profile_freezes_metadata_copy() -> None:
    source = {"dimension": 1024}
    profile = OpenVINOModelProfile(
        name="openvino.embedding",
        model_path="/models/embedding.xml",
        task="embedding",
        metadata=source,
    )

    source["dimension"] = 768

    assert profile.metadata["dimension"] == 1024
    with pytest.raises(TypeError):
        profile.metadata["dimension"] = 1  # type: ignore[index]


def test_openvino_model_profile_registry_selects_explicit_profile() -> None:
    embedding = OpenVINOModelProfile(
        name="openvino.embedding",
        model_path="/models/embedding.xml",
        task="embedding",
    )
    generation = OpenVINOModelProfile(
        name="openvino.generation",
        model_path="/models/generation.xml",
        task="generation",
    )
    registry = OpenVINOModelProfileRegistry()

    registry.register(generation)
    registry.register(embedding)

    assert registry.profile_names() == ("openvino.embedding", "openvino.generation")
    assert registry.tasks() == ("embedding", "generation")
    assert registry.select("openvino.embedding") is embedding
    assert registry.by_task("embedding") == (embedding,)

    snapshot = registry.snapshot()
    assert snapshot.profile_names == ("openvino.embedding", "openvino.generation")
    assert snapshot.metadata["count"] == 2


def test_openvino_model_profile_registry_rejects_duplicate_profile() -> None:
    profile = OpenVINOModelProfile(
        name="openvino.raw",
        model_path="/models/raw.xml",
        task="raw",
    )
    registry = OpenVINOModelProfileRegistry()
    registry.register(profile)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(profile)


def test_openvino_model_profile_registry_has_no_implicit_fallback() -> None:
    registry = OpenVINOModelProfileRegistry()

    with pytest.raises(LookupError, match="Available profiles: none"):
        registry.select("openvino.embedding")


def test_supported_openvino_tasks_are_intentional_minimal_profiles() -> None:
    assert SUPPORTED_OPENVINO_TASKS == frozenset({"embedding", "generation", "raw"})
