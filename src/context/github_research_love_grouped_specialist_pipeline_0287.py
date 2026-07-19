"""Pipeline groupé des deux spécialistes du laboratoire amour.

Cette unité adapte les opérations métier déjà présentes à des handlers du
Scheduler. Elle ne recrée ni laboratoire, ni Scheduler, ni connexion SQL, ni
client Qdrant, ni moteur OpenVINO. Le graphe v2 regroupe la persistance et les
deux projections dans une seule tâche Scheduler, tout en conservant deux
objets SQL et deux points Qdrant distincts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Any, Protocol

from context.github_research_love_first_visit_dispatch_0287 import (
    GitHubResearchLoveFirstVisitDispatchCommand,
    GitHubResearchLoveFirstVisitDispatchResult,
    dispatch_first_love_visit_from_github_research,
)
from context.github_research_love_scheduler_bootstrap_0287 import (
    GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_CAPABILITY_REF,
    GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_HANDLER_REF,
    GitHubResearchLoveFirstVisitInputProvider,
    GitHubResearchLovePrepareFirstVisitHandler,
)
from context.github_research_love_second_visit_dispatch_0287 import (
    GitHubResearchLoveSecondVisitDispatchCommand,
    GitHubResearchLoveSecondVisitDispatchResult,
    dispatch_second_love_visit_from_first_analysis,
)
from context.github_research_love_sql_persistence_0287 import (
    GitHubResearchLoveSqlPersistenceResult,
    persist_github_research_love_analyses,
)
from context.github_research_love_two_qdrant_projections_0287 import (
    GitHubResearchLoveTwoProjectionCommand,
    GitHubResearchLoveTwoProjectionResult,
    ReferencePointReader,
    project_github_research_love_analyses,
)
from context.github_research_scheduler_command_0287 import (
    GitHubResearchSchedulerCommand,
)
from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimePorts,
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

GROUPED_GRAPH_SCHEMA = "missipy.github.research_love_grouped_task_graph.v2"
PAIR_RESULT_SCHEMA = "missipy.github.research_love_persisted_projected_pair.v1"

EXECUTE_FIRST_CAPABILITY_REF = (
    "capability:github-research.love.execute-first-specialist.v1"
)
EXECUTE_SECOND_CAPABILITY_REF = (
    "capability:github-research.love.execute-second-specialist.v1"
)
PERSIST_PROJECT_PAIR_CAPABILITY_REF = (
    "capability:github-research.love.persist-project-two-analyses.v1"
)

EXECUTE_FIRST_HANDLER_REF = (
    "handler:github-research-love-execute-first-specialist-v1"
)
EXECUTE_SECOND_HANDLER_REF = (
    "handler:github-research-love-execute-second-specialist-v1"
)
PERSIST_PROJECT_PAIR_HANDLER_REF = (
    "handler:github-research-love-persist-project-two-analyses-v1"
)


class GitHubResearchLoveGroupedPipelineError(RuntimeError):
    """Erreur de contrat ou d'exécution du pipeline groupé."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveGroupedStageSpec:
    stage: str
    task_kind_ref: str
    capability_ref: str
    max_attempts: int

    def __post_init__(self) -> None:
        if not self.stage:
            raise GitHubResearchLoveGroupedPipelineError("stage vide")
        if not self.task_kind_ref.startswith("task-kind:"):
            raise GitHubResearchLoveGroupedPipelineError(
                "task_kind_ref doit commencer par task-kind:"
            )
        if not self.capability_ref.startswith("capability:"):
            raise GitHubResearchLoveGroupedPipelineError(
                "capability_ref doit commencer par capability:"
            )
        if isinstance(self.max_attempts, bool) or self.max_attempts <= 0:
            raise GitHubResearchLoveGroupedPipelineError(
                "max_attempts doit être strictement positif"
            )


