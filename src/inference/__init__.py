from __future__ import annotations

from .adapter import InferenceAdapter
from .backend import DummyInferenceBackend
from .handlers import InferenceRequestHandler
from .model_profile import (
    OpenVINOModelProfile,
    OpenVINOModelProfileRegistry,
    OpenVINOModelProfileRegistrySnapshot,
    SUPPORTED_OPENVINO_TASKS,
)
from .openvino_factory import (
    OpenVINOBackendBuildResult,
    OpenVINOBackendFactory,
    OpenVINORuntimeFactory,
)
from .openvino_backend import (
    OpenVINOBackend,
    OpenVINOBackendConfig,
    OpenVINOBackendError,
    OpenVINOBackendState,
    OpenVINORuntime,
)
from .openvino_runtime import (
    RealOpenVINORuntime,
    RealOpenVINORuntimeError,
    RealOpenVINORuntimeState,
    RealOpenVINORuntimeUnavailable,
)
from .registry import BackendRegistry, BackendRegistrySnapshot

__all__ = [
    "BackendRegistry",
    "BackendRegistrySnapshot",
    "DummyInferenceBackend",
    "InferenceAdapter",
    "InferenceRequestHandler",
    "OpenVINOBackendBuildResult",
    "OpenVINOBackendFactory",
    "OpenVINORuntimeFactory",
    "OpenVINOBackend",
    "OpenVINOBackendConfig",
    "OpenVINOBackendError",
    "OpenVINOBackendState",
    "OpenVINORuntime",
    "SUPPORTED_OPENVINO_TASKS",
    "OpenVINOModelProfileRegistrySnapshot",
    "OpenVINOModelProfileRegistry",
    "OpenVINOModelProfile",
    "RealOpenVINORuntime",
    "RealOpenVINORuntimeError",
    "RealOpenVINORuntimeState",
    "RealOpenVINORuntimeUnavailable",
]
