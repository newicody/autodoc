"""Assemble the installed externally-managed GitHub research runtime.

This module is a composition boundary.  It receives one already-built
process-local component bundle, assembles the existing ten Scheduler handlers,
the durable bounded cycle and the OpenRC service owner, then returns the r57
service bundle.

It does not create a second Scheduler, a parallel dispatcher, an internal JSON
store or a JSONL queue.  PostgreSQL remains the durable authority; Qdrant and
OpenVINO remain injected projection/recall components; OpenRC owns only the
process lifecycle.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib import import_module
import inspect
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any

from context.github_research_love_externally_managed_runtime_0287 import (
    BufferedPersistentHandlerInformationSink,
    GitHubResearchLoveExternallyManagedRuntime,
    SchedulerTemporalObservationStore,
)
from context.github_research_love_grouped_publication_closure_0287 import (
    GitHubResearchLoveGroupedPublicationInputProvider,
    build_github_research_love_full_grouped_scheduler_bootstrap,
)
from context.github_research_love_grouped_recall_synthesis_deliverable_0287 import (
    GitHubResearchLoveGroupedDownstreamInputProvider,
)
from context.github_research_love_grouped_specialist_pipeline_0287 import (
    GitHubResearchLoveGroupedInputProvider,
)
from context.github_research_love_openrc_scheduler_service_0287 import (
    OPENRC_SCHEDULER_SERVICE_BUNDLE_SCHEMA,
    CanonicalSchedulerProcess,
    GitHubResearchLoveOpenRcSchedulerService,
    GitHubResearchLoveOpenRcServiceBundle,
    OpenRcSchedulerServiceSettings,
)
from context.github_research_love_scheduler_bootstrap_0287 import (
    GitHubResearchLoveFirstVisitInputProvider,
)
from context.github_research_scheduler_command_claim_0287 import (
    SchedulerCommandClaimStore,
)
from context.love_installed_runtime_factory_0287 import (
    InstalledRuntimeFactorySettings,
    load_installed_runtime_factory_settings,
)
from kernel.scheduler_canonical_continuation import (
    SchedulerCanonicalBoundedCycle,
    SchedulerDurableContinuationStore,
    SchedulerReadyTaskStepRunner,
)

EXTERNALLY_MANAGED_INSTALLED_COMPOSITION_SCHEMA = (
    "missipy.github.research_love_externally_managed_installed_composition.v1"
)
EXTERNALLY_MANAGED_COMPONENTS_SCHEMA = (
    "missipy.github.research_love_externally_managed_installed_components.v1"
)
COMPONENT_FACTORY_ENV = (
    "AUTODOC_GITHUB_RESEARCH_EXTERNALLY_MANAGED_COMPONENT_FACTORY"
)
SERVICE_REF_ENV = "AUTODOC_GITHUB_RESEARCH_SERVICE_REF"
ACTOR_REF_ENV = "AUTODOC_GITHUB_RESEARCH_SERVICE_ACTOR_REF"
CAUSE_REF_ENV = "AUTODOC_GITHUB_RESEARCH_SERVICE_CAUSE_REF"
POLL_INTERVAL_ENV = "AUTODOC_GITHUB_RESEARCH_POLL_INTERVAL_SECONDS"
MAX_TASK_STEPS_ENV = "AUTODOC_GITHUB_RESEARCH_MAX_TASK_STEPS"
STARTUP_YIELD_LIMIT_ENV = "AUTODOC_GITHUB_RESEARCH_STARTUP_YIELD_LIMIT"


class GitHubResearchLoveExternallyManagedInstalledCompositionError(RuntimeError):
    """Raised when the installed long-lived composition cannot fail closed."""


StepRunnerBuilder = Callable[..., SchedulerReadyTaskStepRunner]
CloseCallback = Callable[[], object | Awaitable[object]]


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveExternallyManagedInstalledComponents:
    """One process-local component set supplied by the installed server binding."""

    schema: str
    scheduler: CanonicalSchedulerProcess = field(repr=False, compare=False)
    scheduler_ref: str
    command_store: SchedulerCommandClaimStore = field(repr=False, compare=False)
    continuation_store: SchedulerDurableContinuationStore = field(
        repr=False,
        compare=False,
    )
    step_runner_builder: StepRunnerBuilder = field(repr=False, compare=False)
    first_visit_input_provider: GitHubResearchLoveFirstVisitInputProvider = field(
        repr=False,
        compare=False,
    )
    grouped_input_provider: GitHubResearchLoveGroupedInputProvider = field(
        repr=False,
        compare=False,
    )
    downstream_input_provider: GitHubResearchLoveGroupedDownstreamInputProvider = field(
        repr=False,
        compare=False,
    )
    publication_input_provider: GitHubResearchLoveGroupedPublicationInputProvider = field(
        repr=False,
        compare=False,
    )
    observation_store: SchedulerTemporalObservationStore = field(
        repr=False,
        compare=False,
    )
    close_callbacks: tuple[CloseCallback, ...] = field(
        default=(),
        repr=False,
        compare=False,
    )
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != EXTERNALLY_MANAGED_COMPONENTS_SCHEMA:
            raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
                "schéma de composants externally-managed non pris en charge"
            )
        if not isinstance(self.scheduler, CanonicalSchedulerProcess):
            raise TypeError("scheduler ne respecte pas CanonicalSchedulerProcess")
        _typed_ref("scheduler_ref", self.scheduler_ref, "scheduler:")
        _method(self.command_store, "claim_next_pending")
        for name in ("load_snapshot", "commit_promotion"):
            _method(self.continuation_store, name)
        if not callable(self.step_runner_builder):
            raise TypeError("step_runner_builder doit être callable")
        _provider_methods(self.first_visit_input_provider, ("load",))
        _provider_methods(
            self.grouped_input_provider,
            (
                "load_first_dispatch_command",
                "load_second_dispatch_command",
                "load_pair_stage_input",
            ),
        )
        _provider_methods(
            self.downstream_input_provider,
            (
                "load_recall_command",
                "load_synthesis_command",
                "load_final_deliverable_command",
            ),
        )
        _provider_methods(
            self.publication_input_provider,
            (
                "load_publication_command",
                "load_publication_authorization",
                "load_cycle_closure_result",
            ),
        )
        for name in ("initialize_schema", "append_many"):
            _method(self.observation_store, name)
        for callback in self.close_callbacks:
            if not callable(callback):
                raise TypeError("chaque close_callback doit être callable")
        if not self.evidence_refs:
            raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
                "les composants doivent exposer au moins une preuve d'installation"
            )
        for value in self.evidence_refs:
            _typed_ref("evidence_ref", value)

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "scheduler_ref": self.scheduler_ref,
                "close_callback_count": len(self.close_callbacks),
                "evidence_refs": self.evidence_refs,
                "postgresql_durable_authority": True,
                "qdrant_projection_and_recall": True,
                "openvino_e5_injected": True,
                "internal_json_storage_created": False,
                "jsonl_queue_created": False,
            }
        )


def compose_github_research_love_externally_managed_service(
    *,
    settings: InstalledRuntimeFactorySettings,
    components: GitHubResearchLoveExternallyManagedInstalledComponents,
    service_settings: OpenRcSchedulerServiceSettings,
    clock: Callable[[], str] | None = None,
) -> GitHubResearchLoveOpenRcServiceBundle:
    """Compose one durable service from one already-built component set."""

    if not isinstance(settings, InstalledRuntimeFactorySettings):
        raise TypeError("settings doit être InstalledRuntimeFactorySettings")
    if settings.scheduler_lifecycle != "externally-managed":
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            "la composition OpenRC exige scheduler lifecycle externally-managed"
        )
    if not isinstance(
        components,
        GitHubResearchLoveExternallyManagedInstalledComponents,
    ):
        raise TypeError(
            "components doit être GitHubResearchLoveExternallyManagedInstalledComponents"
        )
    if components.scheduler_ref != settings.scheduler_ref:
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            "scheduler_ref des composants diverge de la configuration installée"
        )
    if service_settings.scheduler_ref != settings.scheduler_ref:
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            "scheduler_ref du service diverge de la configuration installée"
        )

    runtime_clock = clock or _utc_now
    bootstrap = build_github_research_love_full_grouped_scheduler_bootstrap(
        components.first_visit_input_provider,
        components.grouped_input_provider,
        components.downstream_input_provider,
        components.publication_input_provider,
    )
    if len(bootstrap.handler_refs) != 10 or len(bootstrap.capability_refs) != 10:
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            "le bootstrap installé doit exposer exactement dix handlers"
        )

    components.observation_store.initialize_schema()
    information_sink = BufferedPersistentHandlerInformationSink(
        scheduler_ref=settings.scheduler_ref,
        clock=runtime_clock,
    )
    step_runner = components.step_runner_builder(
        bootstrap=bootstrap,
        information_sink=information_sink,
        scheduler_ref=settings.scheduler_ref,
    )
    _method(step_runner, "run_ready_task")

    cycle = SchedulerCanonicalBoundedCycle(
        store=components.continuation_store,
        step_runner=step_runner,
        clock=runtime_clock,
        running_probe=lambda: bool(components.scheduler.running),
    )
    runtime = GitHubResearchLoveExternallyManagedRuntime(
        scheduler=components.scheduler,
        scheduler_ref=settings.scheduler_ref,
        command_store=components.command_store,
        bootstrap=bootstrap,
        cycle=cycle,
        observation_sink=information_sink,
        observation_store=components.observation_store,
        clock=runtime_clock,
    )
    service = GitHubResearchLoveOpenRcSchedulerService(
        scheduler=components.scheduler,
        runtime=runtime,
        settings=service_settings,
        clock=runtime_clock,
    )
    evidence_refs = _unique_refs(settings.evidence_refs + components.evidence_refs)
    return GitHubResearchLoveOpenRcServiceBundle(
        schema=OPENRC_SCHEDULER_SERVICE_BUNDLE_SCHEMA,
        service=service,
        close_callbacks=components.close_callbacks,
        evidence_refs=evidence_refs,
    )


def build_github_research_love_openrc_service_bundle(
    *,
    config_path: str | os.PathLike[str] | None = None,
    environment: Mapping[str, str] | None = None,
) -> GitHubResearchLoveOpenRcServiceBundle:
    """Installed factory consumed by the r57 OpenRC CLI."""

    env = os.environ if environment is None else environment
    settings = load_installed_runtime_factory_settings(config_path)
    if settings.scheduler_lifecycle != "externally-managed":
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            "[scheduler] lifecycle doit être externally-managed pour OpenRC"
        )
    factory_ref = str(env.get(COMPONENT_FACTORY_ENV, "")).strip()
    if not factory_ref:
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            f"fabrique de composants absente: définir {COMPONENT_FACTORY_ENV}"
        )
    component_factory = _load_factory(factory_ref)
    provided = component_factory(
        **_supported_keywords(
            component_factory,
            {
                "settings": settings,
                "config_path": Path(settings.config_path),
                "environment": env,
            },
        )
    )
    if not isinstance(
        provided,
        GitHubResearchLoveExternallyManagedInstalledComponents,
    ):
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            "la fabrique de composants doit retourner le bundle typé r16-r58"
        )
    return compose_github_research_love_externally_managed_service(
        settings=settings,
        components=provided,
        service_settings=_service_settings(settings, env),
    )


def _service_settings(
    settings: InstalledRuntimeFactorySettings,
    environment: Mapping[str, str],
) -> OpenRcSchedulerServiceSettings:
    return OpenRcSchedulerServiceSettings(
        service_ref=str(
            environment.get(
                SERVICE_REF_ENV,
                "service:autodoc-github-research-scheduler",
            )
        ).strip(),
        scheduler_ref=settings.scheduler_ref,
        actor_ref=str(
            environment.get(
                ACTOR_REF_ENV,
                "actor:openrc-autodoc-scheduler",
            )
        ).strip(),
        cause_ref=str(
            environment.get(
                CAUSE_REF_ENV,
                "cause:openrc-service-tick",
            )
        ).strip(),
        poll_interval_seconds=_float_setting(
            environment,
            POLL_INTERVAL_ENV,
            1.0,
        ),
        max_task_steps=_int_setting(environment, MAX_TASK_STEPS_ENV, 16),
        startup_yield_limit=_int_setting(
            environment,
            STARTUP_YIELD_LIMIT_ENV,
            128,
        ),
    )


def _load_factory(reference: str) -> Callable[..., object]:
    module_name, separator, function_name = reference.partition(":")
    if not separator or not module_name.strip() or not function_name.strip():
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            f"{COMPONENT_FACTORY_ENV} doit utiliser module:function"
        )
    try:
        module = import_module(module_name.strip())
    except Exception as exc:
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            f"impossible d'importer la fabrique de composants {module_name.strip()}"
        ) from exc
    factory = getattr(module, function_name.strip(), None)
    if factory is None or not callable(factory):
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            "la fabrique de composants configurée n'est pas callable"
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


def _provider_methods(value: object, names: tuple[str, ...]) -> None:
    for name in names:
        _method(value, name)


def _method(value: object, name: str) -> None:
    if not callable(getattr(value, name, None)):
        raise TypeError(f"{type(value).__name__} doit exposer {name}")


def _int_setting(
    environment: Mapping[str, str],
    name: str,
    default: int,
) -> int:
    raw = str(environment.get(name, "")).strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            f"{name} doit être un entier"
        ) from exc


def _float_setting(
    environment: Mapping[str, str],
    name: str,
    default: float,
) -> float:
    raw = str(environment.get(name, "")).strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            f"{name} doit être un nombre"
        ) from exc


def _unique_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        _typed_ref("evidence_ref", value)
        if value not in result:
            result.append(value)
    return tuple(result)


def _typed_ref(name: str, value: object, prefix: str = "") -> None:
    if not isinstance(value, str) or ":" not in value or any(ch.isspace() for ch in value):
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            f"{name} doit être une référence typée"
        )
    if prefix and not value.startswith(prefix):
        raise GitHubResearchLoveExternallyManagedInstalledCompositionError(
            f"{name} doit commencer par {prefix}"
        )


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


__all__ = (
    "ACTOR_REF_ENV",
    "CAUSE_REF_ENV",
    "COMPONENT_FACTORY_ENV",
    "EXTERNALLY_MANAGED_COMPONENTS_SCHEMA",
    "EXTERNALLY_MANAGED_INSTALLED_COMPOSITION_SCHEMA",
    "GitHubResearchLoveExternallyManagedInstalledComponents",
    "GitHubResearchLoveExternallyManagedInstalledCompositionError",
    "MAX_TASK_STEPS_ENV",
    "POLL_INTERVAL_ENV",
    "SERVICE_REF_ENV",
    "STARTUP_YIELD_LIMIT_ENV",
    "build_github_research_love_openrc_service_bundle",
    "compose_github_research_love_externally_managed_service",
)
