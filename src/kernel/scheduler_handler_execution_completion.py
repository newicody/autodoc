"""Contrat transactionnel de clôture d'une exécution de handler Scheduler."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Protocol, runtime_checkable

from .scheduler_handler_execution import SchedulerHandlerExecutionOutcome

SCHEMA = "missipy.scheduler.handler_execution_commit.v1"


@dataclass(frozen=True, slots=True)
class SchedulerHandlerExecutionCommit:
    schema: str
    transaction_ref: str
    scheduler_ref: str
    command_ref: str
    task_ref: str
    attempt_ref: str
    reservation_ref: str
    outcome_ref: str
    task_state: str
    task_state_version: int
    released_at: str
    commit_digest: str

    @classmethod
    def create(cls, *, scheduler_ref: str, command_ref: str, task_ref: str,
               attempt_ref: str, reservation_ref: str, outcome_ref: str,
               task_state: str, task_state_version: int, released_at: str):
        parts = (scheduler_ref, command_ref, task_ref, attempt_ref, reservation_ref,
                 outcome_ref, task_state, str(task_state_version), released_at)
        h = hashlib.sha256()
        for value in parts:
            raw = value.encode()
            h.update(len(raw).to_bytes(8, "big")); h.update(raw)
        digest = "sha256:" + h.hexdigest()
        return cls(SCHEMA, "scheduler-execution-transaction:" + h.hexdigest()[:24],
                   scheduler_ref, command_ref, task_ref, attempt_ref,
                   reservation_ref, outcome_ref, task_state,
                   task_state_version, released_at, digest)


@runtime_checkable
class SchedulerHandlerExecutionTransaction(Protocol):
    def commit_outcome(self, *, outcome: SchedulerHandlerExecutionOutcome[object],
                       released_at: str) -> SchedulerHandlerExecutionCommit: ...


__all__ = ["SCHEMA", "SchedulerHandlerExecutionCommit", "SchedulerHandlerExecutionTransaction"]
