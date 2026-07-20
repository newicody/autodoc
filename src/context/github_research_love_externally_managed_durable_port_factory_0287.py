"""Compose the durable OpenRC ports from one explicit installed component factory.

The r16-r59 foundation already owns the unique Scheduler and the installed
PostgreSQL, OpenVINO and Qdrant resources.  This module does not open a backend.
It loads one explicit component factory, validates the seven durable ports and
returns the typed r16-r60 bundle aligned with the existing foundation.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from importlib import import_module
import inspect
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any

from context.github_research_love_externally_managed_component_binding_0287 import (
    EXTERNALLY_MANAGED_DURABLE_PORTS_SCHEMA,
    GitHubResearchLoveExternallyManagedDurablePorts,
)
from context.love_externally_managed_installed_backend_foundation_0287 import (
    LoveExternallyManagedInstalledBackendFoundation,
)
from context.love_installed_runtime_factory_0287 import InstalledRuntimeFactorySettings

EXTERNALLY_MANAGED_DURABLE_COMPONENTS_SCHEMA = (
    "missipy.github.research_love_externally_managed_durable_components.v1"
)
DURABLE_COMPONENT_FACTORY_ENV = (
    "AUTODOC_GITHUB_RESEARCH_EXTERNALLY_MANAGED_DURABLE_COMPONENT_FACTORY"
)


class GitHubResearchLoveExternallyManagedDurablePortFactoryError(RuntimeError):
    """Raised when one installed durable component set cannot fail closed."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveExternallyManagedDurableComponents:
    """Seven durable ports built around the already-open r16-r59 foundation."""

    schema: str
    continuation_store: object = field(repr=False, compare=False)
    step_runner_builder: Callable[..., object] = field(repr=False, compare=False)
    first_visit_input_provider: object = field(repr=False, compare=False)
    grouped_input_provider: object = field(repr=False, compare=False)
    downstream_input_provider: object = field(repr=False, compare=False)
    publication_input_provider: object = field(repr=False, compare=False)
    observation_store: object = field(repr=False, compare=False)
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != EXTERNALLY_MANAGED_DURABLE_COMPONENTS_SCHEMA:
            raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
                "schéma de composants durables non pris en charge"
            )
        _methods(self.continuation_store, ("load_snapshot", "commit_promotion"))
        if not callable(self.step_runner_builder):
            raise TypeError("step_runner_builder doit être callable")
        _methods(self.first_visit_input_provider, ("load",))
        _methods(
            self.grouped_input_provider,
            (
                "load_first_dispatch_command",
                "load_second_dispatch_command",
                "load_pair_stage_input",
            ),
        )
        _methods(
            self.downstream_input_provider,
            (
                "load_recall_command",
                "load_synthesis_command",
                "load_final_deliverable_command",
            ),
        )
        _methods(
            self.publication_input_provider,
            (
                "load_publication_command",
                "load_publication_authorization",
                "load_cycle_closure_result",
            ),
        )
        _methods(self.observation_store, ("initialize_schema", "append_many"))
        if not self.evidence_refs:
            raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
                "les composants durables doivent exposer une preuve d'installation"
            )
        for value in self.evidence_refs:
            _typed_ref("evidence_ref", value)

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "evidence_refs": self.evidence_refs,
                "component_count": 7,
                "foundation_reused": True,
                "new_backend_opened": False,
                "postgresql_durable_authority": True,
                "internal_json_storage_created": False,
                "jsonl_queue_created": False,
            }
        )


