"""Compose the durable OpenRC components around the shared SQL boundary.

The PostgreSQL observation store is built by the r16-r62 boundary on the
connection already owned by the installed foundation.  One explicit
execution-component factory supplies the six remaining ports: durable
continuation, ready-task step runner builder and the four typed handler
input providers.

This module opens no backend and owns no process.  It only verifies that the
supplied components reuse the same foundation and returns the r16-r61 typed
durable component bundle.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from importlib import import_module
import inspect
import os
from pathlib import Path
from types import MappingProxyType

from context.github_research_love_externally_managed_durable_port_factory_0287 import (
    EXTERNALLY_MANAGED_DURABLE_COMPONENTS_SCHEMA,
    GitHubResearchLoveExternallyManagedDurableComponents,
)
from context.github_research_love_externally_managed_postgresql_adapter_boundary_0287 import (
    GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundary,
    build_github_research_love_externally_managed_postgresql_adapter_boundary,
)
from context.love_externally_managed_installed_backend_foundation_0287 import (
    LoveExternallyManagedInstalledBackendFoundation,
)
from context.love_installed_runtime_factory_0287 import (
    InstalledRuntimeFactorySettings,
)

EXTERNALLY_MANAGED_EXECUTION_COMPONENTS_SCHEMA = (
    "missipy.github.research_love_externally_managed_execution_components.v1"
)
EXECUTION_COMPONENT_FACTORY_ENV = (
    "AUTODOC_GITHUB_RESEARCH_EXTERNALLY_MANAGED_EXECUTION_COMPONENT_FACTORY"
)


class GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
    RuntimeError
):
    """Raised when one durable component composition cannot fail closed."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveExternallyManagedExecutionComponents:
    """Six execution ports that reuse one already-open installed foundation."""

    schema: str
    continuation_store: object = field(repr=False, compare=False)
    step_runner_builder: Callable[..., object] = field(
        repr=False,
        compare=False,
    )
    first_visit_input_provider: object = field(repr=False, compare=False)
    grouped_input_provider: object = field(repr=False, compare=False)
    downstream_input_provider: object = field(repr=False, compare=False)
    publication_input_provider: object = field(repr=False, compare=False)
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != EXTERNALLY_MANAGED_EXECUTION_COMPONENTS_SCHEMA:
            raise (
                GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
                    "schéma de composants d'exécution non pris en charge"
                )
            )
        _methods(
            self.continuation_store,
            ("load_snapshot", "commit_promotion"),
        )
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
        if not self.evidence_refs:
            raise (
                GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
                    "les composants d'exécution doivent exposer une preuve"
                )
            )
        for value in self.evidence_refs:
            _typed_ref("evidence_ref", value)

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "component_count": 6,
                "evidence_refs": self.evidence_refs,
                "foundation_reused": True,
                "postgresql_connection_reused": True,
                "new_backend_opened": False,
                "scheduler_created": False,
                "internal_json_storage_created": False,
                "jsonl_queue_created": False,
            }
        )


