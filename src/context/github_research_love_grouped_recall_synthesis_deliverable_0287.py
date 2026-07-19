"""Handlers groupés de rappel, synthèse et livrable final d'une recherche amour.

Cette unité adapte trois compositions métier existantes au catalogue explicite
 du Scheduler. Elle n'implémente ni nouveau moteur de rappel, ni nouvelle
synthèse, ni nouveau store SQL. Les entrées sont réhydratées par un port injecté
et chaque handler reste borné à la capacité choisie par le Scheduler canonique.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from context.github_research_love_final_deliverable_sql_0287 import (
    GitHubResearchLoveFinalDeliverableCommand,
    GitHubResearchLoveFinalDeliverableResult,
    persist_github_research_love_final_deliverable,
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
from context.github_research_love_liaison_synthesis_0287 import (
    GitHubResearchLoveLiaisonSynthesisCommand,
    GitHubResearchLoveLiaisonSynthesisResult,
    build_github_research_love_liaison_synthesis,
)
from context.github_research_love_scheduler_bootstrap_0287 import (
    GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_HANDLER_REF,
    GitHubResearchLoveFirstVisitInputProvider,
    GitHubResearchLovePrepareFirstVisitHandler,
)
from context.github_research_love_two_analysis_recall_0287 import (
    GitHubResearchLoveTwoAnalysisRecallCommand,
    GitHubResearchLoveTwoAnalysisRecallResult,
    recall_github_research_love_analyses,
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

RECALL_TWO_ANALYSES_CAPABILITY_REF = (
    "capability:github-research.love.recall-two-analyses.v1"
)
SYNTHESIZE_LIAISON_CAPABILITY_REF = (
    "capability:github-research.love.synthesize-liaison.v1"
)
BUILD_FINAL_DELIVERABLE_CAPABILITY_REF = (
    "capability:github-research.love.build-final-deliverable.v1"
)

RECALL_TWO_ANALYSES_HANDLER_REF = (
    "handler:github-research-love-recall-two-analyses-v1"
)
SYNTHESIZE_LIAISON_HANDLER_REF = (
    "handler:github-research-love-synthesize-liaison-v1"
)
BUILD_FINAL_DELIVERABLE_HANDLER_REF = (
    "handler:github-research-love-build-final-deliverable-v1"
)


class GitHubResearchLoveGroupedDownstreamError(RuntimeError):
    """Erreur de corrélation ou d'exécution des trois capacités locales."""


class GitHubResearchLoveGroupedDownstreamInputProvider(Protocol):
    """Réhydrate les commandes typées sans choisir la tâche suivante."""

    def load_recall_command(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
    ) -> GitHubResearchLoveTwoAnalysisRecallCommand: ...

    def load_synthesis_command(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
    ) -> GitHubResearchLoveLiaisonSynthesisCommand: ...

    def load_final_deliverable_command(
        self,
        *,
        command: GitHubResearchSchedulerCommand,
        execution_context: SchedulerHandlerExecutionContext,
    ) -> GitHubResearchLoveFinalDeliverableCommand: ...


class GitHubResearchLoveRecallTwoAnalysesHandler(
    SchedulerHandler[
        GitHubResearchSchedulerCommand,
        GitHubResearchLoveTwoAnalysisRecallResult,
    ]
):
    """Rappelle exactement les deux projections puis réhydrate depuis SQL."""

    HANDLER_REF = RECALL_TWO_ANALYSES_HANDLER_REF
    CAPABILITY_REF = RECALL_TWO_ANALYSES_CAPABILITY_REF
    COMMAND_TYPE = GitHubResearchSchedulerCommand
    RESULT_TYPE = GitHubResearchLoveTwoAnalysisRecallResult
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.IDEMPOTENT,
        timeout_policy_ref="timeout-policy:github-love-recall-pair-v1",
        retry_policy_ref="retry-policy:github-love-recall-pair-v1",
        resource_profile_ref="resource-profile:sql-openvino-qdrant-read-v1",
        laboratory_compatibility=("laboratory-kind:love-studies",),
    )
    INFORMATION = HandlerInformation(
        title="Rappel hybride des deux analyses amour",
        summary=(
            "Produit une requête E5 query, rappelle deux références Qdrant et "
            "réhydrate les corps autoritatifs depuis PostgreSQL."
        ),
    )

    def __init__(
        self,
        provider: GitHubResearchLoveGroupedDownstreamInputProvider,
    ) -> None:
        self._provider = _provider(provider)

    async def execute(
        self,
        command: GitHubResearchSchedulerCommand,
        context: object,
    ) -> GitHubResearchLoveTwoAnalysisRecallResult:
        execution_context = _execution_context(
            command,
            context,
            "recall-two-analyses",
        )
        recall_command = self._provider.load_recall_command(
            command=command,
            execution_context=execution_context,
        )
        if not isinstance(
            recall_command,
            GitHubResearchLoveTwoAnalysisRecallCommand,
        ):
            raise TypeError(
                "load_recall_command doit retourner la commande de rappel typée"
            )
        result = await recall_github_research_love_analyses(recall_command)
        if not result.valid or result.status != "recalled":
            raise GitHubResearchLoveGroupedDownstreamError(
                "le rappel des deux analyses a échoué: " + "; ".join(result.issues)
            )
        _require_work_package(command, result.plan.work_package_ref)
        return result


