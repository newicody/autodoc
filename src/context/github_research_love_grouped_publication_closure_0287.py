"""Handlers Scheduler de publication contrôlée et clôture durable.

Cette unité adapte les composants de publication et de preuve SQL déjà
présents. Le plan est reconstruit de manière déterministe depuis les données
durables. La publication distante et la clôture SQL sont exécutées dans le même
handler rejouable afin qu'un crash après mutation GitHub mais avant la preuve SQL
puisse reprendre par le mécanisme de replay du publisher existant.

La dernière tâche du graphe ne republie rien : elle relit et vérifie seulement
la fermeture durable fournie par un port injecté.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol

from context.github_research_love_final_remote_publication_0287 import (
    GitHubResearchLoveFinalPublicationCommand,
    GitHubResearchLoveFinalPublicationExecution,
    GitHubResearchLoveFinalPublicationPlan,
    GitHubResearchLoveFinalPublicationResult,
    build_github_research_love_final_publication_plan,
    execute_github_research_love_final_publication,
)
from context.github_research_love_grouped_recall_synthesis_deliverable_0287 import (
    BUILD_FINAL_DELIVERABLE_HANDLER_REF,
    RECALL_TWO_ANALYSES_HANDLER_REF,
    SYNTHESIZE_LIAISON_HANDLER_REF,
    GitHubResearchLoveBuildFinalDeliverableHandler,
    GitHubResearchLoveCompleteGroupedSchedulerBootstrap,
    build_github_research_love_complete_grouped_scheduler_bootstrap,
    GitHubResearchLoveGroupedDownstreamInputProvider,
    GitHubResearchLoveRecallTwoAnalysesHandler,
    GitHubResearchLoveSynthesizeLiaisonHandler,
)
from context.github_research_love_grouped_specialist_pipeline_0287 import (
    EXECUTE_FIRST_HANDLER_REF,
    EXECUTE_SECOND_HANDLER_REF,
    PERSIST_PROJECT_PAIR_HANDLER_REF,
    GitHubResearchLoveExecuteFirstSpecialistHandler,
    GitHubResearchLoveExecuteSecondSpecialistHandler,
    GitHubResearchLoveGroupedInputProvider,
    GitHubResearchLovePersistProjectPairHandler,
    grouped_stage_task_ref,
)
from context.github_research_love_publication_evidence_sql_0287 import (
    GitHubResearchLoveCycleClosureResult,
    GitHubResearchLovePublicationEvidenceCommand,
    close_github_research_love_cycle,
)
from context.github_research_love_scheduler_bootstrap_0287 import (
    GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_HANDLER_REF,
    GitHubResearchLoveFirstVisitInputProvider,
    GitHubResearchLovePrepareFirstVisitHandler,
)
from context.github_research_scheduler_command_0287 import (
    GitHubResearchSchedulerCommand,
)
from context.love_final_deliverable_remote_publication_0287 import (
    FinalDeliverableIssuePublicationPort,
    FinalDeliverableProjectV2PublicationPort,
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

PREPARE_PUBLICATION_CAPABILITY_REF = (
    "capability:github-research.love.prepare-publication.v1"
)
PUBLISH_REMOTE_CAPABILITY_REF = (
    "capability:github-research.love.publish-remote.v1"
)
CLOSE_CYCLE_CAPABILITY_REF = (
    "capability:github-research.love.close-cycle.v1"
)

PREPARE_PUBLICATION_HANDLER_REF = (
    "handler:github-research-love-prepare-publication-v1"
)
PUBLISH_REMOTE_HANDLER_REF = (
    "handler:github-research-love-publish-remote-v1"
)
CLOSE_CYCLE_HANDLER_REF = (
    "handler:github-research-love-close-cycle-v1"
)

PUBLISHED_CLOSED_SCHEMA = (
    "missipy.github.research_love_scheduler_published_closed.v1"
)
CLOSURE_VERIFICATION_SCHEMA = (
    "missipy.github.research_love_scheduler_closure_verification.v1"
)


class GitHubResearchLoveGroupedPublicationError(RuntimeError):
    """Erreur de corrélation, d'autorisation ou de fermeture du cycle."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLovePublicationAuthorization:
    """Autorisation explicite consommée par la tâche de mutation distante."""

    runtime_ports: ImportedActionsRuntimePorts = field(repr=False, compare=False)
    final_deliverable: Mapping[str, Any]
    issue_port: FinalDeliverableIssuePublicationPort = field(
        repr=False,
        compare=False,
    )
    project_port: FinalDeliverableProjectV2PublicationPort = field(
        repr=False,
        compare=False,
    )
    confirm_plan_digest: str
    closed_at: str
    operator_decision: str = "approve"
    remote_mutation_allowed: bool = False
    issue_publication_allowed: bool = False
    project_projection_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.final_deliverable, Mapping):
            raise TypeError("final_deliverable doit être un mapping")
        object.__setattr__(
            self,
            "final_deliverable",
            MappingProxyType(dict(self.final_deliverable)),
        )
        if not self.confirm_plan_digest.startswith("sha256:"):
            raise GitHubResearchLoveGroupedPublicationError(
                "confirm_plan_digest doit commencer par sha256:"
            )
        if self.operator_decision != "approve":
            raise GitHubResearchLoveGroupedPublicationError(
                "operator_decision doit être approve"
            )
        if "T" not in self.closed_at or not self.closed_at.endswith("Z"):
            raise GitHubResearchLoveGroupedPublicationError(
                "closed_at doit être un horodatage UTC terminé par Z"
            )
        if not (
            self.remote_mutation_allowed
            and self.issue_publication_allowed
            and self.project_projection_allowed
        ):
            raise GitHubResearchLoveGroupedPublicationError(
                "la publication exige les trois verrous distants"
            )


