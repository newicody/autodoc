from __future__ import annotations

from types import MappingProxyType

import pytest

from contracts.inference import InferenceRequest, InferenceResult
from inference.adapter import InferenceAdapter
from inference.model_profile import OpenVINOModelProfile, OpenVINOModelProfileRegistry
from inference.openvino_backend import OpenVINOBackendConfig
from inference.openvino_factory import (
    OpenVINOBackendBuildResult,
    OpenVINOBackendFactory,
)
from inference.registry import BackendRegistry


class RecordingRuntime:
    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.calls: list[tuple[str, str, str]] = []

    async def infer(
        self,
        request: InferenceRequest,
        *,
        config: OpenVINOBackendConfig,
    ) -> InferenceResult:
        self.calls.append((request.prompt, config.backend_name, config.device))
        return InferenceResult(
            text=f"{self.tag}:{config.backend_name}:{request.prompt}",
            confidence=0.9,
            backend=config.backend_name,
            metadata=MappingProxyType({"device": config.device}),
        )


def runtime_factory(
    profile: OpenVINOModelProfile,
    config: OpenVINOBackendConfig,
) -> RecordingRuntime:
    return RecordingRuntime(f"runtime-for-{profile.task}-{config.device}")


@pytest.mark.asyncio
async def test_openvino_backend_factory_builds_backend_from_profile() -> None:
    profile = OpenVINOModelProfile(
        name="openvino.embedding.bge-m3",
        model_path="/models/bge-m3/openvino_model.xml",
        task="embedding",
        device="GPU",
        input_names=("input_ids", "attention_mask"),
        output_names=("embeddings",),
    )
    factory = OpenVINOBackendFactory(runtime_factory)

    backend = factory.build(profile)
    result = await backend.infer(
        InferenceRequest(prompt="ping", model="openvino.embedding.bge-m3")
    )

    assert backend.name == "openvino.embedding.bge-m3"
    assert backend.config.model_path == "/models/bge-m3/openvino_model.xml"
    assert backend.config.metadata["task"] == "embedding"
    assert result.backend == "openvino.embedding.bge-m3"
    assert result.text == "runtime-for-embedding-GPU:openvino.embedding.bge-m3:ping"


@pytest.mark.asyncio
async def test_openvino_backend_factory_registers_backend_for_adapter_selection() -> None:
    profile = OpenVINOModelProfile(
        name="openvino.raw.debug",
        model_path="/models/debug.xml",
        task="raw",
    )
    backend_registry = BackendRegistry()
    factory = OpenVINOBackendFactory(runtime_factory)

    build = factory.build_and_register(profile, backend_registry, make_default=True)
    adapter = InferenceAdapter(backend_registry)
    result = await adapter.infer(InferenceRequest(prompt="x", model="openvino.raw.debug"))

    assert build.profile_name == "openvino.raw.debug"
    assert build.backend_name == "openvino.raw.debug"
    assert build.registered is True
    assert build.metadata["task"] == "raw"
    assert backend_registry.snapshot().backend_names == ("openvino.raw.debug",)
    assert backend_registry.default_backend_name == "openvino.raw.debug"
    assert result.text == "runtime-for-raw-CPU:openvino.raw.debug:x"


@pytest.mark.asyncio
async def test_openvino_backend_factory_selects_profile_explicitly() -> None:
    profiles = OpenVINOModelProfileRegistry()
    profiles.register(
        OpenVINOModelProfile(
            name="openvino.generation.qwen",
            model_path="/models/qwen/openvino_model.xml",
            task="generation",
        )
    )
    backend_registry = BackendRegistry()
    factory = OpenVINOBackendFactory(runtime_factory)

    build = factory.build_selected_and_register(
        profiles,
        "openvino.generation.qwen",
        backend_registry,
    )
    result = await InferenceAdapter(backend_registry).infer(
        InferenceRequest(prompt="bonjour", model="openvino.generation.qwen")
    )

    assert build.profile_name == "openvino.generation.qwen"
    assert result.backend == "openvino.generation.qwen"


def test_openvino_backend_factory_refuses_missing_selected_profile() -> None:
    factory = OpenVINOBackendFactory(runtime_factory)

    with pytest.raises(LookupError, match="Available profiles: none"):
        factory.build_selected_and_register(
            OpenVINOModelProfileRegistry(),
            "openvino.embedding",
            BackendRegistry(),
        )


def test_openvino_backend_factory_builds_all_profiles_for_task_in_stable_order() -> None:
    profiles = OpenVINOModelProfileRegistry()
    profiles.register(
        OpenVINOModelProfile(
            name="openvino.embedding.z-last",
            model_path="/models/z.xml",
            task="embedding",
        )
    )
    profiles.register(
        OpenVINOModelProfile(
            name="openvino.embedding.a-first",
            model_path="/models/a.xml",
            task="embedding",
            device="GPU",
        )
    )
    profiles.register(
        OpenVINOModelProfile(
            name="openvino.raw.debug",
            model_path="/models/raw.xml",
            task="raw",
        )
    )
    backend_registry = BackendRegistry()
    factory = OpenVINOBackendFactory(runtime_factory)

    builds = factory.build_all_for_task(profiles, "embedding", backend_registry)

    assert tuple(build.profile_name for build in builds) == (
        "openvino.embedding.a-first",
        "openvino.embedding.z-last",
    )
    assert backend_registry.snapshot().backend_names == (
        "openvino.embedding.a-first",
        "openvino.embedding.z-last",
    )


def test_openvino_backend_build_result_is_immutable_and_validated() -> None:
    result = OpenVINOBackendBuildResult(
        profile_name="p",
        backend_name="b",
        model_path="m.xml",
        device="CPU",
        registered=True,
        metadata={"task": "raw"},
    )

    assert result.metadata["task"] == "raw"
    with pytest.raises(TypeError):
        result.metadata["task"] = "embedding"  # type: ignore[index]

    with pytest.raises(ValueError):
        OpenVINOBackendBuildResult(
            profile_name="",
            backend_name="b",
            model_path="m.xml",
            device="CPU",
            registered=True,
        )
