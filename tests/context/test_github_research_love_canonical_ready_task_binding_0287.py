from __future__ import annotations

from dataclasses import dataclass

import pytest

from context.github_research_love_canonical_ready_task_binding_0287 import (
    GitHubResearchLoveCanonicalReadyTaskBindingError,
    GitHubResearchLoveReadyTaskAdmission,
)
from kernel.scheduler_task_admission import (
    SchedulerAdmissionStatus,
    SchedulerTaskAdmissionCandidate,
    SchedulerTaskAdmissionDecision,
    SchedulerTaskAdmissionPlan,
)
from kernel.scheduler_task_model import SchedulerTaskState


@dataclass(frozen=True)
class _TaskView:
    task_ref: str
    command_ref: str
    state: SchedulerTaskState


@dataclass(frozen=True)
class _ReservationView:
    task_ref: str


def _unvalidated_instance(kind: type[object], **attributes: object) -> object:
    value = object.__new__(kind)
    for name, item in attributes.items():
        object.__setattr__(value, name, item)
    return value


def _candidate(task: object) -> SchedulerTaskAdmissionCandidate:
    return _unvalidated_instance(
        SchedulerTaskAdmissionCandidate,
        task=task,
    )  # type: ignore[return-value]


def _decision(
    *,
    task_ref: str,
    status: SchedulerAdmissionStatus,
    reservation: object | None,
) -> SchedulerTaskAdmissionDecision:
    return _unvalidated_instance(
        SchedulerTaskAdmissionDecision,
        task_ref=task_ref,
        status=status,
        reservation=reservation,
    )  # type: ignore[return-value]


def _plan(*decisions: SchedulerTaskAdmissionDecision) -> SchedulerTaskAdmissionPlan:
    return _unvalidated_instance(
        SchedulerTaskAdmissionPlan,
        decisions=tuple(decisions),
    )  # type: ignore[return-value]


def test_admission_accepte_la_decision_ready_deja_prise() -> None:
    task = _TaskView(
        task_ref="scheduler-task:ready-1",
        command_ref="scheduler-command:github-research:command-1",
        state=SchedulerTaskState.READY,
    )
    admission = GitHubResearchLoveReadyTaskAdmission(
        candidate=_candidate(task),
        plan=_plan(
            _decision(
                task_ref=task.task_ref,
                status=SchedulerAdmissionStatus.ADMITTED,
                reservation=_ReservationView(task_ref=task.task_ref),
            )
        ),
        evidence_refs=("evidence:admission-ready-1",),
    )

    assert admission.candidate.task is task
    assert admission.evidence_refs == ("evidence:admission-ready-1",)


def test_admission_refuse_de_planifier_implicitement_une_tache_non_admise() -> None:
    task = _TaskView(
        task_ref="scheduler-task:ready-2",
        command_ref="scheduler-command:github-research:command-2",
        state=SchedulerTaskState.READY,
    )

    with pytest.raises(
        GitHubResearchLoveCanonicalReadyTaskBindingError,
        match="déjà être admise",
    ):
        GitHubResearchLoveReadyTaskAdmission(
            candidate=_candidate(task),
            plan=_plan(
                _decision(
                    task_ref=task.task_ref,
                    status=SchedulerAdmissionStatus.DEFERRED,
                    reservation=None,
                )
            ),
        )