class GitHubResearchLoveGroupedPublicationInputProvider(Protocol):
    """Réhydrate les entrées durables sans décider de la tâche suivante."""

    def load_publication_command(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
    ) -> GitHubResearchLoveFinalPublicationCommand: ...

    def load_publication_authorization(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
        publication_plan: GitHubResearchLoveFinalPublicationPlan,
    ) -> GitHubResearchLovePublicationAuthorization: ...

    def load_cycle_closure_result(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
    ) -> GitHubResearchLoveCycleClosureResult: ...


PublicationCommandLoader = Callable[..., GitHubResearchLoveFinalPublicationCommand]
PublicationAuthorizationLoader = Callable[
    ...,
    GitHubResearchLovePublicationAuthorization,
]
CycleClosureLoader = Callable[..., GitHubResearchLoveCycleClosureResult]


@dataclass(frozen=True, slots=True)
class ExplicitGitHubResearchLoveGroupedPublicationInputProvider:
    """Adaptateur concret construit avec trois loaders explicitement injectés."""

    publication_command_loader: PublicationCommandLoader = field(
        repr=False,
        compare=False,
    )
    publication_authorization_loader: PublicationAuthorizationLoader = field(
        repr=False,
        compare=False,
    )
    cycle_closure_loader: CycleClosureLoader = field(
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        for name in (
            "publication_command_loader",
            "publication_authorization_loader",
            "cycle_closure_loader",
        ):
            if not callable(getattr(self, name)):
                raise TypeError(f"{name} doit être appelable")

    def load_publication_command(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
    ) -> GitHubResearchLoveFinalPublicationCommand:
        return self.publication_command_loader(
            command=command,
            execution_context=execution_context,
        )

    def load_publication_authorization(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
        publication_plan: GitHubResearchLoveFinalPublicationPlan,
    ) -> GitHubResearchLovePublicationAuthorization:
        return self.publication_authorization_loader(
            command=command,
            execution_context=execution_context,
            publication_plan=publication_plan,
        )

    def load_cycle_closure_result(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
    ) -> GitHubResearchLoveCycleClosureResult:
        return self.cycle_closure_loader(
            command=command,
            execution_context=execution_context,
        )


@dataclass(frozen=True, slots=True)
class GitHubResearchLovePublishedClosedResult:
    """Résultat atomique logique : publication vérifiée puis preuve SQL."""

    schema: str
    command_ref: str
    scheduler_task_ref: str
    work_package_ref: str
    publication_plan_digest: str
    remote_publication: GitHubResearchLoveFinalPublicationResult
    closure: GitHubResearchLoveCycleClosureResult

    def __post_init__(self) -> None:
        if self.schema != PUBLISHED_CLOSED_SCHEMA:
            raise GitHubResearchLoveGroupedPublicationError(
                "schéma published-closed non pris en charge"
            )
        if not self.command_ref.startswith("scheduler-command:"):
            raise GitHubResearchLoveGroupedPublicationError(
                "command_ref doit être une référence Scheduler"
            )
        if not self.scheduler_task_ref.startswith("scheduler-task:"):
            raise GitHubResearchLoveGroupedPublicationError(
                "scheduler_task_ref doit être une référence de tâche"
            )
        if not self.work_package_ref.startswith("research-work-package:"):
            raise GitHubResearchLoveGroupedPublicationError(
                "work_package_ref doit être une référence de paquet"
            )
        if self.remote_publication.plan.plan_digest != self.publication_plan_digest:
            raise GitHubResearchLoveGroupedPublicationError(
                "le digest du résultat distant diverge du plan"
            )
        if not self.remote_publication.valid or self.remote_publication.status not in {
            "published",
            "published-replay",
        }:
            raise GitHubResearchLoveGroupedPublicationError(
                "la publication distante n'est pas confirmée"
            )
        if not self.closure.valid or self.closure.status != "closed":
            raise GitHubResearchLoveGroupedPublicationError(
                "la preuve SQL de fermeture n'est pas confirmée"
            )
        if self.closure.plan is None:
            raise GitHubResearchLoveGroupedPublicationError(
                "le plan de fermeture SQL est absent"
            )
        if self.closure.plan.work_package_ref != self.work_package_ref:
            raise GitHubResearchLoveGroupedPublicationError(
                "la fermeture appartient à un autre paquet de recherche"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": True,
            "status": "published-and-closed",
            "command_ref": self.command_ref,
            "scheduler_task_ref": self.scheduler_task_ref,
            "work_package_ref": self.work_package_ref,
            "publication_plan_digest": self.publication_plan_digest,
            "remote_publication": self.remote_publication.to_mapping(),
            "closure": self.closure.to_mapping(),
            "boundaries": {
                "remote_publication_replay_safe": True,
                "publication_evidence_persisted": True,
                "sql_cycle_closed": True,
                "scheduler_remains_authority": True,
                "new_scheduler_created": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveCycleClosureVerification:
    """Relecture finale sans nouvelle mutation distante ni nouvelle écriture SQL."""

    schema: str
    command_ref: str
    scheduler_task_ref: str
    work_package_ref: str
    closure_plan_digest: str
    closure_revision_ref: str
    publication_evidence_object_ref: str
    verified_at: str

    def __post_init__(self) -> None:
        if self.schema != CLOSURE_VERIFICATION_SCHEMA:
            raise GitHubResearchLoveGroupedPublicationError(
                "schéma de vérification de fermeture non pris en charge"
            )
        for name, prefix in (
            ("command_ref", "scheduler-command:"),
            ("scheduler_task_ref", "scheduler-task:"),
            ("work_package_ref", "research-work-package:"),
            ("closure_plan_digest", "sha256:"),
            ("closure_revision_ref", "context-revision:"),
            ("publication_evidence_object_ref", "context-object:"),
        ):
            if not getattr(self, name).startswith(prefix):
                raise GitHubResearchLoveGroupedPublicationError(
                    f"{name} doit commencer par {prefix}"
                )
        if "T" not in self.verified_at or not self.verified_at.endswith("Z"):
            raise GitHubResearchLoveGroupedPublicationError(
                "verified_at doit être un horodatage UTC terminé par Z"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": True,
            "status": "closed-verified",
            "command_ref": self.command_ref,
            "scheduler_task_ref": self.scheduler_task_ref,
            "work_package_ref": self.work_package_ref,
            "closure_plan_digest": self.closure_plan_digest,
            "closure_revision_ref": self.closure_revision_ref,
            "publication_evidence_object_ref": (
                self.publication_evidence_object_ref
            ),
            "verified_at": self.verified_at,
            "remote_publication_performed": False,
            "sql_write_performed": False,
        }


class GitHubResearchLovePreparePublicationHandler(
    SchedulerHandler[
        GitHubResearchSchedulerCommand,
        GitHubResearchLoveFinalPublicationPlan,
    ]
):
    HANDLER_REF = PREPARE_PUBLICATION_HANDLER_REF
    CAPABILITY_REF = PREPARE_PUBLICATION_CAPABILITY_REF
    COMMAND_TYPE = GitHubResearchSchedulerCommand
    RESULT_TYPE = GitHubResearchLoveFinalPublicationPlan
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.IDEMPOTENT,
        timeout_policy_ref="timeout-policy:github-love-publication-plan-v1",
        retry_policy_ref="retry-policy:github-love-publication-plan-v1",
        resource_profile_ref="resource-profile:sql-publication-plan-v1",
        laboratory_compatibility=("laboratory-kind:love-studies",),
    )
    INFORMATION = HandlerInformation(
        title="Préparation de la publication finale amour",
        summary=(
            "Reconstruit le plan déterministe depuis le livrable SQL et exige "
            "une confirmation exacte de son digest avant toute mutation."
        ),
    )

    def __init__(
        self,
        provider: GitHubResearchLoveGroupedPublicationInputProvider,
    ) -> None:
        self._provider = _provider(provider)

    async def execute(
        self,
        command: GitHubResearchSchedulerCommand,
        context: object,
    ) -> GitHubResearchLoveFinalPublicationPlan:
        execution_context = _execution_context(
            command,
            context,
            "prepare-publication",
        )
        publication_command = self._provider.load_publication_command(
            command=command,
            execution_context=execution_context,
        )
        if not isinstance(
            publication_command,
            GitHubResearchLoveFinalPublicationCommand,
        ):
            raise TypeError(
                "load_publication_command doit retourner la commande typée"
            )
        plan = build_github_research_love_final_publication_plan(
            publication_command
        )
        _require_work_package(command, plan.work_package_ref)
        return plan


class GitHubResearchLovePublishRemoteAndCloseHandler(
    SchedulerHandler[
        GitHubResearchSchedulerCommand,
        GitHubResearchLovePublishedClosedResult,
    ]
):
    HANDLER_REF = PUBLISH_REMOTE_HANDLER_REF
    CAPABILITY_REF = PUBLISH_REMOTE_CAPABILITY_REF
    COMMAND_TYPE = GitHubResearchSchedulerCommand
    RESULT_TYPE = GitHubResearchLovePublishedClosedResult
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.DEDUPLICATED,
        timeout_policy_ref="timeout-policy:github-love-publish-and-close-v1",
        retry_policy_ref="retry-policy:github-love-publish-and-close-v1",
        resource_profile_ref="resource-profile:github-sql-publication-v1",
        laboratory_compatibility=("laboratory-kind:love-studies",),
    )
    INFORMATION = HandlerInformation(
        title="Publication distante et preuve SQL du cycle amour",
        summary=(
            "Exécute le publisher contrôlé avec les trois verrous, vérifie le "
            "readback puis persiste immédiatement la preuve SQL de fermeture."
        ),
    )

    def __init__(
        self,
        provider: GitHubResearchLoveGroupedPublicationInputProvider,
    ) -> None:
        self._provider = _provider(provider)

    async def execute(
        self,
        command: GitHubResearchSchedulerCommand,
        context: object,
    ) -> GitHubResearchLovePublishedClosedResult:
        execution_context = _execution_context(
            command,
            context,
            "publish-remote",
        )
        publication_command = self._provider.load_publication_command(
            command=command,
            execution_context=execution_context,
        )
        if not isinstance(
            publication_command,
            GitHubResearchLoveFinalPublicationCommand,
        ):
            raise TypeError(
                "load_publication_command doit retourner la commande typée"
            )
        plan = build_github_research_love_final_publication_plan(
            publication_command
        )
        _require_work_package(command, plan.work_package_ref)
        authorization = self._provider.load_publication_authorization(
            command=command,
            execution_context=execution_context,
            publication_plan=plan,
        )
        if not isinstance(
            authorization,
            GitHubResearchLovePublicationAuthorization,
        ):
            raise TypeError(
                "load_publication_authorization doit retourner l'autorisation typée"
            )
        if authorization.confirm_plan_digest != plan.plan_digest:
            raise GitHubResearchLoveGroupedPublicationError(
                "le digest confirmé diverge du plan reconstruit"
            )
        remote = execute_github_research_love_final_publication(
            GitHubResearchLoveFinalPublicationExecution(
                plan=plan,
                operator_decision=authorization.operator_decision,
                execute=True,
                confirm_plan_digest=authorization.confirm_plan_digest,
                remote_mutation_allowed=authorization.remote_mutation_allowed,
                issue_publication_allowed=authorization.issue_publication_allowed,
                project_projection_allowed=authorization.project_projection_allowed,
            ),
            issue_port=authorization.issue_port,
            project_port=authorization.project_port,
        )
        if not remote.valid or remote.status not in {
            "published",
            "published-replay",
        }:
            raise GitHubResearchLoveGroupedPublicationError(
                "la publication distante contrôlée a échoué: "
                + "; ".join(remote.remote_result.issues)
            )
        closure = close_github_research_love_cycle(
            GitHubResearchLovePublicationEvidenceCommand(
                runtime_ports=authorization.runtime_ports,
                final_deliverable=authorization.final_deliverable,
                remote_publication=remote.to_mapping(),
                closed_at=authorization.closed_at,
            )
        )
        if not closure.valid or closure.status != "closed":
            raise GitHubResearchLoveGroupedPublicationError(
                "la preuve SQL de publication n'a pas fermé le cycle: "
                + "; ".join(closure.issues)
            )
        return GitHubResearchLovePublishedClosedResult(
            schema=PUBLISHED_CLOSED_SCHEMA,
            command_ref=command.command_ref,
            scheduler_task_ref=execution_context.task_ref,
            work_package_ref=plan.work_package_ref,
            publication_plan_digest=plan.plan_digest,
            remote_publication=remote,
            closure=closure,
        )


class GitHubResearchLoveVerifyClosedCycleHandler(
    SchedulerHandler[
        GitHubResearchSchedulerCommand,
        GitHubResearchLoveCycleClosureVerification,
    ]
):
    HANDLER_REF = CLOSE_CYCLE_HANDLER_REF
    CAPABILITY_REF = CLOSE_CYCLE_CAPABILITY_REF
    COMMAND_TYPE = GitHubResearchSchedulerCommand
    RESULT_TYPE = GitHubResearchLoveCycleClosureVerification
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.IDEMPOTENT,
        timeout_policy_ref="timeout-policy:github-love-verify-closure-v1",
        retry_policy_ref="retry-policy:github-love-verify-closure-v1",
        resource_profile_ref="resource-profile:sql-closure-read-v1",
        laboratory_compatibility=("laboratory-kind:love-studies",),
    )
    INFORMATION = HandlerInformation(
        title="Vérification durable de la fermeture du cycle amour",
        summary=(
            "Relit la preuve PostgreSQL finale sans republier et rend au "
            "Scheduler une confirmation typée de cycle fermé."
        ),
    )

    def __init__(
        self,
        provider: GitHubResearchLoveGroupedPublicationInputProvider,
    ) -> None:
        self._provider = _provider(provider)

    async def execute(
        self,
        command: GitHubResearchSchedulerCommand,
        context: object,
    ) -> GitHubResearchLoveCycleClosureVerification:
        execution_context = _execution_context(
            command,
            context,
            "close-cycle",
        )
        closure = self._provider.load_cycle_closure_result(
            command=command,
            execution_context=execution_context,
        )
        if not isinstance(closure, GitHubResearchLoveCycleClosureResult):
            raise TypeError(
                "load_cycle_closure_result doit retourner le résultat typé"
            )
        if (
            not closure.valid
            or closure.status != "closed"
            or closure.plan is None
            or closure.receipt is None
            or not closure.receipt.readback_verified
        ):
            raise GitHubResearchLoveGroupedPublicationError(
                "la fermeture durable ne peut pas être vérifiée: "
                + "; ".join(closure.issues)
            )
        _require_work_package(command, closure.plan.work_package_ref)
        return GitHubResearchLoveCycleClosureVerification(
            schema=CLOSURE_VERIFICATION_SCHEMA,
            command_ref=command.command_ref,
            scheduler_task_ref=execution_context.task_ref,
            work_package_ref=closure.plan.work_package_ref,
            closure_plan_digest=closure.plan.plan_digest,
            closure_revision_ref=closure.receipt.closure_revision_ref,
            publication_evidence_object_ref=(
                closure.receipt.evidence_object_ref
            ),
            verified_at=execution_context.started_at,
        )


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFullGroupedSchedulerBootstrap:
    """Catalogue explicite des dix capacités du cycle groupé complet."""

    catalog: SchedulerHandlerCatalog
    factory: SchedulerHandlerFactory = field(repr=False, compare=False)
    handler_refs: tuple[str, ...]
    capability_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        bindings = self.catalog.snapshot()
        if tuple(binding.handler_ref for binding in bindings) != self.handler_refs:
            raise GitHubResearchLoveGroupedPublicationError(
                "handler_refs diverge du catalogue complet"
            )
        if tuple(binding.key.capability_ref for binding in bindings) != (
            self.capability_refs
        ):
            raise GitHubResearchLoveGroupedPublicationError(
                "capability_refs diverge du catalogue complet"
            )
        if len(bindings) != 10:
            raise GitHubResearchLoveGroupedPublicationError(
                "le cycle groupé complet doit cataloguer dix handlers"
            )


