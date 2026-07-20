"""Pipeline transactionnel d'une tâche ``ready`` du Scheduler canonique.

Le runner ne choisit ni la tâche, ni le handler, ni une politique de reprise.
Un fournisseur typé réhydrate la commande, le candidat, le plan d'admission et
les ports métier déjà préparés. Le runner applique ensuite la chaîne canonique
existante : lancement SQL, création/armement du handler, exécution bornée et
commit terminal SQL.

Les transactions de lancement et de fin sont injectées par la fondation r16-r64
et ne peuvent pas être remplacées par le fournisseur métier.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from kernel.scheduler_canonical_continuation import SchedulerDurableGraphSnapshot
from kernel.scheduler_handler_execution import (
    SchedulerCancellationSignal,
    SchedulerHandlerCloser,
    SchedulerHandlerExecutionOutcome,
    SchedulerHandlerExecutionService,
    SchedulerHandlerFailureClassifier,
    SchedulerHandlerResultProjector,
)
from kernel.scheduler_handler_execution_completion import (
    SchedulerHandlerExecutionCommit,
    SchedulerHandlerExecutionTransaction,
)
from kernel.scheduler_handler_instance_lifecycle import (
    SchedulerHandlerFactory,
    SchedulerHandlerInstanceLifecycleService,
)
from kernel.scheduler_handler_contract import HandlerInformationSink
from kernel.scheduler_handler_catalog import SchedulerHandlerCatalog
from kernel.scheduler_task_admission import (
    SchedulerTaskAdmissionCandidate,
    SchedulerTaskAdmissionPlan,
)
from kernel.scheduler_task_launch_preparation import (
    SchedulerTaskLaunchPreparationService,
    SchedulerTaskLaunchTransaction,
)
from kernel.scheduler_task_model import SchedulerTaskState

TRANSACTIONAL_STEP_RUNNER_VERSION = "0287.r16.r65"


class GitHubResearchLoveTransactionalStepRunnerError(RuntimeError):
    """Échec fermé du pipeline transactionnel d'une étape."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveReadyTaskExecutionInput:
    """Entrées déjà décidées et réhydratées pour une tâche précise."""

    command: object = field(repr=False, compare=False)
    candidate: SchedulerTaskAdmissionCandidate = field(repr=False)
    plan: SchedulerTaskAdmissionPlan = field(repr=False)
    catalog: SchedulerHandlerCatalog = field(repr=False, compare=False)
    handler_factory: SchedulerHandlerFactory = field(repr=False, compare=False)
    information_sink: HandlerInformationSink = field(repr=False, compare=False)
    result_projector: SchedulerHandlerResultProjector[Any] = field(
        repr=False,
        compare=False,
    )
    failure_classifier: SchedulerHandlerFailureClassifier = field(
        repr=False,
        compare=False,
    )
    closer: SchedulerHandlerCloser = field(repr=False, compare=False)
    utc_now: Callable[[], str] = field(repr=False, compare=False)
    cancellation_signal: SchedulerCancellationSignal | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if not callable(self.utc_now):
            raise TypeError("utc_now doit être callable")
        command_ref = getattr(self.command, "command_ref", "")
        if command_ref != self.candidate.task.command_ref:
            raise GitHubResearchLoveTransactionalStepRunnerError(
                "la commande et le candidat ne sont pas corrélés"
            )
        if not isinstance(self.catalog, SchedulerHandlerCatalog):
            raise TypeError("catalog doit être SchedulerHandlerCatalog")
        if not isinstance(self.handler_factory, SchedulerHandlerFactory):
            raise TypeError("handler_factory doit implémenter le port attendu")
        if not callable(getattr(self.information_sink, "publish", None)):
            raise TypeError("information_sink doit exposer publish")
        if not isinstance(self.result_projector, SchedulerHandlerResultProjector):
            raise TypeError("result_projector doit implémenter le port attendu")
        if not isinstance(self.failure_classifier, SchedulerHandlerFailureClassifier):
            raise TypeError("failure_classifier doit implémenter le port attendu")
        if not isinstance(self.closer, SchedulerHandlerCloser):
            raise TypeError("closer doit implémenter le port attendu")
        if self.cancellation_signal is not None and not isinstance(
            self.cancellation_signal,
            SchedulerCancellationSignal,
        ):
            raise TypeError("cancellation_signal doit implémenter le port attendu")