class GitHubResearchLoveSynthesizeLiaisonHandler(
    SchedulerHandler[
        GitHubResearchSchedulerCommand,
        GitHubResearchLoveLiaisonSynthesisResult,
    ]
):
    """Construit une synthèse distincte depuis deux analyses SQL réhydratées."""

    HANDLER_REF = SYNTHESIZE_LIAISON_HANDLER_REF
    CAPABILITY_REF = SYNTHESIZE_LIAISON_CAPABILITY_REF
    COMMAND_TYPE = GitHubResearchSchedulerCommand
    RESULT_TYPE = GitHubResearchLoveLiaisonSynthesisResult
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.IDEMPOTENT,
        timeout_policy_ref="timeout-policy:github-love-liaison-synthesis-v1",
        retry_policy_ref="retry-policy:github-love-liaison-synthesis-v1",
        resource_profile_ref="resource-profile:cpu-memory-synthesis-v1",
        laboratory_compatibility=("laboratory-kind:love-studies",),
    )
    INFORMATION = HandlerInformation(
        title="Synthèse de liaison des deux analyses amour",
        summary=(
            "Conserve les deux analyses distinctes et construit une synthèse "
            "locale avec convergences, contradictions et incertitudes."
        ),
    )

    def __init__(
        self,
        provider: GitHubResearchLoveGroupedDownstreamInputProvider,
    ) -> None:
        self._provider = _provider(provider)

    async def execute(
        self,
        command: GitHubResearchSchedulerCommand,
        context: object,
    ) -> GitHubResearchLoveLiaisonSynthesisResult:
        execution_context = _execution_context(
            command,
            context,
            "synthesize-liaison",
        )
        synthesis_command = self._provider.load_synthesis_command(
            command=command,
            execution_context=execution_context,
        )
        if not isinstance(
            synthesis_command,
            GitHubResearchLoveLiaisonSynthesisCommand,
        ):
            raise TypeError(
                "load_synthesis_command doit retourner la commande de synthèse typée"
            )
        result = build_github_research_love_liaison_synthesis(
            synthesis_command
        )
        if not result.valid or result.status != "synthesized":
            raise GitHubResearchLoveGroupedDownstreamError(
                "la synthèse de liaison a échoué: " + "; ".join(result.issues)
            )
        _require_work_package(command, result.plan.work_package_ref)
        return result


class GitHubResearchLoveBuildFinalDeliverableHandler(
    SchedulerHandler[
        GitHubResearchSchedulerCommand,
        GitHubResearchLoveFinalDeliverableResult,
    ]
):
    """Construit et persiste le livrable local, sans publication distante."""

    HANDLER_REF = BUILD_FINAL_DELIVERABLE_HANDLER_REF
    CAPABILITY_REF = BUILD_FINAL_DELIVERABLE_CAPABILITY_REF
    COMMAND_TYPE = GitHubResearchSchedulerCommand
    RESULT_TYPE = GitHubResearchLoveFinalDeliverableResult
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.IDEMPOTENT,
        timeout_policy_ref="timeout-policy:github-love-final-deliverable-v1",
        retry_policy_ref="retry-policy:github-love-final-deliverable-v1",
        resource_profile_ref="resource-profile:sql-final-deliverable-v1",
        laboratory_compatibility=("laboratory-kind:love-studies",),
    )
    INFORMATION = HandlerInformation(
        title="Construction du livrable final local",
        summary=(
            "Construit le paquet final et l'enregistre dans PostgreSQL avant "
            "toute préparation ou mutation GitHub."
        ),
    )

    def __init__(
        self,
        provider: GitHubResearchLoveGroupedDownstreamInputProvider,
    ) -> None:
        self._provider = _provider(provider)

    async def execute(
        self,
        command: GitHubResearchSchedulerCommand,
        context: object,
    ) -> GitHubResearchLoveFinalDeliverableResult:
        execution_context = _execution_context(
            command,
            context,
            "build-final-deliverable",
        )
        final_command = self._provider.load_final_deliverable_command(
            command=command,
            execution_context=execution_context,
        )
        if not isinstance(
            final_command,
            GitHubResearchLoveFinalDeliverableCommand,
        ):
            raise TypeError(
                "load_final_deliverable_command doit retourner la commande finale typée"
            )
        result = persist_github_research_love_final_deliverable(final_command)
        if (
            not result.valid
            or result.status != "persisted"
            or result.plan is None
            or result.receipt is None
            or not result.receipt.readback_verified
        ):
            raise GitHubResearchLoveGroupedDownstreamError(
                "le livrable final n'est pas durablement persisté: "
                + "; ".join(result.issues)
            )
        _require_work_package(command, result.plan.work_package_ref)
        return result


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveCompleteGroupedSchedulerBootstrap:
    """Catalogue explicite des sept capacités locales maintenant disponibles."""

    catalog: SchedulerHandlerCatalog
    factory: SchedulerHandlerFactory = field(repr=False, compare=False)
    handler_refs: tuple[str, ...]
    capability_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        bindings = self.catalog.snapshot()
        if tuple(binding.handler_ref for binding in bindings) != self.handler_refs:
            raise GitHubResearchLoveGroupedDownstreamError(
                "handler_refs diverge du catalogue complet"
            )
        if tuple(binding.key.capability_ref for binding in bindings) != (
            self.capability_refs
        ):
            raise GitHubResearchLoveGroupedDownstreamError(
                "capability_refs diverge du catalogue complet"
            )


