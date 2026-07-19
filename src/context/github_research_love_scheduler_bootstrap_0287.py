"""Graphe de recherche GitHub et première capacité du laboratoire amour.

Cette unité adapte les contrats existants au catalogue typé du Scheduler. Elle
construit le graphe durable complet d'une recherche, catalogue explicitement la
capacité de préparation de la première visite et réutilise le constructeur de
surface déjà présent dans ``github_research_love_first_visit_dispatch_0287``.

Le handler ne soumet aucune visite, n'appelle aucun spécialiste et ne crée ni
Scheduler, ni Dispatcher, ni EventBus. Les tâches suivantes restent décrites
mais sans handler catalogué jusqu'aux unités métier correspondantes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import re
from types import MappingProxyType
from typing import Any, Protocol

from context.github_research_love_first_visit_dispatch_0287 import (
    GitHubResearchLoveFirstVisitSurface,
    build_first_love_visit_surface_from_github_research,
)
from context.github_research_scheduler_command_0287 import (
    GitHubResearchSchedulerCommand,
)
from kernel.scheduler_handler_catalog import SchedulerHandlerCatalog
from kernel.scheduler_handler_contract import (
    HandlerExecutionPolicy,
    HandlerIdempotencyKind,
    HandlerInformation,
    SchedulerHandler,
)
from kernel.scheduler_handler_instance_lifecycle import (
    ExplicitSchedulerHandlerFactory,
    SchedulerHandlerExecutionContext,
    SchedulerHandlerFactory,
)
from kernel.scheduler_task_graph import SchedulerTaskGraph
from kernel.scheduler_task_model import (
    SchedulerTask,
    SchedulerTaskDependency,
    SchedulerTaskDependencyKind,
)

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_CAPABILITY_REF = (
    "capability:github-research.love.prepare-first-visit.v1"
)
GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_HANDLER_REF = (
    "handler:github-research-love-prepare-first-visit-v1"
)
GITHUB_RESEARCH_LOVE_GRAPH_SCHEMA = "missipy.github.research_love_task_graph.v1"
GITHUB_RESEARCH_LOVE_PREPARED_VISIT_SCHEMA = (
    "missipy.github.research_love_prepared_first_visit.v1"
)


class GitHubResearchLoveSchedulerBootstrapError(ValueError):
    """Erreur de contrat du graphe ou du bootstrap du laboratoire amour."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveStageSpec:
    """Description statique d'une étape du graphe, sans exécution implicite."""

    stage: str
    task_kind_ref: str
    capability_ref: str
    max_attempts: int

    def __post_init__(self) -> None:
        if not isinstance(self.stage, str) or not self.stage:
            raise GitHubResearchLoveSchedulerBootstrapError("stage vide")
        if not self.task_kind_ref.startswith("task-kind:"):
            raise GitHubResearchLoveSchedulerBootstrapError(
                "task_kind_ref doit commencer par task-kind:"
            )
        if not self.capability_ref.startswith("capability:"):
            raise GitHubResearchLoveSchedulerBootstrapError(
                "capability_ref doit commencer par capability:"
            )
        if isinstance(self.max_attempts, bool) or self.max_attempts <= 0:
            raise GitHubResearchLoveSchedulerBootstrapError(
                "max_attempts doit être strictement positif"
            )