@runtime_checkable
class GitHubResearchLoveReadyTaskExecutionInputProvider(Protocol):
    """Réhydrate les objets d'une tâche déjà choisie par le Scheduler."""

    def load_ready_task_execution_input(
        self,
        *,
        snapshot: SchedulerDurableGraphSnapshot,
        task_ref: str,
    ) -> GitHubResearchLoveReadyTaskExecutionInput: ...


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveTransactionalStepCommit:
    """Trace locale reliant le lancement, l'outcome et la clôture durable."""

    task_ref: str
    launch_transaction_ref: str
    outcome_ref: str
    completion_transaction_ref: str
    released_at: str

    def __post_init__(self) -> None:
        _typed_ref("task_ref", self.task_ref, "scheduler-task:")
        _typed_ref(
            "launch_transaction_ref",
            self.launch_transaction_ref,
            "scheduler-launch-transaction:",
        )
        _typed_ref("outcome_ref", self.outcome_ref, "handler-outcome:")
        _typed_ref(
            "completion_transaction_ref",
            self.completion_transaction_ref,
            "scheduler-execution-transaction:",
        )
        _utc("released_at", self.released_at)


class GitHubResearchLoveTransactionalStepRunner:
    """Exécute une tâche ``ready`` sans prendre de décision d'orchestration."""

    def __init__(
        self,
        *,
        scheduler_ref: str,
        continuation_store: object,
        task_launch_transaction: SchedulerTaskLaunchTransaction,
        handler_execution_transaction: SchedulerHandlerExecutionTransaction,
        ready_task_input_provider: GitHubResearchLoveReadyTaskExecutionInputProvider,
        launch_service: SchedulerTaskLaunchPreparationService | None = None,
        lifecycle_service: SchedulerHandlerInstanceLifecycleService | None = None,
        execution_service: SchedulerHandlerExecutionService | None = None,
        **_unused: object,
    ) -> None:
        _typed_ref("scheduler_ref", scheduler_ref, "scheduler:")
        if not callable(getattr(continuation_store, "load_snapshot", None)):
            raise TypeError("continuation_store doit exposer load_snapshot")
        if not callable(getattr(task_launch_transaction, "commit_launch", None)):
            raise TypeError(
                "task_launch_transaction doit exposer commit_launch"
            )
        if not callable(
            getattr(handler_execution_transaction, "commit_outcome", None)
        ):
            raise TypeError(
                "handler_execution_transaction doit exposer commit_outcome"
            )
        if not callable(
            getattr(
                ready_task_input_provider,
                "load_ready_task_execution_input",
                None,
            )
        ):
            raise TypeError(
                "ready_task_input_provider doit exposer "
                "load_ready_task_execution_input"
            )
        self._scheduler_ref = scheduler_ref
        self._continuation_store = continuation_store
        self._task_launch_transaction = task_launch_transaction
        self._handler_execution_transaction = handler_execution_transaction
        self._ready_task_input_provider = ready_task_input_provider
        self._launch_service = launch_service or SchedulerTaskLaunchPreparationService()
        self._lifecycle_service = (
            lifecycle_service or SchedulerHandlerInstanceLifecycleService()
        )
        self._execution_service = execution_service or SchedulerHandlerExecutionService()
        self._last_commit: GitHubResearchLoveTransactionalStepCommit | None = None

    @property
    def last_commit(self) -> GitHubResearchLoveTransactionalStepCommit | None:
        return self._last_commit

    async def run_ready_task(
        self,
        *,
        snapshot: SchedulerDurableGraphSnapshot,
        task_ref: str,
    ) -> SchedulerHandlerExecutionOutcome[Any]:
        if snapshot.scheduler_ref != self._scheduler_ref:
            raise GitHubResearchLoveTransactionalStepRunnerError(
                "le snapshot appartient à un autre Scheduler"
            )
        task = snapshot.graph.task(task_ref)
        if task.state is not SchedulerTaskState.READY:
            raise GitHubResearchLoveTransactionalStepRunnerError(
                "le runner n'accepte qu'une tâche ready"
            )
        runtime_input = (
            self._ready_task_input_provider.load_ready_task_execution_input(
                snapshot=snapshot,
                task_ref=task_ref,
            )
        )
        if not isinstance(runtime_input, GitHubResearchLoveReadyTaskExecutionInput):
            raise TypeError("le provider doit retourner le contrat typé r16-r65")
        if runtime_input.candidate.task != task:
            raise GitHubResearchLoveTransactionalStepRunnerError(
                "le candidat réhydraté diverge de la tâche durable"
            )

        applied_at = runtime_input.utc_now()
        ticket = self._launch_service.apply(
            scheduler_ref=self._scheduler_ref,
            command=runtime_input.command,
            candidate=runtime_input.candidate,
            plan=runtime_input.plan,
            catalog=runtime_input.catalog,
            transaction=self._task_launch_transaction,
            applied_at=applied_at,
        )
        created = self._lifecycle_service.create(
            ticket=ticket,
            factory=runtime_input.handler_factory,
            information_sink=runtime_input.information_sink,
            created_at=runtime_input.utc_now(),
        )
        lease = self._lifecycle_service.start(
            created=created,
            information_sink=runtime_input.information_sink,
            started_at=runtime_input.utc_now(),
        )
        outcome = await self._execution_service.execute(
            lease=lease,
            result_projector=runtime_input.result_projector,
            failure_classifier=runtime_input.failure_classifier,
            closer=runtime_input.closer,
            information_sink=runtime_input.information_sink,
            utc_now=runtime_input.utc_now,
            cancellation_signal=runtime_input.cancellation_signal,
        )
        released_at = runtime_input.utc_now()
        completion = self._handler_execution_transaction.commit_outcome(
            outcome=outcome,
            released_at=released_at,
        )
        self._validate_completion(outcome, completion, task_ref)
        self._last_commit = GitHubResearchLoveTransactionalStepCommit(
            task_ref=task_ref,
            launch_transaction_ref=ticket.launch_commit.transaction_ref,
            outcome_ref=outcome.outcome_ref,
            completion_transaction_ref=completion.transaction_ref,
            released_at=released_at,
        )
        return outcome

    def _validate_completion(
        self,
        outcome: SchedulerHandlerExecutionOutcome[Any],
        completion: SchedulerHandlerExecutionCommit,
        task_ref: str,
    ) -> None:
        if not isinstance(completion, SchedulerHandlerExecutionCommit):
            raise GitHubResearchLoveTransactionalStepRunnerError(
                "la transaction terminale doit retourner le reçu typé"
            )
        if completion.scheduler_ref != self._scheduler_ref:
            raise GitHubResearchLoveTransactionalStepRunnerError(
                "le reçu terminal appartient à un autre Scheduler"
            )
        if completion.task_ref != task_ref:
            raise GitHubResearchLoveTransactionalStepRunnerError(
                "le reçu terminal appartient à une autre tâche"
            )
        if completion.outcome_ref != outcome.outcome_ref:
            raise GitHubResearchLoveTransactionalStepRunnerError(
                "le reçu terminal diverge de l'outcome exécuté"
            )


