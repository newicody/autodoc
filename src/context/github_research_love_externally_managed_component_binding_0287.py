"""Bind the installed OpenRC backend foundation to durable handler ports.

The r16-r59 foundation owns exactly one process-local Scheduler stack and the
installed PostgreSQL, OpenVINO and Qdrant resources.  This module loads one
explicit durable-port factory, verifies that every provider is aligned with
that foundation, and returns the typed r16-r58 component bundle.

The durable-port factory may build adapters around the injected foundation. It
must not open another SQL connection, Qdrant client, embedding runtime,
Scheduler, Dispatcher or EventBus. PostgreSQL remains the durable authority;
no internal JSON storage or JSONL queue is introduced.
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

from context.github_research_love_externally_managed_installed_composition_0287 import (
    EXTERNALLY_MANAGED_COMPONENTS_SCHEMA,
    GitHubResearchLoveExternallyManagedInstalledComponents,
)
from context.love_externally_managed_installed_backend_foundation_0287 import (
    LoveExternallyManagedInstalledBackendFoundation,
    build_love_externally_managed_installed_backend_foundation,
)
from context.love_installed_runtime_factory_0287 import InstalledRuntimeFactorySettings

EXTERNALLY_MANAGED_DURABLE_PORTS_SCHEMA = (
    "missipy.github.research_love_externally_managed_durable_ports.v1"
)
DURABLE_PORT_FACTORY_ENV = (
    "AUTODOC_GITHUB_RESEARCH_EXTERNALLY_MANAGED_DURABLE_PORT_FACTORY"
)


class GitHubResearchLoveExternallyManagedComponentBindingError(RuntimeError):
    """Raised when installed durable ports cannot align with one foundation."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveExternallyManagedDurablePorts:
    """Durable providers built around the already-open installed foundation."""

    schema: str
    scheduler_ref: str
    base_revision_ref: str
    collection_name: str
    embedding_dimension: int
    continuation_store: object = field(repr=False, compare=False)
    step_runner_builder: Callable[..., object] = field(repr=False, compare=False)
    first_visit_input_provider: object = field(repr=False, compare=False)
    grouped_input_provider: object = field(repr=False, compare=False)
    downstream_input_provider: object = field(repr=False, compare=False)
    publication_input_provider: object = field(repr=False, compare=False)
    observation_store: object = field(repr=False, compare=False)
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != EXTERNALLY_MANAGED_DURABLE_PORTS_SCHEMA:
            raise GitHubResearchLoveExternallyManagedComponentBindingError(
                "schéma de ports durables externally-managed non pris en charge"
            )
        _typed_ref("scheduler_ref", self.scheduler_ref, "scheduler:")
        _typed_ref("base_revision_ref", self.base_revision_ref, "context-revision:")
        if not isinstance(self.collection_name, str) or not self.collection_name.strip():
            raise GitHubResearchLoveExternallyManagedComponentBindingError(
                "collection_name doit être non vide"
            )
        if self.embedding_dimension != 384:
            raise GitHubResearchLoveExternallyManagedComponentBindingError(
                "les ports installés doivent conserver la dimension 384"
            )
        for name in ("load_snapshot", "commit_promotion"):
            _method(self.continuation_store, name)
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
            raise GitHubResearchLoveExternallyManagedComponentBindingError(
                "les ports durables doivent exposer une preuve d'installation"
            )
        for value in self.evidence_refs:
            _typed_ref("evidence_ref", value)

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "scheduler_ref": self.scheduler_ref,
                "base_revision_ref": self.base_revision_ref,
                "collection_name": self.collection_name,
                "embedding_dimension": self.embedding_dimension,
                "evidence_refs": self.evidence_refs,
                "postgresql_durable_authority": True,
                "qdrant_projection_and_recall": True,
                "openvino_e5_reused": True,
                "new_backend_opened": False,
                "internal_json_storage_created": False,
                "jsonl_queue_created": False,
            }
        )


def build_github_research_love_externally_managed_installed_components(
    *,
    settings: InstalledRuntimeFactorySettings,
    config_path: str | os.PathLike[str] | None = None,
    environment: Mapping[str, str] | None = None,
) -> GitHubResearchLoveExternallyManagedInstalledComponents:
    """Build the r16-r58 components from one r16-r59 foundation."""

    env = os.environ if environment is None else environment
    foundation = build_love_externally_managed_installed_backend_foundation(
        settings=settings,
        config_path=config_path,
        environment=env,
    )
    try:
        _validate_foundation(foundation)
        factory_ref = str(env.get(DURABLE_PORT_FACTORY_ENV, "")).strip()
        if not factory_ref:
            raise GitHubResearchLoveExternallyManagedComponentBindingError(
                f"fabrique de ports durables absente: définir {DURABLE_PORT_FACTORY_ENV}"
            )
        factory = _load_factory(factory_ref)
        provided = factory(
            **_supported_keywords(
                factory,
                {
                    "settings": settings,
                    "config_path": Path(config_path or settings.config_path),
                    "environment": env,
                    "foundation": foundation,
                },
            )
        )
        if not isinstance(
            provided,
            GitHubResearchLoveExternallyManagedDurablePorts,
        ):
            raise GitHubResearchLoveExternallyManagedComponentBindingError(
                "la fabrique durable doit retourner le bundle typé r16-r60"
            )
        _validate_alignment(foundation, provided)
        return GitHubResearchLoveExternallyManagedInstalledComponents(
            schema=EXTERNALLY_MANAGED_COMPONENTS_SCHEMA,
            scheduler=foundation.scheduler,
            scheduler_ref=foundation.scheduler_ref,
            command_store=foundation.command_store,
            continuation_store=provided.continuation_store,
            step_runner_builder=provided.step_runner_builder,
            first_visit_input_provider=provided.first_visit_input_provider,
            grouped_input_provider=provided.grouped_input_provider,
            downstream_input_provider=provided.downstream_input_provider,
            publication_input_provider=provided.publication_input_provider,
            observation_store=provided.observation_store,
            close_callbacks=tuple(foundation.close_callbacks),
            evidence_refs=_unique_refs(
                tuple(foundation.evidence_refs) + tuple(provided.evidence_refs)
            ),
        )
    except Exception:
        _close_foundation(foundation)
        raise