GROUPED_STAGE_SPECS = (
    GitHubResearchLoveGroupedStageSpec(
        "prepare-first-visit",
        "task-kind:github-research-love-prepare-first-visit",
        GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_CAPABILITY_REF,
        2,
    ),
    GitHubResearchLoveGroupedStageSpec(
        "execute-first-specialist",
        "task-kind:github-research-love-execute-first-specialist",
        EXECUTE_FIRST_CAPABILITY_REF,
        2,
    ),
    GitHubResearchLoveGroupedStageSpec(
        "execute-second-specialist",
        "task-kind:github-research-love-execute-second-specialist",
        EXECUTE_SECOND_CAPABILITY_REF,
        2,
    ),
    GitHubResearchLoveGroupedStageSpec(
        "persist-project-two-analyses",
        "task-kind:github-research-love-persist-project-two-analyses",
        PERSIST_PROJECT_PAIR_CAPABILITY_REF,
        3,
    ),
    GitHubResearchLoveGroupedStageSpec(
        "recall-two-analyses",
        "task-kind:github-research-love-recall-two-analyses",
        "capability:github-research.love.recall-two-analyses.v1",
        2,
    ),
    GitHubResearchLoveGroupedStageSpec(
        "synthesize-liaison",
        "task-kind:github-research-love-synthesize-liaison",
        "capability:github-research.love.synthesize-liaison.v1",
        2,
    ),
    GitHubResearchLoveGroupedStageSpec(
        "build-final-deliverable",
        "task-kind:github-research-love-build-final-deliverable",
        "capability:github-research.love.build-final-deliverable.v1",
        2,
    ),
    GitHubResearchLoveGroupedStageSpec(
        "prepare-publication",
        "task-kind:github-research-love-prepare-publication",
        "capability:github-research.love.prepare-publication.v1",
        2,
    ),
    GitHubResearchLoveGroupedStageSpec(
        "publish-remote",
        "task-kind:github-research-love-publish-remote",
        "capability:github-research.love.publish-remote.v1",
        2,
    ),
    GitHubResearchLoveGroupedStageSpec(
        "close-cycle",
        "task-kind:github-research-love-close-cycle",
        "capability:github-research.love.close-cycle.v1",
        3,
    ),
)


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveGroupedTaskGraphBuild:
    schema: str
    graph: SchedulerTaskGraph
    stage_task_refs: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.schema != GROUPED_GRAPH_SCHEMA:
            raise GitHubResearchLoveGroupedPipelineError(
                "schéma de graphe groupé non pris en charge"
            )
        copied = dict(self.stage_task_refs)
        expected = tuple(spec.stage for spec in GROUPED_STAGE_SPECS)
        if tuple(copied) != expected:
            raise GitHubResearchLoveGroupedPipelineError(
                "stage_task_refs diverge des étapes groupées"
            )
        if tuple(copied.values()) != tuple(
            task.task_ref for task in self.graph.tasks
        ):
            raise GitHubResearchLoveGroupedPipelineError(
                "stage_task_refs diverge des tâches"
            )
        object.__setattr__(self, "stage_task_refs", MappingProxyType(copied))