GITHUB_RESEARCH_LOVE_STAGE_SPECS = (
    GitHubResearchLoveStageSpec(
        "prepare-first-visit",
        "task-kind:github-research-love-prepare-first-visit",
        GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_CAPABILITY_REF,
        2,
    ),
    GitHubResearchLoveStageSpec(
        "execute-first-specialist",
        "task-kind:github-research-love-execute-first-specialist",
        "capability:github-research.love.execute-first-specialist.v1",
        2,
    ),
    GitHubResearchLoveStageSpec(
        "persist-first-analysis",
        "task-kind:github-research-love-persist-first-analysis",
        "capability:github-research.love.persist-first-analysis.v1",
        3,
    ),
    GitHubResearchLoveStageSpec(
        "project-first-analysis",
        "task-kind:github-research-love-project-first-analysis",
        "capability:github-research.love.project-first-analysis.v1",
        3,
    ),
    GitHubResearchLoveStageSpec(
        "prepare-second-visit",
        "task-kind:github-research-love-prepare-second-visit",
        "capability:github-research.love.prepare-second-visit.v1",
        2,
    ),
    GitHubResearchLoveStageSpec(
        "execute-second-specialist",
        "task-kind:github-research-love-execute-second-specialist",
        "capability:github-research.love.execute-second-specialist.v1",
        2,
    ),
    GitHubResearchLoveStageSpec(
        "persist-second-analysis",
        "task-kind:github-research-love-persist-second-analysis",
        "capability:github-research.love.persist-second-analysis.v1",
        3,
    ),
    GitHubResearchLoveStageSpec(
        "project-second-analysis",
        "task-kind:github-research-love-project-second-analysis",
        "capability:github-research.love.project-second-analysis.v1",
        3,
    ),
    GitHubResearchLoveStageSpec(
        "recall-two-analyses",
        "task-kind:github-research-love-recall-two-analyses",
        "capability:github-research.love.recall-two-analyses.v1",
        2,
    ),
    GitHubResearchLoveStageSpec(
        "synthesize-liaison",
        "task-kind:github-research-love-synthesize-liaison",
        "capability:github-research.love.synthesize-liaison.v1",
        2,
    ),
    GitHubResearchLoveStageSpec(
        "build-final-deliverable",
        "task-kind:github-research-love-build-final-deliverable",
        "capability:github-research.love.build-final-deliverable.v1",
        2,
    ),
    GitHubResearchLoveStageSpec(
        "prepare-publication",
        "task-kind:github-research-love-prepare-publication",
        "capability:github-research.love.prepare-publication.v1",
        2,
    ),
    GitHubResearchLoveStageSpec(
        "publish-remote",
        "task-kind:github-research-love-publish-remote",
        "capability:github-research.love.publish-remote.v1",
        2,
    ),
    GitHubResearchLoveStageSpec(
        "close-cycle",
        "task-kind:github-research-love-close-cycle",
        "capability:github-research.love.close-cycle.v1",
        3,
    ),
)


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveTaskGraphBuild:
    """Graphe complet et index typé des étapes d'une commande unique."""

    schema: str
    graph: SchedulerTaskGraph
    stage_task_refs: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.schema != GITHUB_RESEARCH_LOVE_GRAPH_SCHEMA:
            raise GitHubResearchLoveSchedulerBootstrapError(
                "schéma de graphe de recherche amour non pris en charge"
            )
        copied = dict(self.stage_task_refs)
        expected_stages = tuple(spec.stage for spec in GITHUB_RESEARCH_LOVE_STAGE_SPECS)
        if tuple(copied) != expected_stages:
            raise GitHubResearchLoveSchedulerBootstrapError(
                "stage_task_refs diverge des étapes canoniques"
            )
        if tuple(copied.values()) != tuple(task.task_ref for task in self.graph.tasks):
            raise GitHubResearchLoveSchedulerBootstrapError(
                "stage_task_refs diverge des tâches du graphe"
            )
        object.__setattr__(self, "stage_task_refs", MappingProxyType(copied))

    @property
    def first_task_ref(self) -> str:
        return self.stage_task_refs["prepare-first-visit"]


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFirstVisitInput:
    """Entrées existantes nécessaires au constructeur de surface de visite."""

    runtime_ports: object = field(repr=False, compare=False)
    work_package: Mapping[str, Any]
    scheduler_intake: Mapping[str, Any]
    scheduler_dispatch: Mapping[str, Any]

    def __post_init__(self) -> None:
        for name in ("work_package", "scheduler_intake", "scheduler_dispatch"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise TypeError(f"{name} doit être un mapping")
            object.__setattr__(self, name, MappingProxyType(dict(value)))


class GitHubResearchLoveFirstVisitInputProvider(Protocol):
    """Port injecté qui réhydrate les entrées depuis l'autorité locale."""

    def load(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
    ) -> GitHubResearchLoveFirstVisitInput: ...


@dataclass(frozen=True, slots=True)
class GitHubResearchLovePreparedFirstVisit:
    """Surface de visite construite, mais pas encore soumise au laboratoire."""

    schema: str
    command_ref: str
    scheduler_task_ref: str
    work_package_ref: str
    study_ref: str
    specialist_task_ref: str
    visit_ref: str
    prepared_at: str
    surface: GitHubResearchLoveFirstVisitSurface = field(repr=False, compare=False)
    result_digest: str

    def __post_init__(self) -> None:
        if self.schema != GITHUB_RESEARCH_LOVE_PREPARED_VISIT_SCHEMA:
            raise GitHubResearchLoveSchedulerBootstrapError(
                "schéma de première visite préparée non pris en charge"
            )
        _require_typed_ref("command_ref", self.command_ref, "scheduler-command:")
        _require_typed_ref("scheduler_task_ref", self.scheduler_task_ref, "scheduler-task:")
        _require_typed_ref("work_package_ref", self.work_package_ref)
        _require_typed_ref("study_ref", self.study_ref, "love-study:")
        _require_typed_ref("specialist_task_ref", self.specialist_task_ref, "specialist-task:")
        _require_typed_ref("visit_ref", self.visit_ref, "laboratory-visit:")
        _require_utc("prepared_at", self.prepared_at)
        if self.surface.study.study_ref != self.study_ref:
            raise GitHubResearchLoveSchedulerBootstrapError("study_ref divergent")
        if self.surface.first_task.task_ref != self.specialist_task_ref:
            raise GitHubResearchLoveSchedulerBootstrapError(
                "specialist_task_ref divergent"
            )
        if self.surface.first_visit.visit_ref != self.visit_ref:
            raise GitHubResearchLoveSchedulerBootstrapError("visit_ref divergent")
        _require_sha256("result_digest", self.result_digest)
        expected = _prepared_visit_digest(
            command_ref=self.command_ref,
            scheduler_task_ref=self.scheduler_task_ref,
            work_package_ref=self.work_package_ref,
            study_ref=self.study_ref,
            specialist_task_ref=self.specialist_task_ref,
            visit_ref=self.visit_ref,
            prepared_at=self.prepared_at,
        )
        if self.result_digest != expected:
            raise GitHubResearchLoveSchedulerBootstrapError(
                "result_digest de visite incohérent"
            )


class GitHubResearchLovePrepareFirstVisitHandler(
    SchedulerHandler[
        GitHubResearchSchedulerCommand,
        GitHubResearchLovePreparedFirstVisit,
    ]
):
    """Prépare la première visite à partir des contrats existants, sans la lancer."""

    HANDLER_REF = GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_HANDLER_REF
    CAPABILITY_REF = GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_CAPABILITY_REF
    COMMAND_TYPE = GitHubResearchSchedulerCommand
    RESULT_TYPE = GitHubResearchLovePreparedFirstVisit
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.IDEMPOTENT,
        timeout_policy_ref="timeout-policy:github-research-love-prepare-first-visit-v1",
        retry_policy_ref="retry-policy:github-research-love-prepare-first-visit-v1",
        resource_profile_ref="resource-profile:love-first-visit-preparation-v1",
        laboratory_compatibility=("laboratory-kind:love-studies",),
    )
    INFORMATION = HandlerInformation(
        title="Préparation de la première visite du laboratoire amour",
        summary=(
            "Réhydrate les entrées locales et construit la surface typée de visite "
            "sans soumettre le spécialiste."
        ),
        created_text="Le préparateur de première visite existe pour {command_ref}.",
        started_text="Préparation de la première visite pour {command_ref}.",
        succeeded_text="Première visite préparée pour {command_ref} en {elapsed_ms} ms.",
        failed_text="Échec de préparation de la première visite: {error_type}.",
        cancelled_text="Préparation de première visite annulée pour {command_ref}.",
        closed_text="Préparateur de première visite fermé.",
    )

    def __init__(self, input_provider: GitHubResearchLoveFirstVisitInputProvider) -> None:
        if not callable(getattr(input_provider, "load", None)):
            raise TypeError("input_provider doit exposer load")
        self._input_provider = input_provider

    async def execute(
        self,
        command: GitHubResearchSchedulerCommand,
        context: object,
    ) -> GitHubResearchLovePreparedFirstVisit:
        if not isinstance(command, GitHubResearchSchedulerCommand):
            raise TypeError("command doit être GitHubResearchSchedulerCommand")
        if not isinstance(context, SchedulerHandlerExecutionContext):
            raise TypeError("context doit être SchedulerHandlerExecutionContext")
        if context.command_ref != command.command_ref:
            raise GitHubResearchLoveSchedulerBootstrapError(
                "le contexte d'exécution appartient à une autre commande"
            )
        expected_task_ref = _stage_task_ref(command.command_ref, "prepare-first-visit")
        if context.task_ref != expected_task_ref:
            raise GitHubResearchLoveSchedulerBootstrapError(
                "le handler de première visite a reçu une autre tâche"
            )
        inputs = self._input_provider.load(
            command=command,
            execution_context=context,
        )
        if not isinstance(inputs, GitHubResearchLoveFirstVisitInput):
            raise TypeError("input_provider.load doit retourner GitHubResearchLoveFirstVisitInput")
        _validate_first_visit_input(command, inputs)
        surface = build_first_love_visit_surface_from_github_research(
            runtime_ports=inputs.runtime_ports,
            work_package=inputs.work_package,
            scheduler_intake=inputs.scheduler_intake,
            scheduler_dispatch=inputs.scheduler_dispatch,
        )
        digest = _prepared_visit_digest(
            command_ref=command.command_ref,
            scheduler_task_ref=context.task_ref,
            work_package_ref=command.research.work_package_ref,
            study_ref=surface.study.study_ref,
            specialist_task_ref=surface.first_task.task_ref,
            visit_ref=surface.first_visit.visit_ref,
            prepared_at=context.started_at,
        )
        return GitHubResearchLovePreparedFirstVisit(
            schema=GITHUB_RESEARCH_LOVE_PREPARED_VISIT_SCHEMA,
            command_ref=command.command_ref,
            scheduler_task_ref=context.task_ref,
            work_package_ref=command.research.work_package_ref,
            study_ref=surface.study.study_ref,
            specialist_task_ref=surface.first_task.task_ref,
            visit_ref=surface.first_visit.visit_ref,
            prepared_at=context.started_at,
            surface=surface,
            result_digest=digest,
        )


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveSchedulerBootstrap:
    """Catalogue et fabrique explicitement assemblés au bootstrap serveur."""

    catalog: SchedulerHandlerCatalog
    factory: SchedulerHandlerFactory = field(repr=False, compare=False)
    handler_refs: tuple[str, ...]
    capability_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        bindings = self.catalog.snapshot()
        if tuple(binding.handler_ref for binding in bindings) != self.handler_refs:
            raise GitHubResearchLoveSchedulerBootstrapError(
                "handler_refs diverge du catalogue"
            )
        if tuple(binding.key.capability_ref for binding in bindings) != self.capability_refs:
            raise GitHubResearchLoveSchedulerBootstrapError(
                "capability_refs diverge du catalogue"
            )