def build_github_research_love_externally_managed_durable_ports(
    *,
    settings: InstalledRuntimeFactorySettings,
    foundation: LoveExternallyManagedInstalledBackendFoundation,
    config_path: str | os.PathLike[str] | None = None,
    environment: Mapping[str, str] | None = None,
) -> GitHubResearchLoveExternallyManagedDurablePorts:
    """Build the typed r16-r60 durable ports without reopening a backend."""

    if not isinstance(settings, InstalledRuntimeFactorySettings):
        raise TypeError("settings doit être InstalledRuntimeFactorySettings")
    if not isinstance(foundation, LoveExternallyManagedInstalledBackendFoundation):
        raise TypeError(
            "foundation doit être LoveExternallyManagedInstalledBackendFoundation"
        )
    if settings.scheduler_lifecycle != "externally-managed":
        raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
            "la fabrique durable exige scheduler lifecycle externally-managed"
        )
    if foundation.scheduler_ref != settings.scheduler_ref:
        raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
            "scheduler_ref de la fondation diverge de la configuration installée"
        )
    if foundation.base_revision_ref != settings.base_revision_ref:
        raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
            "base_revision_ref de la fondation diverge de la configuration installée"
        )

    env = os.environ if environment is None else environment
    factory_ref = str(env.get(DURABLE_COMPONENT_FACTORY_ENV, "")).strip()
    if not factory_ref:
        raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
            f"fabrique de composants durables absente: définir {DURABLE_COMPONENT_FACTORY_ENV}"
        )
    factory = _load_factory(factory_ref)
    provided = factory(
        **_supported_keywords(
            factory,
            {
                "settings": settings,
                "foundation": foundation,
                "config_path": Path(config_path or settings.config_path),
                "environment": env,
            },
        )
    )
    if not isinstance(
        provided,
        GitHubResearchLoveExternallyManagedDurableComponents,
    ):
        raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
            "la fabrique configurée doit retourner le bundle typé r16-r61"
        )

    collection_name = str(getattr(foundation.collection, "collection_name", ""))
    if not collection_name:
        raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
            "la fondation n'expose pas de collection Qdrant"
        )
    return GitHubResearchLoveExternallyManagedDurablePorts(
        schema=EXTERNALLY_MANAGED_DURABLE_PORTS_SCHEMA,
        scheduler_ref=foundation.scheduler_ref,
        base_revision_ref=foundation.base_revision_ref,
        collection_name=collection_name,
        embedding_dimension=384,
        continuation_store=provided.continuation_store,
        step_runner_builder=provided.step_runner_builder,
        first_visit_input_provider=provided.first_visit_input_provider,
        grouped_input_provider=provided.grouped_input_provider,
        downstream_input_provider=provided.downstream_input_provider,
        publication_input_provider=provided.publication_input_provider,
        observation_store=provided.observation_store,
        evidence_refs=_unique_refs(
            provided.evidence_refs
            + ("evidence:externally-managed-durable-port-factory-r16-r61",)
        ),
    )


def _load_factory(reference: str) -> Callable[..., object]:
    module_name, separator, function_name = reference.partition(":")
    if not separator or not module_name.strip() or not function_name.strip():
        raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
            f"{DURABLE_COMPONENT_FACTORY_ENV} doit utiliser module:function"
        )
    try:
        module = import_module(module_name.strip())
    except Exception as exc:
        raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
            f"impossible d'importer la fabrique durable {module_name.strip()}"
        ) from exc
    factory = getattr(module, function_name.strip(), None)
    if not callable(factory):
        raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
            "la fabrique de composants durables n'est pas callable"
        )
    return factory


def _supported_keywords(
    factory: Callable[..., object],
    available: Mapping[str, object],
) -> Mapping[str, object]:
    try:
        signature = inspect.signature(factory)
    except (TypeError, ValueError):
        return available
    if any(
        value.kind is inspect.Parameter.VAR_KEYWORD
        for value in signature.parameters.values()
    ):
        return available
    names = {
        name
        for name, value in signature.parameters.items()
        if value.kind
        in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }
    }
    return MappingProxyType(
        {name: value for name, value in available.items() if name in names}
    )


def _methods(value: object, names: tuple[str, ...]) -> None:
    for name in names:
        if not callable(getattr(value, name, None)):
            raise TypeError(f"{type(value).__name__} doit exposer {name}")


def _typed_ref(name: str, value: object) -> None:
    if not isinstance(value, str) or ":" not in value or any(ch.isspace() for ch in value):
        raise GitHubResearchLoveExternallyManagedDurablePortFactoryError(
            f"{name} doit être une référence typée"
        )


def _unique_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        _typed_ref("evidence_ref", value)
        if value not in result:
            result.append(value)
    return tuple(result)


__all__ = (
    "DURABLE_COMPONENT_FACTORY_ENV",
    "EXTERNALLY_MANAGED_DURABLE_COMPONENTS_SCHEMA",
    "GitHubResearchLoveExternallyManagedDurableComponents",
    "GitHubResearchLoveExternallyManagedDurablePortFactoryError",
    "build_github_research_love_externally_managed_durable_ports",
)