@dataclass(frozen=True, slots=True)
class GitHubResearchLovePairStageInput:
    """Entrées réhydratées pour la persistance SQL puis les deux projections."""

    runtime_ports: ImportedActionsRuntimePorts = field(repr=False, compare=False)
    first_dispatch: Mapping[str, Any]
    second_dispatch: Mapping[str, Any]
    reference_point_reader: ReferencePointReader = field(
        repr=False,
        compare=False,
    )
    branch_ref: str
    project_ref: str
    conversation_ref: str
    security_scope: str
    dense_vector_name: str
    sparse_vector_name: str
    projected_at: str = ""

    def __post_init__(self) -> None:
        for name in ("first_dispatch", "second_dispatch"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise TypeError(f"{name} doit être un mapping")
            object.__setattr__(self, name, MappingProxyType(dict(value)))
        for name in (
            "branch_ref",
            "project_ref",
            "conversation_ref",
            "security_scope",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or ":" not in value:
                raise TypeError(f"{name} doit être une référence typée")
        for name in ("dense_vector_name", "sparse_vector_name"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f"{name} doit être non vide")
        if self.dense_vector_name == self.sparse_vector_name:
            raise ValueError("les noms des vecteurs dense et sparse doivent différer")


class GitHubResearchLoveGroupedInputProvider(Protocol):
    """Réhydrate les entrées durables sans prendre de décision Scheduler."""

    def load_first_dispatch_command(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
    ) -> GitHubResearchLoveFirstVisitDispatchCommand: ...

    def load_second_dispatch_command(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
    ) -> GitHubResearchLoveSecondVisitDispatchCommand: ...

    def load_pair_stage_input(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
    ) -> GitHubResearchLovePairStageInput: ...


@dataclass(frozen=True, slots=True)
class GitHubResearchLovePersistedProjectedPair:
    """Preuve compacte de deux objets SQL et deux projections distinctes."""

    schema: str
    command_ref: str
    scheduler_task_ref: str
    work_package_ref: str
    sql_plan_digest: str
    revision_ref: str
    first_object_ref: str
    second_object_ref: str
    first_artifact_ref: str
    second_artifact_ref: str
    qdrant_pair_plan_digest: str
    first_projection: Mapping[str, Any]
    second_projection: Mapping[str, Any]
    completed_at: str
    result_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema != PAIR_RESULT_SCHEMA:
            raise GitHubResearchLoveGroupedPipelineError(
                "schéma de résultat pair non pris en charge"
            )
        for name in (
            "command_ref",
            "scheduler_task_ref",
            "work_package_ref",
            "revision_ref",
            "first_object_ref",
            "second_object_ref",
            "first_artifact_ref",
            "second_artifact_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or ":" not in value:
                raise TypeError(f"{name} doit être une référence typée")
        if self.first_object_ref == self.second_object_ref:
            raise GitHubResearchLoveGroupedPipelineError(
                "les deux analyses doivent rester des objets SQL distincts"
            )
        if self.first_artifact_ref == self.second_artifact_ref:
            raise GitHubResearchLoveGroupedPipelineError(
                "les deux artefacts doivent rester distincts"
            )
        for name in ("sql_plan_digest", "qdrant_pair_plan_digest"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.startswith("sha256:"):
                raise TypeError(f"{name} doit être un SHA-256 préfixé")
        if "T" not in self.completed_at or not self.completed_at.endswith("Z"):
            raise TypeError("completed_at doit être un horodatage UTC")
        first = MappingProxyType(dict(self.first_projection))
        second = MappingProxyType(dict(self.second_projection))
        if first.get("object_ref") == second.get("object_ref"):
            raise GitHubResearchLoveGroupedPipelineError(
                "les reçus Qdrant doivent référencer deux objets distincts"
            )
        object.__setattr__(self, "first_projection", first)
        object.__setattr__(self, "second_projection", second)
        object.__setattr__(self, "result_digest", _pair_result_digest(self))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "command_ref": self.command_ref,
            "scheduler_task_ref": self.scheduler_task_ref,
            "work_package_ref": self.work_package_ref,
            "sql_plan_digest": self.sql_plan_digest,
            "revision_ref": self.revision_ref,
            "first_object_ref": self.first_object_ref,
            "second_object_ref": self.second_object_ref,
            "first_artifact_ref": self.first_artifact_ref,
            "second_artifact_ref": self.second_artifact_ref,
            "qdrant_pair_plan_digest": self.qdrant_pair_plan_digest,
            "first_projection": dict(self.first_projection),
            "second_projection": dict(self.second_projection),
            "completed_at": self.completed_at,
            "result_digest": self.result_digest,
            "checks": {
                "two_sql_objects_distinct": True,
                "two_sql_artifacts_distinct": True,
                "two_qdrant_projections_distinct": True,
                "embedding_dimension": 384,
                "sql_remains_authority": True,
            },
        }


class GitHubResearchLoveExecuteFirstSpecialistHandler(
    SchedulerHandler[
        GitHubResearchSchedulerCommand,
        GitHubResearchLoveFirstVisitDispatchResult,
    ]
):
    HANDLER_REF = EXECUTE_FIRST_HANDLER_REF
    CAPABILITY_REF = EXECUTE_FIRST_CAPABILITY_REF
    COMMAND_TYPE = GitHubResearchSchedulerCommand
    RESULT_TYPE = GitHubResearchLoveFirstVisitDispatchResult
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.DEDUPLICATED,
        timeout_policy_ref="timeout-policy:github-love-first-specialist-v1",
        retry_policy_ref="retry-policy:github-love-first-specialist-v1",
        resource_profile_ref="resource-profile:love-specialist-analysis-v1",
        laboratory_compatibility=("laboratory-kind:love-studies",),
    )
    INFORMATION = HandlerInformation(
        title="Exécution du premier spécialiste amour",
        summary="Délègue la première visite au chemin Scheduler/laboratoire existant.",
    )

    def __init__(self, provider: GitHubResearchLoveGroupedInputProvider) -> None:
        self._provider = _provider(provider)

    async def execute(
        self,
        command: GitHubResearchSchedulerCommand,
        context: object,
    ) -> GitHubResearchLoveFirstVisitDispatchResult:
        execution_context = _execution_context(
            command,
            context,
            "execute-first-specialist",
        )
        dispatch_command = self._provider.load_first_dispatch_command(
            command=command,
            execution_context=execution_context,
        )
        if not isinstance(
            dispatch_command,
            GitHubResearchLoveFirstVisitDispatchCommand,
        ):
            raise TypeError(
                "load_first_dispatch_command doit retourner la commande attendue"
            )
        result = await dispatch_first_love_visit_from_github_research(
            dispatch_command
        )
        if not result.valid or result.status != "first-specialist-completed":
            raise GitHubResearchLoveGroupedPipelineError(
                "la première analyse spécialiste n'est pas complète: "
                + "; ".join(result.issues)
            )
        return result


class GitHubResearchLoveExecuteSecondSpecialistHandler(
    SchedulerHandler[
        GitHubResearchSchedulerCommand,
        GitHubResearchLoveSecondVisitDispatchResult,
    ]
):
    HANDLER_REF = EXECUTE_SECOND_HANDLER_REF
    CAPABILITY_REF = EXECUTE_SECOND_CAPABILITY_REF
    COMMAND_TYPE = GitHubResearchSchedulerCommand
    RESULT_TYPE = GitHubResearchLoveSecondVisitDispatchResult
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.DEDUPLICATED,
        timeout_policy_ref="timeout-policy:github-love-second-specialist-v1",
        retry_policy_ref="retry-policy:github-love-second-specialist-v1",
        resource_profile_ref="resource-profile:love-specialist-analysis-v1",
        laboratory_compatibility=("laboratory-kind:love-studies",),
    )
    INFORMATION = HandlerInformation(
        title="Exécution du second spécialiste amour",
        summary="Réhydrate la première analyse puis délègue la visite complémentaire existante.",
    )

    def __init__(self, provider: GitHubResearchLoveGroupedInputProvider) -> None:
        self._provider = _provider(provider)

    async def execute(
        self,
        command: GitHubResearchSchedulerCommand,
        context: object,
    ) -> GitHubResearchLoveSecondVisitDispatchResult:
        execution_context = _execution_context(
            command,
            context,
            "execute-second-specialist",
        )
        dispatch_command = self._provider.load_second_dispatch_command(
            command=command,
            execution_context=execution_context,
        )
        if not isinstance(
            dispatch_command,
            GitHubResearchLoveSecondVisitDispatchCommand,
        ):
            raise TypeError(
                "load_second_dispatch_command doit retourner la commande attendue"
            )
        result = await dispatch_second_love_visit_from_first_analysis(
            dispatch_command
        )
        if not result.valid or result.status != "second-specialist-completed":
            raise GitHubResearchLoveGroupedPipelineError(
                "la seconde analyse spécialiste n'est pas complète: "
                + "; ".join(result.issues)
            )
        return result


class GitHubResearchLovePersistProjectPairHandler(
    SchedulerHandler[
        GitHubResearchSchedulerCommand,
        GitHubResearchLovePersistedProjectedPair,
    ]
):
    HANDLER_REF = PERSIST_PROJECT_PAIR_HANDLER_REF
    CAPABILITY_REF = PERSIST_PROJECT_PAIR_CAPABILITY_REF
    COMMAND_TYPE = GitHubResearchSchedulerCommand
    RESULT_TYPE = GitHubResearchLovePersistedProjectedPair
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.IDEMPOTENT,
        timeout_policy_ref="timeout-policy:github-love-persist-project-pair-v1",
        retry_policy_ref="retry-policy:github-love-persist-project-pair-v1",
        resource_profile_ref="resource-profile:sql-openvino-qdrant-v1",
        laboratory_compatibility=("laboratory-kind:love-studies",),
    )
    INFORMATION = HandlerInformation(
        title="Persistance et projection des deux analyses amour",
        summary=(
            "Écrit deux objets SQL distincts puis deux projections Qdrant distinctes "
            "avec OpenVINO/E5 384 dimensions."
        ),
    )

    def __init__(self, provider: GitHubResearchLoveGroupedInputProvider) -> None:
        self._provider = _provider(provider)

    async def execute(
        self,
        command: GitHubResearchSchedulerCommand,
        context: object,
    ) -> GitHubResearchLovePersistedProjectedPair:
        execution_context = _execution_context(
            command,
            context,
            "persist-project-two-analyses",
        )
        inputs = self._provider.load_pair_stage_input(
            command=command,
            execution_context=execution_context,
        )
        if not isinstance(inputs, GitHubResearchLovePairStageInput):
            raise TypeError(
                "load_pair_stage_input doit retourner GitHubResearchLovePairStageInput"
            )
        persistence = persist_github_research_love_analyses(
            runtime_ports=inputs.runtime_ports,
            first_dispatch=inputs.first_dispatch,
            second_dispatch=inputs.second_dispatch,
            created_at=execution_context.started_at,
        )
        _require_persisted(persistence)
        persistence_mapping = persistence.to_mapping()
        projection_command = GitHubResearchLoveTwoProjectionCommand(
            runtime_ports=inputs.runtime_ports,
            sql_persistence=persistence_mapping,
            reference_point_reader=inputs.reference_point_reader,
            branch_ref=inputs.branch_ref,
            project_ref=inputs.project_ref,
            conversation_ref=inputs.conversation_ref,
            security_scope=inputs.security_scope,
            dense_vector_name=inputs.dense_vector_name,
            sparse_vector_name=inputs.sparse_vector_name,
            projected_at=inputs.projected_at,
            allow_write=True,
        )
        projections = await project_github_research_love_analyses(
            projection_command
        )
        _require_projected(projections)
        assert persistence.receipt is not None
        assert projections.receipt is not None
        sql_receipt = persistence.receipt
        projection_receipt = projections.receipt
        return GitHubResearchLovePersistedProjectedPair(
            schema=PAIR_RESULT_SCHEMA,
            command_ref=command.command_ref,
            scheduler_task_ref=execution_context.task_ref,
            work_package_ref=sql_receipt.work_package_ref,
            sql_plan_digest=sql_receipt.plan_digest,
            revision_ref=sql_receipt.revision_ref,
            first_object_ref=sql_receipt.first_object_ref,
            second_object_ref=sql_receipt.second_object_ref,
            first_artifact_ref=sql_receipt.first_artifact_ref,
            second_artifact_ref=sql_receipt.second_artifact_ref,
            qdrant_pair_plan_digest=projection_receipt.pair_plan_digest,
            first_projection=projection_receipt.first,
            second_projection=projection_receipt.second,
            completed_at=execution_context.started_at,
        )


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveGroupedSchedulerBootstrap:
    catalog: SchedulerHandlerCatalog
    factory: SchedulerHandlerFactory = field(repr=False, compare=False)
    handler_refs: tuple[str, ...]
    capability_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        bindings = self.catalog.snapshot()
        if tuple(binding.handler_ref for binding in bindings) != self.handler_refs:
            raise GitHubResearchLoveGroupedPipelineError(
                "handler_refs diverge du catalogue groupé"
            )
        if tuple(binding.key.capability_ref for binding in bindings) != (
            self.capability_refs
        ):
            raise GitHubResearchLoveGroupedPipelineError(
                "capability_refs diverge du catalogue groupé"
            )


