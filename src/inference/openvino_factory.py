from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .model_profile import OpenVINOModelProfile, OpenVINOModelProfileRegistry
from .openvino_backend import OpenVINOBackend, OpenVINOBackendConfig, OpenVINORuntime
from .registry import BackendRegistry


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


OpenVINORuntimeFactory = Callable[[OpenVINOModelProfile, OpenVINOBackendConfig], OpenVINORuntime]


@dataclass(frozen=True, slots=True)
class OpenVINOBackendBuildResult:
    """Résultat immuable d'une construction de backend depuis un profil.

    Cette structure ne contient pas l'instance backend ni le runtime concret.
    Elle sert uniquement à tracer ce qui a été construit et enregistré, sans
    exposer d'objet vivant à l'observabilité ou aux rapports.
    """

    profile_name: str
    backend_name: str
    model_path: str
    device: str
    registered: bool
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.profile_name:
            raise ValueError("OpenVINOBackendBuildResult.profile_name must not be empty")
        if not self.backend_name:
            raise ValueError("OpenVINOBackendBuildResult.backend_name must not be empty")
        if not self.model_path:
            raise ValueError("OpenVINOBackendBuildResult.model_path must not be empty")
        if not self.device:
            raise ValueError("OpenVINOBackendBuildResult.device must not be empty")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class OpenVINOBackendFactory:
    """Construit des backends OpenVINO depuis des profils déclaratifs.

    La factory relie la couche ``OpenVINOModelProfile`` à la couche exécutable
    ``OpenVINOBackend``. Elle ne sélectionne aucun modèle implicitement et
    n'importe pas ``openvino`` : le runtime est fourni par injection.
    """

    def __init__(self, runtime_factory: OpenVINORuntimeFactory) -> None:
        self._runtime_factory = runtime_factory

    def build(self, profile: OpenVINOModelProfile) -> OpenVINOBackend:
        """Construit un backend non enregistré depuis un profil explicite."""

        config = profile.to_backend_config()
        runtime = self._runtime_factory(profile, config)
        return OpenVINOBackend(config, runtime)

    def build_and_register(
        self,
        profile: OpenVINOModelProfile,
        backend_registry: BackendRegistry,
        *,
        make_default: bool = False,
    ) -> OpenVINOBackendBuildResult:
        """Construit puis enregistre un backend dans BackendRegistry."""

        backend = self.build(profile)
        backend_registry.register(backend, make_default=make_default)
        return _build_result(profile, backend.config, registered=True)

    def build_selected_and_register(
        self,
        profile_registry: OpenVINOModelProfileRegistry,
        profile_name: str,
        backend_registry: BackendRegistry,
        *,
        make_default: bool = False,
    ) -> OpenVINOBackendBuildResult:
        """Sélectionne un profil par nom, puis enregistre son backend.

        Il n'y a pas de fallback : le nom du profil doit être fourni par la
        configuration de lancement ou par une décision explicite future.
        """

        profile = profile_registry.select(profile_name)
        return self.build_and_register(
            profile,
            backend_registry,
            make_default=make_default,
        )

    def build_all_for_task(
        self,
        profile_registry: OpenVINOModelProfileRegistry,
        task: str,
        backend_registry: BackendRegistry,
    ) -> tuple[OpenVINOBackendBuildResult, ...]:
        """Construit tous les profils d'une tâche dans un ordre stable."""

        return tuple(
            self.build_and_register(profile, backend_registry)
            for profile in profile_registry.by_task(task)
        )


def _build_result(
    profile: OpenVINOModelProfile,
    config: OpenVINOBackendConfig,
    *,
    registered: bool,
) -> OpenVINOBackendBuildResult:
    return OpenVINOBackendBuildResult(
        profile_name=profile.name,
        backend_name=config.backend_name,
        model_path=config.model_path,
        device=config.device,
        registered=registered,
        metadata=MappingProxyType(
            {
                "task": profile.task,
                "profile_backend": profile.backend_name,
                "input_names": profile.input_names,
                "output_names": profile.output_names,
            }
        ),
    )