def build_github_research_love_full_grouped_scheduler_bootstrap(
    first_visit_input_provider: GitHubResearchLoveFirstVisitInputProvider,
    grouped_input_provider: GitHubResearchLoveGroupedInputProvider,
    downstream_input_provider: GitHubResearchLoveGroupedDownstreamInputProvider,
    publication_input_provider: GitHubResearchLoveGroupedPublicationInputProvider,
) -> GitHubResearchLoveFullGroupedSchedulerBootstrap:
    """Assemble les dix handlers sans auto-inscription ni Scheduler parallèle."""

    _provider(publication_input_provider)
    # Valide aussi les trois fournisseurs amont avec leur bootstrap installé.
    upstream: GitHubResearchLoveCompleteGroupedSchedulerBootstrap = (
        build_github_research_love_complete_grouped_scheduler_bootstrap(
            first_visit_input_provider,
            grouped_input_provider,
            downstream_input_provider,
        )
    )
    if len(upstream.handler_refs) != 7:
        raise GitHubResearchLoveGroupedPublicationError(
            "le bootstrap amont doit fournir sept handlers"
        )

    handler_types = (
        GitHubResearchLovePrepareFirstVisitHandler,
        GitHubResearchLoveExecuteFirstSpecialistHandler,
        GitHubResearchLoveExecuteSecondSpecialistHandler,
        GitHubResearchLovePersistProjectPairHandler,
        GitHubResearchLoveRecallTwoAnalysesHandler,
        GitHubResearchLoveSynthesizeLiaisonHandler,
        GitHubResearchLoveBuildFinalDeliverableHandler,
        GitHubResearchLovePreparePublicationHandler,
        GitHubResearchLovePublishRemoteAndCloseHandler,
        GitHubResearchLoveVerifyClosedCycleHandler,
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
        RECALL_TWO_ANALYSES_HANDLER_REF: (
            lambda _binding, _ticket: GitHubResearchLoveRecallTwoAnalysesHandler(
                downstream_input_provider
            )
        ),
        SYNTHESIZE_LIAISON_HANDLER_REF: (
            lambda _binding, _ticket: GitHubResearchLoveSynthesizeLiaisonHandler(
                downstream_input_provider
            )
        ),
        BUILD_FINAL_DELIVERABLE_HANDLER_REF: (
            lambda _binding, _ticket: GitHubResearchLoveBuildFinalDeliverableHandler(
                downstream_input_provider
            )
        ),
        PREPARE_PUBLICATION_HANDLER_REF: (
            lambda _binding, _ticket: GitHubResearchLovePreparePublicationHandler(
                publication_input_provider
            )
        ),
        PUBLISH_REMOTE_HANDLER_REF: (
            lambda _binding, _ticket: GitHubResearchLovePublishRemoteAndCloseHandler(
                publication_input_provider
            )
        ),
        CLOSE_CYCLE_HANDLER_REF: (
            lambda _binding, _ticket: GitHubResearchLoveVerifyClosedCycleHandler(
                publication_input_provider
            )
        ),
    }
    factory = ExplicitSchedulerHandlerFactory(builders)
    bindings = catalog.snapshot()
    return GitHubResearchLoveFullGroupedSchedulerBootstrap(
        catalog=catalog,
        factory=factory,
        handler_refs=tuple(binding.handler_ref for binding in bindings),
        capability_refs=tuple(binding.key.capability_ref for binding in bindings),
    )


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
        raise GitHubResearchLoveGroupedPublicationError(
            "le contexte appartient à une autre commande"
        )
    expected = grouped_stage_task_ref(command.command_ref, stage)
    if context.task_ref != expected:
        raise GitHubResearchLoveGroupedPublicationError(
            f"le handler {stage} a reçu une autre tâche"
        )
    return context


