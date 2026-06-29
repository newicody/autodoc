from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from contracts.inference import InferenceBackend, InferenceRequest, InferenceResult


class InferenceAdapter:
    """Membrane stable entre les handlers kernel et les backends d'inférence.

    Le Scheduler ne connaît ni cet adapter ni les backends concrets. Le
    Launcher assemble le handler avec cet adapter, puis le Dispatcher route
    uniquement les événements ``INFERENCE_REQUEST``.
    """

    name = "inference-adapter"

    def __init__(self, default_backend: InferenceBackend) -> None:
        self._default_backend_name = default_backend.name
        self._backends: dict[str, InferenceBackend] = {}
        self.register_backend(default_backend)

    @property
    def default_backend_name(self) -> str:
        """Nom du backend utilisé quand la requête ne précise pas de modèle."""

        return self._default_backend_name

    @property
    def backends(self) -> Mapping[str, InferenceBackend]:
        """Vue immuable des backends connus de l'adapter."""

        return MappingProxyType(self._backends)

    def register_backend(self, backend: InferenceBackend) -> None:
        """Ajoute ou remplace explicitement un backend d'inférence."""

        if not backend.name:
            raise ValueError("Inference backend name must not be empty")
        self._backends[backend.name] = backend

    def select_backend(self, request: InferenceRequest) -> InferenceBackend:
        """Sélectionne le backend demandé sans fallback implicite dangereux."""

        backend_name = request.model or self._default_backend_name
        backend = self._backends.get(backend_name)
        if backend is None:
            available = ", ".join(sorted(self._backends)) or "none"
            raise LookupError(
                f"No inference backend registered for model '{backend_name}'. "
                f"Available backends: {available}"
            )
        return backend

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        """Délègue l'inférence au backend sélectionné."""

        backend = self.select_backend(request)
        return await backend.infer(request)