def _validate_foundation(
    foundation: LoveExternallyManagedInstalledBackendFoundation,
) -> None:
    for name in (
        "scheduler",
        "scheduler_ref",
        "command_store",
        "authority_store",
        "task_launch_transaction",
        "handler_execution_transaction",
        "projection_port",
        "collection",
        "embedder",
        "retrieval_executor",
        "base_revision_ref",
        "close_callbacks",
        "evidence_refs",
    ):
        if not hasattr(foundation, name):
            raise GitHubResearchLoveExternallyManagedComponentBindingError(
                f"la fondation installée n'expose pas {name}"
            )
    _typed_ref("foundation.scheduler_ref", foundation.scheduler_ref, "scheduler:")
    _typed_ref(
        "foundation.base_revision_ref",
        foundation.base_revision_ref,
        "context-revision:",
    )
    if not foundation.close_callbacks:
        raise GitHubResearchLoveExternallyManagedComponentBindingError(
            "la fondation doit posséder ses fermetures installées"
        )


def _validate_alignment(
    foundation: LoveExternallyManagedInstalledBackendFoundation,
    ports: GitHubResearchLoveExternallyManagedDurablePorts,
) -> None:
    if ports.scheduler_ref != foundation.scheduler_ref:
        raise GitHubResearchLoveExternallyManagedComponentBindingError(
            "scheduler_ref des ports durables diverge de la fondation"
        )
    if ports.base_revision_ref != foundation.base_revision_ref:
        raise GitHubResearchLoveExternallyManagedComponentBindingError(
            "base_revision_ref des ports durables diverge de la fondation"
        )
    collection_name = str(getattr(foundation.collection, "collection_name", ""))
    if ports.collection_name != collection_name:
        raise GitHubResearchLoveExternallyManagedComponentBindingError(
            "collection Qdrant des ports durables diverge de la fondation"
        )
    if ports.embedding_dimension != 384:
        raise GitHubResearchLoveExternallyManagedComponentBindingError(
            "dimension des ports durables divergente"
        )


def _load_factory(reference: str) -> Callable[..., object]:
    module_name, separator, function_name = reference.partition(":")
    if not separator or not module_name.strip() or not function_name.strip():
        raise GitHubResearchLoveExternallyManagedComponentBindingError(
            f"{DURABLE_PORT_FACTORY_ENV} doit utiliser module:function"
        )
    try:
        module = import_module(module_name.strip())
    except Exception as exc:
        raise GitHubResearchLoveExternallyManagedComponentBindingError(
            f"impossible d'importer la fabrique durable {module_name.strip()}"
        ) from exc
    factory = getattr(module, function_name.strip(), None)
    if factory is None or not callable(factory):
        raise GitHubResearchLoveExternallyManagedComponentBindingError(
            "la fabrique durable configurée n'est pas callable"
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
    supported = {
        name
        for name, value in signature.parameters.items()
        if value.kind
        in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }
    }
    return MappingProxyType(
        {name: value for name, value in available.items() if name in supported}
    )


def _close_foundation(
    foundation: LoveExternallyManagedInstalledBackendFoundation,
) -> None:
    for callback in reversed(tuple(getattr(foundation, "close_callbacks", ()))):
        try:
            callback()
        except Exception:
            pass


def _methods(value: object, names: tuple[str, ...]) -> None:
    for name in names:
        _method(value, name)


def _method(value: object, name: str) -> None:
    if not callable(getattr(value, name, None)):
        raise TypeError(f"{type(value).__name__} doit exposer {name}")


def _typed_ref(name: str, value: object, prefix: str = "") -> None:
    if not isinstance(value, str) or ":" not in value or any(ch.isspace() for ch in value):
        raise GitHubResearchLoveExternallyManagedComponentBindingError(
            f"{name} doit être une référence typée"
        )
    if prefix and not value.startswith(prefix):
        raise GitHubResearchLoveExternallyManagedComponentBindingError(
            f"{name} doit commencer par {prefix}"
        )


def _unique_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        _typed_ref("evidence_ref", value)
        if value not in result:
            result.append(value)
    return tuple(result)


__all__ = (
    "DURABLE_PORT_FACTORY_ENV",
    "EXTERNALLY_MANAGED_DURABLE_PORTS_SCHEMA",
    "GitHubResearchLoveExternallyManagedComponentBindingError",
    "GitHubResearchLoveExternallyManagedDurablePorts",
    "build_github_research_love_externally_managed_installed_components",
)