def _require_work_package(
    command: GitHubResearchSchedulerCommand,
    work_package_ref: str,
) -> None:
    if work_package_ref != command.research.work_package_ref:
        raise GitHubResearchLoveGroupedPublicationError(
            "le résultat appartient à un autre paquet de recherche"
        )


def _provider(
    value: GitHubResearchLoveGroupedPublicationInputProvider,
) -> GitHubResearchLoveGroupedPublicationInputProvider:
    for name in (
        "load_publication_command",
        "load_publication_authorization",
        "load_cycle_closure_result",
    ):
        if not callable(getattr(value, name, None)):
            raise TypeError(f"publication_input_provider doit exposer {name}")
    return value


__all__ = (
    "CLOSE_CYCLE_CAPABILITY_REF",
    "CLOSE_CYCLE_HANDLER_REF",
    "CLOSURE_VERIFICATION_SCHEMA",
    "PUBLISHED_CLOSED_SCHEMA",
    "PREPARE_PUBLICATION_CAPABILITY_REF",
    "PREPARE_PUBLICATION_HANDLER_REF",
    "PUBLISH_REMOTE_CAPABILITY_REF",
    "PUBLISH_REMOTE_HANDLER_REF",
    "ExplicitGitHubResearchLoveGroupedPublicationInputProvider",
    "GitHubResearchLoveCycleClosureVerification",
    "GitHubResearchLoveFullGroupedSchedulerBootstrap",
    "GitHubResearchLoveGroupedPublicationError",
    "GitHubResearchLoveGroupedPublicationInputProvider",
    "GitHubResearchLovePreparePublicationHandler",
    "GitHubResearchLovePublicationAuthorization",
    "GitHubResearchLovePublishRemoteAndCloseHandler",
    "GitHubResearchLovePublishedClosedResult",
    "GitHubResearchLoveVerifyClosedCycleHandler",
    "build_github_research_love_full_grouped_scheduler_bootstrap",
)
