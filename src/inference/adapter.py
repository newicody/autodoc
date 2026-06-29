from __future__ import annotations

from contracts.inference import InferenceBackend, InferenceRequest, InferenceResult

from .registry import BackendRegistry


class InferenceAdapter:
    """Membrane stable entre les handlers kernel et les backends d'inférence.

    Le Scheduler ne connaît ni cet adapter ni les backends concrets. Le
    Launcher assemble le handler avec cet adapter, puis le Dispatcher route
    uniquement les événements ``INFERENCE_REQUEST``.
    """

    name = "inference-adapter"

    def __init__(self, registry: BackendRegistry) -> None:
        self._registry = registry

    @classmethod
    def from_backend(cls, default_backend: InferenceBackend) -> InferenceAdapter:
        """Construit un adapter minimal autour d'un backend unique."""

        registry = BackendRegistry()
        registry.register(default_backend, make_default=True)
        return cls(registry)

    @property
    def registry(self) -> BackendRegistry:
        """Registre utilisé par l'adapter."""

        return self._registry

    @property
    def default_backend_name(self) -> str:
        """Nom du backend par défaut."""

        return self._registry.default_backend_name

    def select_backend(self, request: InferenceRequest) -> InferenceBackend:
        """Sélectionne le backend demandé via le registre."""

        return self._registry.select(request.model)

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        """Délègue l'inférence au backend sélectionné."""

        backend = self.select_backend(request)
        return await backend.infer(request)
