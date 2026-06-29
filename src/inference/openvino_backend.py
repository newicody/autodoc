from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol

from contracts.inference import InferenceRequest, InferenceResult


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class OpenVINOBackendConfig:
    """Configuration stable du futur backend OpenVINO.

    Cette configuration ne charge pas OpenVINO. Elle décrit uniquement ce que
    le backend réel devra recevoir quand le runtime sera branché.
    """

    model_path: str
    device: str = "CPU"
    backend_name: str = "openvino"
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)


@dataclass(frozen=True, slots=True)
class OpenVINOBackendState:
    """État observable du backend OpenVINO sans exposer le runtime concret."""

    backend_name: str
    model_path: str
    device: str
    ready: bool
    request_count: int
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)


class OpenVINOBackendError(RuntimeError):
    """Erreur stable levée par la membrane OpenVINO."""


class OpenVINORuntime(Protocol):
    """Runtime injecté pour le futur backend OpenVINO.

    Le contrat reste volontairement minimal : le backend lui transmet une
    ``InferenceRequest`` et sa configuration. La vraie implémentation pourra
    cacher ``CompiledModel``, ``InferRequest`` ou un pool interne sans modifier
    le kernel.
    """

    async def infer(
        self,
        request: InferenceRequest,
        *,
        config: OpenVINOBackendConfig,
    ) -> InferenceResult:
        """Exécute une inférence via un runtime compatible OpenVINO."""
        ...


class OpenVINOBackend:
    """Backend OpenVINO contractuel, sans import du runtime OpenVINO.

    Cette classe valide la forme du futur backend, pas l'exécution réelle du
    moteur Intel. Le runtime est injecté pour permettre des tests déterministes
    avec un faux runtime. L'intégration réelle pourra donc remplacer uniquement
    l'objet runtime, sans toucher au Scheduler, au Dispatcher ni à
    l'InferenceAdapter.
    """

    def __init__(self, config: OpenVINOBackendConfig, runtime: OpenVINORuntime) -> None:
        if not config.backend_name:
            raise ValueError("OpenVINO backend name must not be empty")
        if not config.model_path:
            raise ValueError("OpenVINO model_path must not be empty")
        if not config.device:
            raise ValueError("OpenVINO device must not be empty")

        self._config = config
        self._runtime = runtime
        self._request_count = 0
        self._closed = False

    @property
    def name(self) -> str:
        """Nom utilisé par BackendRegistry."""

        return self._config.backend_name

    @property
    def config(self) -> OpenVINOBackendConfig:
        """Configuration immuable du backend."""

        return self._config

    def state(self) -> OpenVINOBackendState:
        """Construit une vue immuable de l'état courant."""

        return OpenVINOBackendState(
            backend_name=self.name,
            model_path=self._config.model_path,
            device=self._config.device,
            ready=not self._closed,
            request_count=self._request_count,
            metadata=MappingProxyType(
                {
                    "runtime": type(self._runtime).__name__,
                    "has_real_openvino": False,
                }
            ),
        )

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        """Exécute une inférence via le runtime injecté."""

        if self._closed:
            raise OpenVINOBackendError("OpenVINO backend is closed")

        self._request_count += 1
        result = await self._runtime.infer(request, config=self._config)
        if result.backend != self.name:
            return InferenceResult(
                text=result.text,
                confidence=result.confidence,
                backend=self.name,
                metadata=MappingProxyType(
                    {
                        **dict(result.metadata),
                        "wrapped_backend": result.backend,
                    }
                ),
            )
        return result

    def close(self) -> None:
        """Ferme la membrane backend.

        La vraie implémentation OpenVINO pourra libérer ici ses ressources. En
        Phase 2.6, on garde seulement un état déterministe testable.
        """

        self._closed = True
