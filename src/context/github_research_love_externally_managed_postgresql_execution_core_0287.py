"""Build the durable Scheduler execution core on one shared PostgreSQL port.

The installed foundation already owns the PostgreSQL connection, the canonical
Scheduler, the launch transaction and the handler-completion transaction.  This
module reuses those exact objects.  It builds the durable continuation store on
the shared adapter port and exposes a ready-task step-runner builder that cannot
replace the installed SQL transactions.

No backend, Scheduler, Dispatcher, EventBus, thread, process, JSON store or
JSONL queue is created here.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from importlib import import_module
import inspect
import os
from types import MappingProxyType

from context.love_externally_managed_installed_backend_foundation_0287 import (
    LoveExternallyManagedInstalledBackendFoundation,
)
from context.love_postgresql_shared_adapter_port_0287 import (
    LovePostgreSqlSharedAdapterPort,
)

POSTGRESQL_EXECUTION_CORE_SCHEMA = (
    "missipy.github.research_love_postgresql_execution_core.v1"
)
CONTINUATION_STORE_FACTORY_ENV = (
    "AUTODOC_GITHUB_RESEARCH_POSTGRESQL_CONTINUATION_STORE_FACTORY"
)
TRANSACTIONAL_STEP_RUNNER_FACTORY_ENV = (
    "AUTODOC_GITHUB_RESEARCH_TRANSACTIONAL_STEP_RUNNER_FACTORY"
)


class GitHubResearchLovePostgreSqlExecutionCoreError(RuntimeError):
    """Raised when the shared PostgreSQL execution core cannot fail closed."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLovePostgreSqlExecutionCore:
    """Continuation and step runner bound to the installed SQL transactions."""

    schema: str
    adapter_port: LovePostgreSqlSharedAdapterPort = field(
        repr=False,
        compare=False,
    )
    continuation_store: object = field(repr=False, compare=False)
    step_runner_builder: Callable[..., object] = field(
        repr=False,
        compare=False,
    )
    task_launch_transaction: object = field(repr=False, compare=False)
    handler_execution_transaction: object = field(
        repr=False,
        compare=False,
    )
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != POSTGRESQL_EXECUTION_CORE_SCHEMA:
            raise GitHubResearchLovePostgreSqlExecutionCoreError(
                "schéma du noyau d'exécution PostgreSQL non pris en charge"
            )
        if not isinstance(self.adapter_port, LovePostgreSqlSharedAdapterPort):
            raise TypeError(
                "adapter_port doit être le port PostgreSQL partagé"
            )
        _methods(
            self.continuation_store,
            ("load_snapshot", "commit_promotion"),
        )
        if not callable(self.step_runner_builder):
            raise TypeError("step_runner_builder doit être callable")
        _methods(self.task_launch_transaction, ("commit_launch",))
        _methods(self.handler_execution_transaction, ("commit_outcome",))
        if not self.evidence_refs:
            raise GitHubResearchLovePostgreSqlExecutionCoreError(
                "le noyau d'exécution PostgreSQL doit exposer une preuve"
            )
        for value in self.evidence_refs:
            _typed_ref("evidence_ref", value)

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "evidence_refs": self.evidence_refs,
                "postgresql_connection_reused": True,
                "task_launch_transaction_reused": True,
                "handler_execution_transaction_reused": True,
                "scheduler_created": False,
                "new_backend_opened": False,
                "raw_connection_exposed": False,
                "internal_json_storage_created": False,
                "jsonl_queue_created": False,
            }
        )


