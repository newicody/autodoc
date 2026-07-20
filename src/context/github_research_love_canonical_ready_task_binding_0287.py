"""Réhydrate une tâche déjà décidée sans créer de routeur parallèle.

Le Scheduler canonique choisit la tâche ``ready``. Son service de lancement résout
ensuite le ``SchedulerHandlerBinding`` dans le catalogue des dix handlers. Cette
frontière ne reproduit aucune de ces décisions : elle relit uniquement la
commande et l'admission durable de la tâche reçue, puis injecte le bootstrap déjà
assemblé dans le runner transactionnel r16-r65.

Aucun Scheduler, Dispatcher, EventBus, registre de capacités, backend, thread,
processus, stockage JSON ou file JSONL n'est créé ici.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from context.github_research_love_grouped_publication_closure_0287 import (
    GitHubResearchLoveFullGroupedSchedulerBootstrap,
)
from context.github_research_love_transactional_step_runner_0287 import (
    GitHubResearchLoveReadyTaskExecutionInput,
)
from context.github_research_scheduler_command_0287 import (
    GitHubResearchSchedulerCommand,
    GitHubResearchSchedulerCommandStore,
)
from kernel.scheduler_canonical_continuation import SchedulerDurableGraphSnapshot
from kernel.scheduler_handler_contract import HandlerInformationSink
from kernel.scheduler_handler_execution import (
    SchedulerCancellationSignal,
    SchedulerHandlerCloser,
    SchedulerHandlerFailureClassifier,
    SchedulerHandlerResultProjector,
)
from kernel.scheduler_task_admission import (
    SchedulerAdmissionStatus,
    SchedulerTaskAdmissionCandidate,
    SchedulerTaskAdmissionPlan,
)
from kernel.scheduler_task_model import SchedulerTaskState


CANONICAL_READY_TASK_BINDING_SCHEMA = (
    "missipy.github.research_love_canonical_ready_task_binding.v1"
)


class GitHubResearchLoveCanonicalReadyTaskBindingError(RuntimeError):
    """Échec fermé d'une réhydratation divergente de l'autorité durable."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveReadyTaskAdmission:
    """Candidat et plan déjà décidés pour la tâche reçue du Scheduler."""

    candidate: SchedulerTaskAdmissionCandidate = field(repr=False)
    plan: SchedulerTaskAdmissionPlan = field(repr=False)
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.candidate, SchedulerTaskAdmissionCandidate):
            raise TypeError("candidate doit être SchedulerTaskAdmissionCandidate")
        if not isinstance(self.plan, SchedulerTaskAdmissionPlan):
            raise TypeError("plan doit être SchedulerTaskAdmissionPlan")
        task = self.candidate.task
        if task.state is not SchedulerTaskState.READY:
            raise GitHubResearchLoveCanonicalReadyTaskBindingError(
                "le candidat durable doit porter la tâche ready déjà choisie"
            )
        decisions = tuple(
            decision
            for decision in self.plan.decisions
            if decision.task_ref == task.task_ref
        )
        if len(decisions) != 1:
            raise GitHubResearchLoveCanonicalReadyTaskBindingError(
                "le plan doit contenir une décision unique pour la tâche reçue"
            )
        decision = decisions[0]
        if decision.status is not SchedulerAdmissionStatus.ADMITTED:
            raise GitHubResearchLoveCanonicalReadyTaskBindingError(
                "la tâche reçue doit déjà être admise par le Scheduler"
            )
        if decision.reservation is None:
            raise GitHubResearchLoveCanonicalReadyTaskBindingError(
                "l'admission durable doit porter sa réservation"
            )
        if decision.reservation.task_ref != task.task_ref:
            raise GitHubResearchLoveCanonicalReadyTaskBindingError(
                "la réservation appartient à une autre tâche"
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _unique_typed_refs("evidence_refs", self.evidence_refs),
        )