def build_github_research_love_task_graph(
    command: GitHubResearchSchedulerCommand,
    *,
    created_at: str,
) -> GitHubResearchLoveTaskGraphBuild:
    """Construit le graphe linéaire complet d'une recherche GitHub autorisée."""

    if not isinstance(command, GitHubResearchSchedulerCommand):
        raise TypeError("command doit être GitHubResearchSchedulerCommand")
    _require_utc("created_at", created_at)
    if command.execution_budget.max_scheduler_steps < len(
        GITHUB_RESEARCH_LOVE_STAGE_SPECS
    ):
        raise GitHubResearchLoveSchedulerBootstrapError(
            "max_scheduler_steps est inférieur au nombre d'étapes du graphe"
        )
    if command.execution_budget.max_specialist_visits < 2:
        raise GitHubResearchLoveSchedulerBootstrapError(
            "la recherche amour exige deux visites de spécialistes"
        )

    refs = {
        spec.stage: _stage_task_ref(command.command_ref, spec.stage)
        for spec in GITHUB_RESEARCH_LOVE_STAGE_SPECS
    }
    context_refs = _unique_refs(
        (
            *command.research.context_refs,
            command.correlation.conversation_ref,
            command.correlation.return_route_ref,
            command.research.work_package_ref,
            command.research.route_candidate_ref,
        )
    )
    evidence_refs = tuple(command.research.evidence_refs)
    tasks: list[SchedulerTask] = []
    previous_ref = ""
    for index, spec in enumerate(GITHUB_RESEARCH_LOVE_STAGE_SPECS):
        dependencies = (
            (
                SchedulerTaskDependency(
                    task_ref=previous_ref,
                    kind=SchedulerTaskDependencyKind.SUCCEEDED,
                ),
            )
            if previous_ref
            else ()
        )
        task = SchedulerTask.plan(
            task_ref=refs[spec.stage],
            command_ref=command.command_ref,
            task_kind_ref=spec.task_kind_ref,
            capability_ref=spec.capability_ref,
            contract_version=1,
            priority=max(0, min(100, command.priority - index // 3)),
            max_attempts=spec.max_attempts,
            created_at=created_at,
            parent_task_ref=previous_ref,
            dependencies=dependencies,
            context_refs=context_refs,
            evidence_refs=evidence_refs,
        )
        tasks.append(task)
        previous_ref = task.task_ref

    graph = SchedulerTaskGraph.create(
        graph_ref=_graph_ref(command.command_ref),
        command_ref=command.command_ref,
        created_at=created_at,
        tasks=tasks,
    )
    return GitHubResearchLoveTaskGraphBuild(
        schema=GITHUB_RESEARCH_LOVE_GRAPH_SCHEMA,
        graph=graph,
        stage_task_refs=refs,
    )


def build_github_research_love_scheduler_bootstrap(
    input_provider: GitHubResearchLoveFirstVisitInputProvider,
) -> GitHubResearchLoveSchedulerBootstrap:
    """Assemble explicitement le premier handler et sa fabrique injectée."""

    if not callable(getattr(input_provider, "load", None)):
        raise TypeError("input_provider doit exposer load")
    catalog = SchedulerHandlerCatalog((GitHubResearchLovePrepareFirstVisitHandler,))
    factory = ExplicitSchedulerHandlerFactory(
        {
            GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_HANDLER_REF: (
                lambda _binding, _ticket: GitHubResearchLovePrepareFirstVisitHandler(
                    input_provider
                )
            )
        }
    )
    return GitHubResearchLoveSchedulerBootstrap(
        catalog=catalog,
        factory=factory,
        handler_refs=(GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_HANDLER_REF,),
        capability_refs=(GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_CAPABILITY_REF,),
    )


def _validate_first_visit_input(
    command: GitHubResearchSchedulerCommand,
    inputs: GitHubResearchLoveFirstVisitInput,
) -> None:
    expected = {
        "repository": command.correlation.repository,
        "run_id": command.correlation.run_id,
        "work_package_ref": command.research.work_package_ref,
        "context_generation": command.research.context_generation,
    }
    for name, value in expected.items():
        if inputs.work_package.get(name) != value:
            raise GitHubResearchLoveSchedulerBootstrapError(
                f"work_package.{name} diverge de la commande"
            )
    issue = inputs.work_package.get("source_issue")
    if not isinstance(issue, Mapping) or issue.get("number") != command.correlation.issue_number:
        raise GitHubResearchLoveSchedulerBootstrapError(
            "work_package.source_issue.number diverge de la commande"
        )


def _stage_task_ref(command_ref: str, stage: str) -> str:
    suffix = hashlib.sha256(command_ref.encode("utf-8")).hexdigest()[:20]
    return f"scheduler-task:github-love-{stage}-{suffix}"


def _graph_ref(command_ref: str) -> str:
    suffix = hashlib.sha256(command_ref.encode("utf-8")).hexdigest()[:24]
    return f"scheduler-task-graph:github-love-{suffix}"


def _prepared_visit_digest(
    *,
    command_ref: str,
    scheduler_task_ref: str,
    work_package_ref: str,
    study_ref: str,
    specialist_task_ref: str,
    visit_ref: str,
    prepared_at: str,
) -> str:
    digest = hashlib.sha256()
    for name, value in (
        ("command_ref", command_ref),
        ("scheduler_task_ref", scheduler_task_ref),
        ("work_package_ref", work_package_ref),
        ("study_ref", study_ref),
        ("specialist_task_ref", specialist_task_ref),
        ("visit_ref", visit_ref),
        ("prepared_at", prepared_at),
    ):
        key = name.encode("utf-8")
        encoded = str(value).encode("utf-8")
        digest.update(len(key).to_bytes(4, "big"))
        digest.update(key)
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return "sha256:" + digest.hexdigest()


def _unique_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    result = tuple(dict.fromkeys(values))
    for value in result:
        _require_typed_ref("context_ref", value)
    return result


def _require_typed_ref(name: str, value: object, prefix: str = "") -> None:
    if not isinstance(value, str) or _TYPED_REF_RE.fullmatch(value) is None:
        raise GitHubResearchLoveSchedulerBootstrapError(
            f"{name} doit être une référence typée"
        )
    if prefix and not value.startswith(prefix):
        raise GitHubResearchLoveSchedulerBootstrapError(
            f"{name} doit commencer par {prefix}"
        )


def _require_utc(name: str, value: object) -> None:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        raise GitHubResearchLoveSchedulerBootstrapError(
            f"{name} doit être un horodatage UTC finissant par Z"
        )


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise GitHubResearchLoveSchedulerBootstrapError(
            f"{name} doit être un SHA-256 préfixé"
        )


__all__ = (
    "GITHUB_RESEARCH_LOVE_GRAPH_SCHEMA",
    "GITHUB_RESEARCH_LOVE_PREPARED_VISIT_SCHEMA",
    "GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_CAPABILITY_REF",
    "GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_HANDLER_REF",
    "GITHUB_RESEARCH_LOVE_STAGE_SPECS",
    "GitHubResearchLoveFirstVisitInput",
    "GitHubResearchLoveFirstVisitInputProvider",
    "GitHubResearchLovePrepareFirstVisitHandler",
    "GitHubResearchLovePreparedFirstVisit",
    "GitHubResearchLoveSchedulerBootstrap",
    "GitHubResearchLoveSchedulerBootstrapError",
    "GitHubResearchLoveStageSpec",
    "GitHubResearchLoveTaskGraphBuild",
    "build_github_research_love_scheduler_bootstrap",
    "build_github_research_love_task_graph",
)
