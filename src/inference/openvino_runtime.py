from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from contracts.inference import InferenceRequest, InferenceResult

from .openvino_backend import OpenVINOBackendConfig


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class RealOpenVINORuntimeState:
    """État observable du runtime OpenVINO réel.

    Cette structure ne contient pas le Core, le CompiledModel ou les tensors.
    Elle expose seulement une vue déterministe et sérialisable pour les tests,
    l'observabilité et les futurs rapports de diagnostic.
    """

    available: bool
    compiled_models: int
    infer_count: int
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)


class RealOpenVINORuntimeError(RuntimeError):
    """Erreur stable levée par le wrapper OpenVINO réel."""


class RealOpenVINORuntimeUnavailable(RealOpenVINORuntimeError):
    """Levée quand le paquet openvino n'est pas disponible."""


class RealOpenVINORuntime:
    """Runtime OpenVINO réel, isolé dans un seul module.

    Ce module est le seul endroit autorisé à importer ``openvino``. Il reste
    volontairement générique : il ne tokenise pas, ne choisit aucun modèle et ne
    connaît pas Qdrant. Il exécute uniquement des entrées OpenVINO brutes
    fournies dans ``InferenceRequest.context['inputs']``.
    """

    is_real_openvino_runtime = True

    def __init__(self, ov_module: Any | None = None) -> None:
        self._ov_module = ov_module
        self._core: Any | None = None
        self._compiled_models: dict[tuple[str, str], Any] = {}
        self._infer_count = 0

    @classmethod
    def with_imported_openvino(cls) -> RealOpenVINORuntime:
        """Construit le runtime en important le module openvino installé."""

        return cls(_load_openvino_module())

    def state(self) -> RealOpenVINORuntimeState:
        """Construit une vue immuable de l'état du runtime."""

        return RealOpenVINORuntimeState(
            available=self._ov_module is not None,
            compiled_models=len(self._compiled_models),
            infer_count=self._infer_count,
            metadata=MappingProxyType(
                {
                    "runtime": type(self).__name__,
                    "has_core": self._core is not None,
                }
            ),
        )

    async def infer(
        self,
        request: InferenceRequest,
        *,
        config: OpenVINOBackendConfig,
    ) -> InferenceResult:
        """Exécute une inférence OpenVINO sans bloquer l'event loop."""

        return await asyncio.to_thread(self._infer_sync, request, config)

    def close(self) -> None:
        """Libère les références au runtime OpenVINO."""

        self._compiled_models.clear()
        self._core = None

    def _infer_sync(
        self,
        request: InferenceRequest,
        config: OpenVINOBackendConfig,
    ) -> InferenceResult:
        inputs = _extract_raw_inputs(request)
        compiled_model = self._compiled_model(config)
        raw_outputs = _run_compiled_model(compiled_model, inputs)
        self._infer_count += 1

        return InferenceResult(
            text=f"openvino://{config.device}:{Path(config.model_path).name}",
            confidence=1.0,
            backend=config.backend_name,
            metadata=MappingProxyType(
                {
                    "model_path": config.model_path,
                    "device": config.device,
                    "input_kind": type(inputs).__name__,
                    "output_kind": type(raw_outputs).__name__,
                    "output_count": _output_count(raw_outputs),
                    "raw_outputs": raw_outputs,
                    "runtime": type(self).__name__,
                }
            ),
        )

    def _compiled_model(self, config: OpenVINOBackendConfig) -> Any:
        key = (config.model_path, config.device)
        compiled = self._compiled_models.get(key)
        if compiled is not None:
            return compiled

        core = self._core_instance()
        try:
            if hasattr(core, "read_model"):
                model = core.read_model(config.model_path)
                compiled = core.compile_model(model, config.device)
            else:
                compiled = core.compile_model(config.model_path, config.device)
        except Exception as exc:  # pragma: no cover - dépend du runtime réel.
            raise RealOpenVINORuntimeError(
                f"OpenVINO model compilation failed for {config.model_path!r} "
                f"on device {config.device!r}: {exc}"
            ) from exc

        self._compiled_models[key] = compiled
        return compiled

    def _core_instance(self) -> Any:
        if self._core is not None:
            return self._core

        ov_module = self._ov_module or _load_openvino_module()
        core_type = getattr(ov_module, "Core", None)
        if core_type is None:
            raise RealOpenVINORuntimeError("openvino module does not expose Core")

        self._ov_module = ov_module
        self._core = core_type()
        return self._core


def _load_openvino_module() -> Any:
    try:
        import openvino as ov
    except ModuleNotFoundError as exc:
        raise RealOpenVINORuntimeUnavailable(
            "OpenVINO is not installed. Install it before using RealOpenVINORuntime."
        ) from exc
    return ov


def _extract_raw_inputs(request: InferenceRequest) -> Any:
    inputs = request.context.get("inputs")
    if inputs is None:
        inputs = request.metadata.get("inputs")
    if inputs is None:
        raise RealOpenVINORuntimeError(
            "RealOpenVINORuntime requires raw OpenVINO inputs under "
            "InferenceRequest.context['inputs'] or metadata['inputs']."
        )
    return inputs


def _run_compiled_model(compiled_model: Any, inputs: Any) -> Any:
    try:
        if callable(compiled_model):
            return compiled_model(inputs)
        if hasattr(compiled_model, "create_infer_request"):
            infer_request = compiled_model.create_infer_request()
            return infer_request.infer(inputs)
    except Exception as exc:  # pragma: no cover - dépend du runtime réel.
        raise RealOpenVINORuntimeError(f"OpenVINO inference failed: {exc}") from exc

    raise RealOpenVINORuntimeError(
        "Compiled OpenVINO model is neither callable nor InferRequest-compatible"
    )


def _output_count(raw_outputs: Any) -> int:
    if isinstance(raw_outputs, Mapping):
        return len(raw_outputs)
    if isinstance(raw_outputs, (tuple, list)):
        return len(raw_outputs)
    return 1
