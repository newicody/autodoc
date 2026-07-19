"""Claim one SQL-authoritative research command for the running Scheduler.

This adapter never creates or starts a Scheduler. It proves that the injected
canonical Scheduler is already running, then delegates one atomic SQL claim to
the relational authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from context.github_research_scheduler_command_sql_authority_0287 import (
    SchedulerCommandSqlClaim,
)

CANONICAL_SCHEDULER_CLAIM_RESULT_SCHEMA = (
    "missipy.github.research_canonical_scheduler_claim_result.v1"
)


class CanonicalSchedulerCommandClaimError(RuntimeError):
    """Raised when the canonical Scheduler ownership boundary is violated."""


@runtime_checkable
class RunningSchedulerView(Protocol):
    @property
    def running(self) -> bool: ...


@runtime_checkable
class SchedulerCommandClaimStore(Protocol):
    def claim_next_pending(
        self,
        *,
        scheduler_ref: str,
        claimed_at: str,
    ) -> SchedulerCommandSqlClaim | None: ...


@dataclass(frozen=True, slots=True)
class CanonicalSchedulerCommandClaimResult:
    schema: str
    valid: bool
    status: str
    scheduler_ref: str
    claim: SchedulerCommandSqlClaim | None

    def __post_init__(self) -> None:
        if self.schema != CANONICAL_SCHEDULER_CLAIM_RESULT_SCHEMA:
            raise CanonicalSchedulerCommandClaimError(
                "unsupported canonical Scheduler claim result schema"
            )
        if self.status not in {"command-claimed", "no-pending-command"}:
            raise CanonicalSchedulerCommandClaimError(
                "unsupported canonical Scheduler claim status"
            )
        if self.valid is not True:
            raise CanonicalSchedulerCommandClaimError(
                "canonical Scheduler claim result must be valid"
            )
        if (self.claim is None) != (self.status == "no-pending-command"):
            raise CanonicalSchedulerCommandClaimError(
                "claim presence does not match result status"
            )


def claim_next_for_running_canonical_scheduler(
    *,
    scheduler: RunningSchedulerView,
    command_store: SchedulerCommandClaimStore,
    scheduler_ref: str,
    claimed_at: str,
) -> CanonicalSchedulerCommandClaimResult:
    if not isinstance(scheduler, RunningSchedulerView):
        raise CanonicalSchedulerCommandClaimError(
            "scheduler must expose the existing running lifecycle view"
        )
    if scheduler.running is not True:
        raise CanonicalSchedulerCommandClaimError(
            "the canonical Scheduler must already be running before SQL claim"
        )
    if not isinstance(command_store, SchedulerCommandClaimStore):
        raise CanonicalSchedulerCommandClaimError(
            "command_store must implement the atomic SQL claim port"
        )
    claim = command_store.claim_next_pending(
        scheduler_ref=scheduler_ref,
        claimed_at=claimed_at,
    )
    return CanonicalSchedulerCommandClaimResult(
        schema=CANONICAL_SCHEDULER_CLAIM_RESULT_SCHEMA,
        valid=True,
        status="command-claimed" if claim is not None else "no-pending-command",
        scheduler_ref=scheduler_ref,
        claim=claim,
    )


__all__ = (
    "CANONICAL_SCHEDULER_CLAIM_RESULT_SCHEMA",
    "CanonicalSchedulerCommandClaimError",
    "CanonicalSchedulerCommandClaimResult",
    "RunningSchedulerView",
    "SchedulerCommandClaimStore",
    "claim_next_for_running_canonical_scheduler",
)
