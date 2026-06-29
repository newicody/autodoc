from __future__ import annotations

import pytest

from contracts.inference import InferenceRequest, InferenceResult
from inference.backend import DummyInferenceBackend
from inference.registry import BackendRegistry


class EchoBackend:
    name = "echo"

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        return InferenceResult(text=request.prompt, confidence=0.5, backend=self.name)


def test_backend_registry_registers_default_backend() -> None:
    registry = BackendRegistry()
    backend = DummyInferenceBackend()

    registry.register(backend, make_default=True)
    snapshot = registry.snapshot()

    assert registry.default_backend_name == "dummy"
    assert registry.select("dummy") is backend
    assert registry.select("") is backend
    assert snapshot.default_backend_name == "dummy"
    assert snapshot.backend_names == ("dummy",)
    assert snapshot.metadata["count"] == 1


def test_backend_registry_rejects_duplicate_backend_name() -> None:
    registry = BackendRegistry()
    registry.register(DummyInferenceBackend())

    with pytest.raises(ValueError, match="already registered"):
        registry.register(DummyInferenceBackend())


def test_backend_registry_rejects_unknown_backend() -> None:
    registry = BackendRegistry()
    registry.register(DummyInferenceBackend(), make_default=True)

    with pytest.raises(LookupError, match="missing"):
        registry.select("missing")


def test_backend_registry_keeps_backend_names_sorted() -> None:
    registry = BackendRegistry()
    registry.register(DummyInferenceBackend())
    registry.register(EchoBackend())

    assert registry.backend_names() == ("dummy", "echo")