def build_github_research_love_complete_grouped_scheduler_bootstrap(
    first_visit_input_provider: GitHubResearchLoveFirstVisitInputProvider,
    grouped_input_provider: GitHubResearchLoveGroupedInputProvider,
    downstream_input_provider: GitHubResearchLoveGroupedDownstreamInputProvider,
) -> GitHubResearchLoveCompleteGroupedSchedulerBootstrap:
    """Assemble les sept handlers sans auto-inscription ni Scheduler parallèle."""

    _grouped_provider(grouped_input_provider)
    _provider(downstream_input_provider)
    handler_types = (
        GitHubResearchLovePrepareFirstVisitHandler,
        GitHubResearchLoveExecuteFirstSpecialistHandler,
        GitHubResearchLoveExecuteSecondSpecialistHandler,
        GitHubResearchLovePersistProjectPairHandler,
        GitHubResearchLoveRecallTwoAnalysesHandler,
        GitHubResearchLoveSynthesizeLiaisonHandler,
        GitHubResearchLoveBuildFinalDeliverableHandler,
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
    }
    factory = ExplicitSchedulerHandlerFactory(builders)
    bindings = catalog.snapshot()
    return GitHubResearchLoveCompleteGroupedSchedulerBootstrap(
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
        raise GitHubResearchLoveGroupedDownstreamError(
            "le contexte appartient à une autre commande"
        )
    expected = grouped_stage_task_ref(command.command_ref, stage)
    if context.task_ref != expected:
        raise GitHubResearchLoveGroupedDownstreamError(
            f"le handler {stage} a reçu une autre tâche"
        )
    return context


def _require_work_package(
    command: GitHubResearchSchedulerCommand,
    work_package_ref: str,
) -> None:
    if work_package_ref != command.research.work_package_ref:
        raise GitHubResearchLoveGroupedDownstreamError(
            "le résultat appartient à un autre paquet de recherche"
        )


def _provider(
    value: GitHubResearchLoveGroupedDownstreamInputProvider,
) -> GitHubResearchLoveGroupedDownstreamInputProvider:
    for name in (
        "load_recall_command",
        "load_synthesis_command",
        "load_final_deliverable_command",
    ):
        if not callable(getattr(value, name, None)):
            raise TypeError(f"downstream_input_provider doit exposer {name}")
    return value


def _grouped_provider(
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


__all__ = (
    "BUILD_FINAL_DELIVERABLE_CAPABILITY_REF",
    "BUILD_FINAL_DELIVERABLE_HANDLER_REF",
    "RECALL_TWO_ANALYSES_CAPABILITY_REF",
    "RECALL_TWO_ANALYSES_HANDLER_REF",
    "SYNTHESIZE_LIAISON_CAPABILITY_REF",
    "SYNTHESIZE_LIAISON_HANDLER_REF",
    "GitHubResearchLoveBuildFinalDeliverableHandler",
    "GitHubResearchLoveCompleteGroupedSchedulerBootstrap",
    "GitHubResearchLoveGroupedDownstreamError",
    "GitHubResearchLoveGroupedDownstreamInputProvider",
    "GitHubResearchLoveRecallTwoAnalysesHandler",
    "GitHubResearchLoveSynthesizeLiaisonHandler",
    "build_github_research_love_complete_grouped_scheduler_bootstrap",
)
