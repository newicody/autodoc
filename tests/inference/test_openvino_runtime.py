from __future__ import annotations

import pytest

from contracts.inference import InferenceRequest
from inference.openvino_backend import OpenVINOBackend, OpenVINOBackendConfig
from inference.openvino_runtime import (
    RealOpenVINORuntime,
    RealOpenVINORuntimeError,
    RealOpenVINORuntimeUnavailable,
)


class FakeCompiledModel:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def __call__(self, inputs: object) -> dict[str, object]:
        self.calls.append(inputs)
        return {"embedding": [1.0, 2.0, 3.0]}


class FakeCore:
    def __init__(self) -> None:
        self.read_models: list[str] = []
        self.compile_calls: list[tuple[object, str]] = []
        self.compiled = FakeCompiledModel()

    def read_model(self, model_path: str) -> str:
        self.read_models.append(model_path)
        return f"read:{model_path}"

    def compile_model(self, model: object, device: str) -> FakeCompiledModel:
        self.compile_calls.append((model, device))
        return self.compiled


class FakeOpenVINOModule:
    def __init__(self) -> None:
        self.core = FakeCore()

    def Core(self) -> FakeCore:  # noqa: N802 - mirrors OpenVINO API.
        return self.core


@pytest.mark.asyncio
async def test_real_openvino_runtime_uses_injected_openvino_module() -> None:
    ov_module = FakeOpenVINOModule()
    runtime = RealOpenVINORuntime(ov_module)
    backend = OpenVINOBackend(
        OpenVINOBackendConfig(
            model_path="models/embed/openvino_model.xml",
            device="GPU",
        ),
        runtime,
    )

    request = InferenceRequest(
        prompt="ignored by raw runtime",
        model="openvino",
        context={"inputs": {"input_ids": [1, 2, 3]}},
    )

    result = await backend.infer(request)

    assert result.backend == "openvino"
    assert result.text == "openvino://GPU:openvino_model.xml"
    assert result.metadata["output_count"] == 1
    assert result.metadata["raw_outputs"] == {"embedding": [1.0, 2.0, 3.0]}
    assert result.metadata["input_kind"] == "dict"
    assert ov_module.core.read_models == ["models/embed/openvino_model.xml"]
    assert ov_module.core.compile_calls == [("read:models/embed/openvino_model.xml", "GPU")]
    assert ov_module.core.compiled.calls == [{"input_ids": [1, 2, 3]}]
    assert backend.state().metadata["has_real_openvino"] is True
    assert runtime.state().compiled_models == 1
    assert runtime.state().infer_count == 1


@pytest.mark.asyncio
async def test_real_openvino_runtime_reuses_compiled_model_cache() -> None:
    ov_module = FakeOpenVINOModule()
    runtime = RealOpenVINORuntime(ov_module)
    backend = OpenVINOBackend(
        OpenVINOBackendConfig(model_path="model.xml", device="CPU"),
        runtime,
    )

    request = InferenceRequest(prompt="x", model="openvino", context={"inputs": [1]})

    await backend.infer(request)
    await backend.infer(request)

    assert ov_module.core.read_models == ["model.xml"]
    assert len(ov_module.core.compile_calls) == 1
    assert runtime.state().compiled_models == 1
    assert runtime.state().infer_count == 2


def test_real_openvino_runtime_requires_raw_inputs() -> None:
    runtime = RealOpenVINORuntime(FakeOpenVINOModule())

    try:
        runtime._infer_sync(
            InferenceRequest(prompt="text only", model="openvino"),
            OpenVINOBackendConfig(model_path="model.xml"),
        )
    except RealOpenVINORuntimeError as exc:
        assert "requires raw OpenVINO inputs" in str(exc)
    else:  # pragma: no cover - garde de sûreté.
        raise AssertionError("RealOpenVINORuntimeError was not raised")


def test_real_openvino_runtime_reports_missing_openvino_package() -> None:
    runtime = RealOpenVINORuntime()

    try:
        runtime._core_instance()
    except RealOpenVINORuntimeUnavailable as exc:
        assert "OpenVINO is not installed" in str(exc)
    else:  # pragma: no cover - environnement avec openvino installé.
        assert runtime.state().available is True
