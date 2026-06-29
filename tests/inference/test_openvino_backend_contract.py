from __future__ import annotations

from types import MappingProxyType

import pytest

from contracts.inference import InferenceRequest, InferenceResult
from inference.adapter import InferenceAdapter
from inference.openvino_backend import (
    OpenVINOBackend,
    OpenVINOBackendConfig,
    OpenVINOBackendError,
)
from inference.registry import BackendRegistry


class FakeOpenVINORuntime:
    """Runtime déterministe qui remplace openvino.runtime dans les tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    async def infer(
        self,
        request: InferenceRequest,
        *,
        config: OpenVINOBackendConfig,
    ) -> InferenceResult:
        self.calls.append((request.prompt, config.model_path, config.device))
        return InferenceResult(
            text=f"fake-openvino://{config.device}:{request.prompt.strip()}",
            confidence=0.75,
            backend=config.backend_name,
            metadata=MappingProxyType(
                {
                    "model_path": config.model_path,
                    "device": config.device,
                }
            ),
        )


class MismatchedBackendRuntime:
    async def infer(
        self,
        request: InferenceRequest,
        *,
        config: OpenVINOBackendConfig,
    ) -> InferenceResult:
        return InferenceResult(
            text=request.prompt,
            confidence=0.25,
            backend="external-runtime",
        )


@pytest.mark.asyncio
async def test_openvino_backend_contract_uses_injected_runtime() -> None:
    runtime = FakeOpenVINORuntime()
    backend = OpenVINOBackend(
        OpenVINOBackendConfig(
            model_path="models/qwen/openvino_model.xml",
            device="GPU",
        ),
        runtime,
    )

    result = await backend.infer(InferenceRequest(prompt=" hello ", model="openvino"))

    assert result.text == "fake-openvino://GPU:hello"
    assert result.backend == "openvino"
    assert result.metadata["model_path"] == "models/qwen/openvino_model.xml"
    assert runtime.calls == [(" hello ", "models/qwen/openvino_model.xml", "GPU")]

    state = backend.state()
    assert state.backend_name == "openvino"
    assert state.model_path == "models/qwen/openvino_model.xml"
    assert state.device == "GPU"
    assert state.ready is True
    assert state.request_count == 1
    assert state.metadata["has_real_openvino"] is False


@pytest.mark.asyncio
async def test_openvino_backend_can_be_selected_by_backend_registry() -> None:
    backend = OpenVINOBackend(
        OpenVINOBackendConfig(model_path="model.xml", device="CPU"),
        FakeOpenVINORuntime(),
    )
    registry = BackendRegistry()
    registry.register(backend, make_default=True)
    adapter = InferenceAdapter(registry)

    result = await adapter.infer(InferenceRequest(prompt="ping", model="openvino"))

    assert result.backend == "openvino"
    assert result.text == "fake-openvino://CPU:ping"
    assert registry.snapshot().backend_names == ("openvino",)


@pytest.mark.asyncio
async def test_openvino_backend_normalizes_runtime_backend_name() -> None:
    backend = OpenVINOBackend(
        OpenVINOBackendConfig(model_path="model.xml", device="CPU"),
        MismatchedBackendRuntime(),
    )

    result = await backend.infer(InferenceRequest(prompt="x", model="openvino"))

    assert result.backend == "openvino"
    assert result.metadata["wrapped_backend"] == "external-runtime"


@pytest.mark.asyncio
async def test_openvino_backend_refuses_after_close() -> None:
    backend = OpenVINOBackend(
        OpenVINOBackendConfig(model_path="model.xml", device="CPU"),
        FakeOpenVINORuntime(),
    )
    backend.close()

    with pytest.raises(OpenVINOBackendError):
        await backend.infer(InferenceRequest(prompt="x", model="openvino"))

    assert backend.state().ready is False


def test_openvino_backend_config_validation() -> None:
    runtime = FakeOpenVINORuntime()

    with pytest.raises(ValueError):
        OpenVINOBackend(OpenVINOBackendConfig(model_path=""), runtime)

    with pytest.raises(ValueError):
        OpenVINOBackend(OpenVINOBackendConfig(model_path="model.xml", device=""), runtime)

    with pytest.raises(ValueError):
        OpenVINOBackend(OpenVINOBackendConfig(model_path="model.xml", backend_name=""), runtime)
