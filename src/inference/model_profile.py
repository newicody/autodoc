from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .openvino_backend import OpenVINOBackendConfig


SUPPORTED_OPENVINO_TASKS = frozenset({"embedding", "generation", "raw"})


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class OpenVINOModelProfile:
    """Profil déclaratif d'un modèle OpenVINO possible.

    Un profil ne charge pas le modèle et n'importe pas OpenVINO. Il décrit
    seulement comment un modèle devra être exposé au BackendRegistry quand on
    décidera de l'activer. Cela permet de préparer un ou plusieurs modèles sans
    modifier le Scheduler, l'InferenceAdapter ou le handler d'inférence.
    """

    name: str
    model_path: str
    task: str
    device: str = "CPU"
    backend_name: str = "openvino"
    input_names: tuple[str, ...] = ()
    output_names: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("OpenVINOModelProfile.name must not be empty")
        if not self.model_path:
            raise ValueError("OpenVINOModelProfile.model_path must not be empty")
        if not self.task:
            raise ValueError("OpenVINOModelProfile.task must not be empty")
        if self.task not in SUPPORTED_OPENVINO_TASKS:
            allowed = ", ".join(sorted(SUPPORTED_OPENVINO_TASKS))
            raise ValueError(f"Unsupported OpenVINO task {self.task!r}. Allowed: {allowed}")
        if not self.device:
            raise ValueError("OpenVINOModelProfile.device must not be empty")
        if not self.backend_name:
            raise ValueError("OpenVINOModelProfile.backend_name must not be empty")

        object.__setattr__(self, "input_names", tuple(self.input_names))
        object.__setattr__(self, "output_names", tuple(self.output_names))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def inference_model_name(self) -> str:
        """Nom à placer dans InferenceRequest.model pour sélectionner ce profil."""

        return self.name

    def to_backend_config(self) -> OpenVINOBackendConfig:
        """Construit la configuration backend correspondant au profil."""

        return OpenVINOBackendConfig(
            model_path=self.model_path,
            device=self.device,
            backend_name=self.name,
            metadata=MappingProxyType(
                {
                    **dict(self.metadata),
                    "profile_name": self.name,
                    "profile_backend": self.backend_name,
                    "task": self.task,
                    "input_names": self.input_names,
                    "output_names": self.output_names,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class OpenVINOModelProfileRegistrySnapshot:
    """Vue immuable des profils OpenVINO connus."""

    profile_names: tuple[str, ...]
    tasks: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)


class OpenVINOModelProfileRegistry:
    """Registre déclaratif de profils modèles OpenVINO.

    Ce registre n'est pas le BackendRegistry : il ne contient aucun moteur
    exécutable. Il liste seulement les modèles possibles pour permettre un choix
    explicite, reproductible et testable avant de créer les backends réels.
    """

    def __init__(self) -> None:
        self._profiles: dict[str, OpenVINOModelProfile] = {}

    @property
    def profiles(self) -> Mapping[str, OpenVINOModelProfile]:
        """Vue immuable des profils enregistrés."""

        return MappingProxyType(self._profiles)

    def register(self, profile: OpenVINOModelProfile) -> None:
        """Enregistre un profil de modèle sans fallback implicite."""

        if profile.name in self._profiles:
            raise ValueError(f"OpenVINO model profile {profile.name!r} is already registered")
        self._profiles[profile.name] = profile

    def select(self, name: str) -> OpenVINOModelProfile:
        """Retourne le profil demandé explicitement."""

        profile = self._profiles.get(name)
        if profile is None:
            available = ", ".join(self.profile_names()) or "none"
            raise LookupError(f"No OpenVINO model profile {name!r}. Available profiles: {available}")
        return profile

    def by_task(self, task: str) -> tuple[OpenVINOModelProfile, ...]:
        """Retourne les profils d'une tâche donnée, dans un ordre stable."""

        if task not in SUPPORTED_OPENVINO_TASKS:
            allowed = ", ".join(sorted(SUPPORTED_OPENVINO_TASKS))
            raise ValueError(f"Unsupported OpenVINO task {task!r}. Allowed: {allowed}")
        return tuple(profile for profile in self._sorted_profiles() if profile.task == task)

    def profile_names(self) -> tuple[str, ...]:
        """Noms triés des profils connus."""

        return tuple(sorted(self._profiles))

    def tasks(self) -> tuple[str, ...]:
        """Tâches actuellement représentées par les profils connus."""

        return tuple(sorted({profile.task for profile in self._profiles.values()}))

    def snapshot(self) -> OpenVINOModelProfileRegistrySnapshot:
        """Construit une vue immuable du registre de profils."""

        return OpenVINOModelProfileRegistrySnapshot(
            profile_names=self.profile_names(),
            tasks=self.tasks(),
            metadata=MappingProxyType({"count": len(self._profiles)}),
        )

    def _sorted_profiles(self) -> tuple[OpenVINOModelProfile, ...]:
        return tuple(self._profiles[name] for name in self.profile_names())