def build_github_research_love_externally_managed_durable_components(
    *,
    settings: InstalledRuntimeFactorySettings,
    foundation: LoveExternallyManagedInstalledBackendFoundation,
    config_path: str | os.PathLike[str] | None = None,
    environment: Mapping[str, str] | None = None,
) -> GitHubResearchLoveExternallyManagedDurableComponents:
    """Build all seven durable ports while reusing the r16-r62 SQL store."""

    if not isinstance(settings, InstalledRuntimeFactorySettings):
        raise TypeError("settings doit être InstalledRuntimeFactorySettings")
    if not isinstance(
        foundation,
        LoveExternallyManagedInstalledBackendFoundation,
    ):
        raise TypeError(
            "foundation doit être LoveExternallyManagedInstalledBackendFoundation"
        )
    if settings.scheduler_lifecycle != "externally-managed":
        raise (
            GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
                "la composition exige scheduler lifecycle externally-managed"
            )
        )
    if settings.scheduler_ref != foundation.scheduler_ref:
        raise (
            GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
                "scheduler_ref diverge entre configuration et fondation"
            )
        )

    postgresql = (
        build_github_research_love_externally_managed_postgresql_adapter_boundary(
            foundation=foundation,
        )
    )
    _validate_postgresql_boundary(foundation, postgresql)

    env = os.environ if environment is None else environment
    factory_ref = str(env.get(EXECUTION_COMPONENT_FACTORY_ENV, "")).strip()
    if not factory_ref:
        raise (
            GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
                "fabrique de composants d'exécution absente: définir "
                + EXECUTION_COMPONENT_FACTORY_ENV
            )
        )
    factory = _load_factory(factory_ref)
    provided = factory(
        **_supported_keywords(
            factory,
            {
                "settings": settings,
                "foundation": foundation,
                "postgresql_boundary": postgresql,
                "postgresql_adapter_port": postgresql.adapter_port,
                "config_path": Path(config_path or settings.config_path),
                "environment": env,
            },
        )
    )
    if not isinstance(
        provided,
        GitHubResearchLoveExternallyManagedExecutionComponents,
    ):
        raise (
            GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
                "la fabrique configurée doit retourner le bundle typé r16-r63"
            )
        )

    return GitHubResearchLoveExternallyManagedDurableComponents(
        schema=EXTERNALLY_MANAGED_DURABLE_COMPONENTS_SCHEMA,
        continuation_store=provided.continuation_store,
        step_runner_builder=provided.step_runner_builder,
        first_visit_input_provider=provided.first_visit_input_provider,
        grouped_input_provider=provided.grouped_input_provider,
        downstream_input_provider=provided.downstream_input_provider,
        publication_input_provider=provided.publication_input_provider,
        observation_store=postgresql.observation_store,
        evidence_refs=_unique_refs(
            postgresql.evidence_refs
            + provided.evidence_refs
            + (
                "evidence:externally-managed-durable-component-composition-r16-r63",
            )
        ),
    )


def _validate_postgresql_boundary(
    foundation: LoveExternallyManagedInstalledBackendFoundation,
    boundary: GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundary,
) -> None:
    if not isinstance(
        boundary,
        GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundary,
    ):
        raise TypeError(
            "la frontière PostgreSQL doit être le bundle typé r16-r62"
        )
    if boundary.adapter_port is not foundation.postgresql_adapter_port:
        raise (
            GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
                "la frontière PostgreSQL n'utilise pas le port de la fondation"
            )
        )


def _load_factory(reference: str) -> Callable[..., object]:
    module_name, separator, function_name = reference.partition(":")
    if not separator or not module_name.strip() or not function_name.strip():
        raise (
            GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
                f"{EXECUTION_COMPONENT_FACTORY_ENV} doit utiliser module:function"
            )
        )
    try:
        module = import_module(module_name.strip())
    except Exception as exc:
        raise (
            GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
                f"impossible d'importer {module_name.strip()}"
            )
        ) from exc
    factory = getattr(module, function_name.strip(), None)
    if not callable(factory):
        raise (
            GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
                "la fabrique de composants d'exécution n'est pas callable"
            )
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
    if (
        not isinstance(value, str)
        or ":" not in value
        or any(ch.isspace() for ch in value)
    ):
        raise (
            GitHubResearchLoveExternallyManagedDurableComponentCompositionError(
                f"{name} doit être une référence typée"
            )
        )


def _unique_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        _typed_ref("evidence_ref", value)
        if value not in result:
            result.append(value)
    return tuple(result)


__all__ = (
    "EXECUTION_COMPONENT_FACTORY_ENV",
    "EXTERNALLY_MANAGED_EXECUTION_COMPONENTS_SCHEMA",
    "GitHubResearchLoveExternallyManagedDurableComponentCompositionError",
    "GitHubResearchLoveExternallyManagedExecutionComponents",
    "build_github_research_love_externally_managed_durable_components",
)
