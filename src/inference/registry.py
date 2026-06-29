from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from contracts.inference import InferenceBackend


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class BackendRegistrySnapshot:
    """Vue immuable des backends d'inférence connus.

    Le snapshot sert à exposer l'état du registre sans divulguer les instances
    concrètes des backends. Il est donc sûr pour l'observabilité, les tests et
    les futures politiques de sélection.
    """

    default_backend_name: str
    backend_names: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)


class BackendRegistry:
    """Registre explicite des backends d'inférence.

    Le registre est volontairement séparé de l'InferenceAdapter :

    - le registre connaît les backends disponibles ;
    - l'adapter exécute une requête via le backend sélectionné ;
    - le Scheduler ne connaît ni l'un ni l'autre.

    Cette séparation prépare OpenVINO sans l'introduire dans le kernel.
    """

    def __init__(self) -> None:
        self._backends: dict[str, InferenceBackend] = {}
        self._default_backend_name = ""

    @property
    def default_backend_name(self) -> str:
        """Nom du backend par défaut."""

        return self._default_backend_name

    @property
    def backends(self) -> Mapping[str, InferenceBackend]:
        """Vue immuable des backends enregistrés."""

        return MappingProxyType(self._backends)

    def register(self, backend: InferenceBackend, *, make_default: bool = False) -> None:
        """Enregistre un backend explicitement.

        Un nom déjà présent est refusé. Remplacer un backend doit rester un acte
        explicite dans une future phase, car cela peut modifier les résultats
        d'inférence et donc le replay.
        """

        if not backend.name:
            raise ValueError("Inference backend name must not be empty")
        if backend.name in self._backends:
            raise ValueError(f"Inference backend {backend.name!r} is already registered")

        self._backends[backend.name] = backend
        if make_default or not self._default_backend_name:
            self._default_backend_name = backend.name

    def select(self, model: str) -> InferenceBackend:
        """Retourne le backend demandé, sans fallback implicite dangereux."""

        backend_name = model or self._default_backend_name
        backend = self._backends.get(backend_name)
        if backend is None:
            available = ", ".join(self.backend_names()) or "none"
            raise LookupError(
                f"No inference backend registered for model '{backend_name}'. "
                f"Available backends: {available}"
            )
        return backend

    def backend_names(self) -> tuple[str, ...]:
        """Noms triés des backends connus."""

        return tuple(sorted(self._backends))

    def snapshot(self) -> BackendRegistrySnapshot:
        """Construit un snapshot immuable du registre."""

        return BackendRegistrySnapshot(
            default_backend_name=self._default_backend_name,
            backend_names=self.backend_names(),
            metadata=MappingProxyType({"count": len(self._backends)}),
        )