@runtime_checkable
class GitHubResearchLoveReadyTaskAdmissionReader(Protocol):
    """Relit une admission existante; il ne planifie et ne réserve rien."""

    def load_ready_task_admission(
        self,
        *,
        snapshot: SchedulerDurableGraphSnapshot,
        task_ref: str,
        command: GitHubResearchSchedulerCommand,
    ) -> GitHubResearchLoveReadyTaskAdmission: ...


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveCanonicalReadyTaskExecutionInputProvider:
    """Construit l'entrée r16-r65 depuis une tâche déjà choisie et admise."""

    command_store: GitHubResearchSchedulerCommandStore = field(
        repr=False,
        compare=False,
    )
    admission_reader: GitHubResearchLoveReadyTaskAdmissionReader = field(
        repr=False,
        compare=False,
    )
    bootstrap: GitHubResearchLoveFullGroupedSchedulerBootstrap = field(
        repr=False,
        compare=False,
    )
    information_sink: HandlerInformationSink = field(repr=False, compare=False)
    result_projector: SchedulerHandlerResultProjector[object] = field(
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
    evidence_refs: tuple[str, ...] = ()
    schema: str = CANONICAL_READY_TASK_BINDING_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != CANONICAL_READY_TASK_BINDING_SCHEMA:
            raise GitHubResearchLoveCanonicalReadyTaskBindingError(
                "schéma de binding de tâche ready non pris en charge"
            )
        if not isinstance(self.command_store, GitHubResearchSchedulerCommandStore):
            raise TypeError("command_store doit implémenter le port PostgreSQL")
        if not isinstance(
            self.admission_reader,
            GitHubResearchLoveReadyTaskAdmissionReader,
        ):
            raise TypeError("admission_reader doit implémenter le port de lecture")
        if not isinstance(
            self.bootstrap,
            GitHubResearchLoveFullGroupedSchedulerBootstrap,
        ):
            raise TypeError("bootstrap doit être le bootstrap groupé complet")
        if len(self.bootstrap.handler_refs) != 10:
            raise GitHubResearchLoveCanonicalReadyTaskBindingError(
                "le bootstrap doit conserver exactement dix handlers"
            )
        if not callable(getattr(self.information_sink, "publish", None)):
            raise TypeError("information_sink doit exposer publish")
        if not isinstance(self.result_projector, SchedulerHandlerResultProjector):
            raise TypeError("result_projector doit implémenter le port attendu")
        if not isinstance(
            self.failure_classifier,
            SchedulerHandlerFailureClassifier,
        ):
            raise TypeError("failure_classifier doit implémenter le port attendu")
        if not isinstance(self.closer, SchedulerHandlerCloser):
            raise TypeError("closer doit implémenter le port attendu")
        if self.cancellation_signal is not None and not isinstance(
            self.cancellation_signal,
            SchedulerCancellationSignal,
        ):
            raise TypeError("cancellation_signal doit implémenter le port attendu")
        if not callable(self.utc_now):
            raise TypeError("utc_now doit être callable")
        object.__setattr__(
            self,
            "evidence_refs",
            _unique_typed_refs("evidence_refs", self.evidence_refs),
        )

    def load_ready_task_execution_input(
        self,
        *,
        snapshot: SchedulerDurableGraphSnapshot,
        task_ref: str,
    ) -> GitHubResearchLoveReadyTaskExecutionInput:
        """Réhydrate les ports d'une tâche que le cycle a déjà sélectionnée."""

        task = snapshot.graph.task(task_ref)
        if task.state is not SchedulerTaskState.READY:
            raise GitHubResearchLoveCanonicalReadyTaskBindingError(
                "le binding n'accepte qu'une tâche ready déjà sélectionnée"
            )
        command = self.command_store.get_command(task.command_ref)
        if not isinstance(command, GitHubResearchSchedulerCommand):
            raise GitHubResearchLoveCanonicalReadyTaskBindingError(
                "la commande typée de la tâche est absente de PostgreSQL"
            )
        admission = self.admission_reader.load_ready_task_admission(
            snapshot=snapshot,
            task_ref=task_ref,
            command=command,
        )
        if not isinstance(admission, GitHubResearchLoveReadyTaskAdmission):
            raise TypeError(
                "admission_reader doit retourner le contrat typé r16-r66"
            )
        if admission.candidate.task != task:
            raise GitHubResearchLoveCanonicalReadyTaskBindingError(
                "le candidat relu diverge de la tâche durable sélectionnée"
            )
        return GitHubResearchLoveReadyTaskExecutionInput(
            command=command,
            candidate=admission.candidate,
            plan=admission.plan,
            catalog=self.bootstrap.catalog,
            handler_factory=self.bootstrap.factory,
            information_sink=self.information_sink,
            result_projector=self.result_projector,
            failure_classifier=self.failure_classifier,
            closer=self.closer,
            utc_now=self.utc_now,
            cancellation_signal=self.cancellation_signal,
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Projection de diagnostic de frontière, jamais état métier interne."""

        return MappingProxyType(
            {
                "schema": self.schema,
                "handler_count": len(self.bootstrap.handler_refs),
                "evidence_refs": self.evidence_refs,
                "ready_task_already_selected": True,
                "admission_already_decided": True,
                "handler_resolution_delegated_to_launch_service": True,
                "bootstrap_catalog_reused": True,
                "bootstrap_factory_reused": True,
                "scheduler_created": False,
                "capability_router_created": False,
                "dispatcher_created": False,
                "eventbus_created": False,
                "backend_opened": False,
            }
        )


def build_github_research_love_canonical_ready_task_execution_input_provider(
    *,
    command_store: GitHubResearchSchedulerCommandStore,
    admission_reader: GitHubResearchLoveReadyTaskAdmissionReader,
    bootstrap: GitHubResearchLoveFullGroupedSchedulerBootstrap,
    information_sink: HandlerInformationSink,
    result_projector: SchedulerHandlerResultProjector[object],
    failure_classifier: SchedulerHandlerFailureClassifier,
    closer: SchedulerHandlerCloser,
    utc_now: Callable[[], str],
    cancellation_signal: SchedulerCancellationSignal | None = None,
    evidence_refs: tuple[str, ...] = (
        "evidence:github-research-love-canonical-ready-task-binding-r16-r66",
        "evidence:ready-task-selected-by-canonical-scheduler",
        "evidence:ten-handler-bootstrap-reused-without-router",
    ),
    **_available: object,
) -> GitHubResearchLoveCanonicalReadyTaskExecutionInputProvider:
    """Fabrique explicite destinée à la composition installée suivante."""

    return GitHubResearchLoveCanonicalReadyTaskExecutionInputProvider(
        command_store=command_store,
        admission_reader=admission_reader,
        bootstrap=bootstrap,
        information_sink=information_sink,
        result_projector=result_projector,
        failure_classifier=failure_classifier,
        closer=closer,
        utc_now=utc_now,
        cancellation_signal=cancellation_signal,
        evidence_refs=evidence_refs,
    )


def _unique_typed_refs(name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in tuple(values):
        if (
            not isinstance(value, str)
            or ":" not in value
            or any(character.isspace() for character in value)
        ):
            raise GitHubResearchLoveCanonicalReadyTaskBindingError(
                f"{name} doit contenir des références typées"
            )
        if value not in result:
            result.append(value)
    return tuple(result)


__all__ = (
    "CANONICAL_READY_TASK_BINDING_SCHEMA",
    "GitHubResearchLoveCanonicalReadyTaskBindingError",
    "GitHubResearchLoveCanonicalReadyTaskExecutionInputProvider",
    "GitHubResearchLoveReadyTaskAdmission",
    "GitHubResearchLoveReadyTaskAdmissionReader",
    "build_github_research_love_canonical_ready_task_execution_input_provider",
)