def build_github_research_love_transactional_step_runner(
    *,
    scheduler_ref: str,
    continuation_store: object,
    task_launch_transaction: SchedulerTaskLaunchTransaction,
    handler_execution_transaction: SchedulerHandlerExecutionTransaction,
    ready_task_input_provider: GitHubResearchLoveReadyTaskExecutionInputProvider,
    **available: object,
) -> GitHubResearchLoveTransactionalStepRunner:
    """Fabrique configurée r16-r65, liée aux transactions injectées r31/r33."""

    return GitHubResearchLoveTransactionalStepRunner(
        scheduler_ref=scheduler_ref,
        continuation_store=continuation_store,
        task_launch_transaction=task_launch_transaction,
        handler_execution_transaction=handler_execution_transaction,
        ready_task_input_provider=ready_task_input_provider,
        **available,
    )


def _typed_ref(name: str, value: object, prefix: str = "") -> None:
    if (
        not isinstance(value, str)
        or ":" not in value
        or any(character.isspace() for character in value)
    ):
        raise GitHubResearchLoveTransactionalStepRunnerError(
            f"{name} doit être une référence typée"
        )
    if prefix and not value.startswith(prefix):
        raise GitHubResearchLoveTransactionalStepRunnerError(
            f"{name} doit commencer par {prefix}"
        )


def _utc(name: str, value: object) -> None:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        raise GitHubResearchLoveTransactionalStepRunnerError(
            f"{name} doit être un horodatage UTC finissant par Z"
        )


__all__ = (
    "TRANSACTIONAL_STEP_RUNNER_VERSION",
    "GitHubResearchLoveReadyTaskExecutionInput",
    "GitHubResearchLoveReadyTaskExecutionInputProvider",
    "GitHubResearchLoveTransactionalStepCommit",
    "GitHubResearchLoveTransactionalStepRunner",
    "GitHubResearchLoveTransactionalStepRunnerError",
    "build_github_research_love_transactional_step_runner",
)