def build_github_research_love_grouped_task_graph(
    command: GitHubResearchSchedulerCommand,
    *,
    created_at: str,
) -> GitHubResearchLoveGroupedTaskGraphBuild:
    """Construit dix tâches en regroupant uniquement les effets compatibles."""

    if not isinstance(command, GitHubResearchSchedulerCommand):
        raise TypeError("command doit être GitHubResearchSchedulerCommand")
    if "T" not in created_at or not created_at.endswith("Z"):
        raise TypeError("created_at doit être un horodatage UTC")
    if command.execution_budget.max_scheduler_steps < len(GROUPED_STAGE_SPECS):
        raise GitHubResearchLoveGroupedPipelineError(
            "max_scheduler_steps est inférieur au graphe groupé"
        )
    if command.execution_budget.max_specialist_visits < 2:
        raise GitHubResearchLoveGroupedPipelineError(
            "deux visites de spécialistes sont requises"
        )
    refs = {
        spec.stage: grouped_stage_task_ref(command.command_ref, spec.stage)
        for spec in GROUPED_STAGE_SPECS
    }
    context_refs = tuple(
        dict.fromkeys(
            (
                *command.research.context_refs,
                command.correlation.conversation_ref,
                command.correlation.return_route_ref,
                command.research.work_package_ref,
                command.research.route_candidate_ref,
            )
        )
    )
    tasks: list[SchedulerTask] = []
    previous_ref = ""
    for index, spec in enumerate(GROUPED_STAGE_SPECS):
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
            priority=max(0, min(100, command.priority - index // 2)),
            max_attempts=spec.max_attempts,
            created_at=created_at,
            parent_task_ref=previous_ref,
            dependencies=dependencies,
            context_refs=context_refs,
            evidence_refs=tuple(command.research.evidence_refs),
        )
        tasks.append(task)
        previous_ref = task.task_ref
    digest = hashlib.sha256(command.command_ref.encode("utf-8")).hexdigest()[:24]
    graph = SchedulerTaskGraph.create(
        graph_ref=f"scheduler-task-graph:github-love-grouped-{digest}",
        command_ref=command.command_ref,
        created_at=created_at,
        tasks=tasks,
    )
    return GitHubResearchLoveGroupedTaskGraphBuild(
        schema=GROUPED_GRAPH_SCHEMA,
        graph=graph,
        stage_task_refs=refs,
    )


def build_github_research_love_grouped_scheduler_bootstrap(
    first_visit_input_provider: GitHubResearchLoveFirstVisitInputProvider,
    grouped_input_provider: GitHubResearchLoveGroupedInputProvider,
) -> GitHubResearchLoveGroupedSchedulerBootstrap:
    """Catalogue explicitement les quatre capacités réellement disponibles."""

    _provider(grouped_input_provider)
    handler_types = (
        GitHubResearchLovePrepareFirstVisitHandler,
        GitHubResearchLoveExecuteFirstSpecialistHandler,
        GitHubResearchLoveExecuteSecondSpecialistHandler,
        GitHubResearchLovePersistProjectPairHandler,
    )
    catalog = SchedulerHandlerCatalog(handler_types)
    builders = {
        GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_HANDLER_REF: (
            lambda _binding, _ticket: GitHubResearchLovePrepareFirstVisitHandler(
                first_visit_input_provider
            )
        ),
        EXECUTE_FIRST_HANDLER_REF: (
            lambda _binding, _ticket: GitHubResearchLoveExecuteFirstSpecialistHandler(
                grouped_input_provider
            )
        ),
        EXECUTE_SECOND_HANDLER_REF: (
            lambda _binding, _ticket: GitHubResearchLoveExecuteSecondSpecialistHandler(
                grouped_input_provider
            )
        ),
        PERSIST_PROJECT_PAIR_HANDLER_REF: (
            lambda _binding, _ticket: GitHubResearchLovePersistProjectPairHandler(
                grouped_input_provider
            )
        ),
    }
    factory = ExplicitSchedulerHandlerFactory(builders)
    bindings = catalog.snapshot()
    return GitHubResearchLoveGroupedSchedulerBootstrap(
        catalog=catalog,
        factory=factory,
        handler_refs=tuple(binding.handler_ref for binding in bindings),
        capability_refs=tuple(binding.key.capability_ref for binding in bindings),
    )


def grouped_stage_task_ref(command_ref: str, stage: str) -> str:
    if stage not in {spec.stage for spec in GROUPED_STAGE_SPECS}:
        raise GitHubResearchLoveGroupedPipelineError(f"étape groupée inconnue: {stage}")
    suffix = hashlib.sha256(command_ref.encode("utf-8")).hexdigest()[:20]
    return f"scheduler-task:github-love-grouped-{stage}-{suffix}"


def _execution_context(
    command: GitHubResearchSchedulerCommand,
    context: object,
    stage: str,
) -> SchedulerHandlerExecutionContext:
    if not isinstance(command, GitHubResearchSchedulerCommand):
        raise TypeError("command doit être GitHubResearchSchedulerCommand")
    if not isinstance(context, SchedulerHandlerExecutionContext):
        raise TypeError("context doit être SchedulerHandlerExecutionContext")
    if context.command_ref != command.command_ref:
        raise GitHubResearchLoveGroupedPipelineError(
            "le contexte appartient à une autre commande"
        )
    expected = grouped_stage_task_ref(command.command_ref, stage)
    if context.task_ref != expected:
        raise GitHubResearchLoveGroupedPipelineError(
            f"le handler {stage} a reçu une autre tâche"
        )
    return context


def _provider(
    value: GitHubResearchLoveGroupedInputProvider,
) -> GitHubResearchLoveGroupedInputProvider:
    for name in (
        "load_first_dispatch_command",
        "load_second_dispatch_command",
        "load_pair_stage_input",
    ):
        if not callable(getattr(value, name, None)):
            raise TypeError(f"grouped_input_provider doit exposer {name}")
    return value


def _require_persisted(value: GitHubResearchLoveSqlPersistenceResult) -> None:
    if not isinstance(value, GitHubResearchLoveSqlPersistenceResult):
        raise TypeError("la persistance doit retourner son résultat typé")
    if not value.valid or value.status != "persisted" or value.receipt is None:
        raise GitHubResearchLoveGroupedPipelineError(
            "les deux analyses ne sont pas durablement persistées: "
            + "; ".join(value.issues)
        )
    if value.receipt.first_object_ref == value.receipt.second_object_ref:
        raise GitHubResearchLoveGroupedPipelineError(
            "la persistance a fusionné les deux analyses"
        )


def _require_projected(value: GitHubResearchLoveTwoProjectionResult) -> None:
    if not isinstance(value, GitHubResearchLoveTwoProjectionResult):
        raise TypeError("la projection doit retourner son résultat typé")
    if not value.valid or value.status != "projected" or value.receipt is None:
        raise GitHubResearchLoveGroupedPipelineError(
            "les deux analyses ne sont pas projetées: " + "; ".join(value.issues)
        )
    if value.receipt.first.get("object_ref") == value.receipt.second.get(
        "object_ref"
    ):
        raise GitHubResearchLoveGroupedPipelineError(
            "les deux projections ne sont pas distinctes"
        )


def _pair_result_digest(value: GitHubResearchLovePersistedProjectedPair) -> str:
    payload = {
        "schema": value.schema,
        "command_ref": value.command_ref,
        "scheduler_task_ref": value.scheduler_task_ref,
        "work_package_ref": value.work_package_ref,
        "sql_plan_digest": value.sql_plan_digest,
        "revision_ref": value.revision_ref,
        "first_object_ref": value.first_object_ref,
        "second_object_ref": value.second_object_ref,
        "first_artifact_ref": value.first_artifact_ref,
        "second_artifact_ref": value.second_artifact_ref,
        "qdrant_pair_plan_digest": value.qdrant_pair_plan_digest,
        "first_projection": dict(value.first_projection),
        "second_projection": dict(value.second_projection),
        "completed_at": value.completed_at,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


__all__ = (
    "EXECUTE_FIRST_CAPABILITY_REF",
    "EXECUTE_FIRST_HANDLER_REF",
    "EXECUTE_SECOND_CAPABILITY_REF",
    "EXECUTE_SECOND_HANDLER_REF",
    "GROUPED_GRAPH_SCHEMA",
    "GROUPED_STAGE_SPECS",
    "PAIR_RESULT_SCHEMA",
    "PERSIST_PROJECT_PAIR_CAPABILITY_REF",
    "PERSIST_PROJECT_PAIR_HANDLER_REF",
    "GitHubResearchLoveExecuteFirstSpecialistHandler",
    "GitHubResearchLoveExecuteSecondSpecialistHandler",
    "GitHubResearchLoveGroupedInputProvider",
    "GitHubResearchLoveGroupedPipelineError",
    "GitHubResearchLoveGroupedSchedulerBootstrap",
    "GitHubResearchLoveGroupedStageSpec",
    "GitHubResearchLoveGroupedTaskGraphBuild",
    "GitHubResearchLovePairStageInput",
    "GitHubResearchLovePersistProjectPairHandler",
    "GitHubResearchLovePersistedProjectedPair",
    "build_github_research_love_grouped_scheduler_bootstrap",
    "build_github_research_love_grouped_task_graph",
    "grouped_stage_task_ref",
)