def build_github_research_love_postgresql_execution_core(
    *,
    foundation: LoveExternallyManagedInstalledBackendFoundation,
    environment: Mapping[str, str] | None = None,
) -> GitHubResearchLovePostgreSqlExecutionCore:
    """Build continuation and step execution on the already-owned SQL port."""

    if not isinstance(
        foundation,
        LoveExternallyManagedInstalledBackendFoundation,
    ):
        raise TypeError(
            "foundation doit être LoveExternallyManagedInstalledBackendFoundation"
        )

    adapter_port = foundation.postgresql_adapter_port
    if not isinstance(adapter_port, LovePostgreSqlSharedAdapterPort):
        raise TypeError(
            "foundation.postgresql_adapter_port doit être le port partagé"
        )
    _methods(foundation.task_launch_transaction, ("commit_launch",))
    _methods(foundation.handler_execution_transaction, ("commit_outcome",))

    env = os.environ if environment is None else environment
    continuation_factory = _load_required_factory(
        env,
        CONTINUATION_STORE_FACTORY_ENV,
    )
    step_runner_factory = _load_required_factory(
        env,
        TRANSACTIONAL_STEP_RUNNER_FACTORY_ENV,
    )

    continuation_store = adapter_port.build_adapter(
        continuation_factory,
        required_methods=("load_snapshot", "commit_promotion"),
        required_connection_methods=("cursor", "commit", "rollback"),
        initialize_schema=True,
        keyword_arguments={
            "scheduler_ref": foundation.scheduler_ref,
            "authority_store": foundation.authority_store,
            "command_store": foundation.command_store,
            "task_launch_transaction": foundation.task_launch_transaction,
            "handler_execution_transaction": (
                foundation.handler_execution_transaction
            ),
        },
    )

    step_runner_builder = _build_bound_step_runner_builder(
        foundation=foundation,
        adapter_port=adapter_port,
        continuation_store=continuation_store,
        factory=step_runner_factory,
    )

    return GitHubResearchLovePostgreSqlExecutionCore(
        schema=POSTGRESQL_EXECUTION_CORE_SCHEMA,
        adapter_port=adapter_port,
        continuation_store=continuation_store,
        step_runner_builder=step_runner_builder,
        task_launch_transaction=foundation.task_launch_transaction,
        handler_execution_transaction=foundation.handler_execution_transaction,
        evidence_refs=(
            "evidence:github-research-love-postgresql-execution-core-r16-r64",
            "evidence:shared-postgresql-continuation-and-step-runner",
        ),
    )


def _build_bound_step_runner_builder(
    *,
    foundation: LoveExternallyManagedInstalledBackendFoundation,
    adapter_port: LovePostgreSqlSharedAdapterPort,
    continuation_store: object,
    factory: Callable[..., object],
) -> Callable[..., object]:
    """Return a builder whose installed authority objects cannot be replaced."""

    def build_step_runner(**runtime_components: object) -> object:
        available = dict(runtime_components)
        available.update(
            {
                "foundation": foundation,
                "scheduler": foundation.scheduler,
                "dispatcher": foundation.dispatcher,
                "scheduler_ref": foundation.scheduler_ref,
                "authority_store": foundation.authority_store,
                "postgresql_adapter_port": adapter_port,
                "command_store": foundation.command_store,
                "continuation_store": continuation_store,
                "task_launch_transaction": (
                    foundation.task_launch_transaction
                ),
                "handler_execution_transaction": (
                    foundation.handler_execution_transaction
                ),
                "projection_port": foundation.projection_port,
                "embedder": foundation.embedder,
                "retrieval_executor": foundation.retrieval_executor,
            }
        )
        runner = factory(**_supported_keywords(factory, available))
        _methods(runner, ("run_ready_task",))
        return runner

    return build_step_runner


def _load_required_factory(
    environment: Mapping[str, str],
    variable_name: str,
) -> Callable[..., object]:
    reference = str(environment.get(variable_name, "")).strip()
    if not reference:
        raise GitHubResearchLovePostgreSqlExecutionCoreError(
            f"fabrique absente: définir {variable_name}"
        )
    module_name, separator, function_name = reference.partition(":")
    if not separator or not module_name.strip() or not function_name.strip():
        raise GitHubResearchLovePostgreSqlExecutionCoreError(
            f"{variable_name} doit utiliser module:function"
        )
    try:
        module = import_module(module_name.strip())
    except Exception as exc:
        raise GitHubResearchLovePostgreSqlExecutionCoreError(
            f"impossible d'importer {module_name.strip()}"
        ) from exc
    factory = getattr(module, function_name.strip(), None)
    if not callable(factory):
        raise GitHubResearchLovePostgreSqlExecutionCoreError(
            f"la fabrique configurée par {variable_name} n'est pas callable"
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
        or any(character.isspace() for character in value)
    ):
        raise GitHubResearchLovePostgreSqlExecutionCoreError(
            f"{name} doit être une référence typée"
        )


__all__ = (
    "CONTINUATION_STORE_FACTORY_ENV",
    "POSTGRESQL_EXECUTION_CORE_SCHEMA",
    "TRANSACTIONAL_STEP_RUNNER_FACTORY_ENV",
    "GitHubResearchLovePostgreSqlExecutionCore",
    "GitHubResearchLovePostgreSqlExecutionCoreError",
    "build_github_research_love_postgresql_execution_core",
)
