"""Existing-Scheduler binding for the r11 two-specialist love laboratory.

This module registers one handler on the existing Dispatcher and submits each
visit through the existing SchedulerContract.  It does not sequence visits on
its own: callers must submit the first visit, prepare the authorized second
visit, then submit that second visit separately.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol

from contracts.event import Event, EventType, Request
from contracts.scheduler import SchedulerContract
from context.laboratory_framework_contract_0273 import LaboratoryVisitRequest
from context.native_love_laboratory_second_specialist_0287 import (
    NATIVE_LOVE_COLLABORATIVE_COMPONENT_ID,
    NativeLoveCollaborativeExecutionRecord,
    NativeLoveCollaborativeLaboratoryProvider,
    execute_native_love_collaborative_visit,
)

NATIVE_LOVE_COLLABORATION_SCHEDULER_BINDING_VERSION = "0287.r7.r11"
NATIVE_LOVE_COLLABORATION_SCHEDULER_RECEIPT_SCHEMA = (
    "missipy.laboratory.scheduler_visit_receipt.love_collaborative.v1"
)
NATIVE_LOVE_COLLABORATION_EVENT_SOURCE = (
    "laboratory.love_native.collaboration.scheduler_binding"
)
NATIVE_LOVE_COLLABORATION_EVENT_DESTINATION = "scheduler"
_COLLABORATION_SCHEDULER_PATH = (
    "Scheduler.emit()",
    "PolicyEngine.decide()",
    "PriorityQueue",
    "Scheduler.run()",
    "Dispatcher",
    "NativeLoveCollaborativeVisitRequestHandler",
    "NativeLoveCollaborativeLaboratoryProvider.execute()",
)


class NativeLoveCollaborationSchedulerBindingError(RuntimeError):
    """Raised when the existing Scheduler cannot close an r11 visit."""


class NativeLoveCollaborationVisitDispatcher(Protocol):
    """Existing Dispatcher registration surface."""

    def register(self, event_type: EventType, handler: object) -> None:
        """Register one handler on the existing Dispatcher."""


@dataclass(frozen=True, slots=True)
class NativeLoveCollaborationSchedulerVisitReceipt:
    """Immutable reply returned through the existing Request future."""

    schema: str
    event_id: str
    correlation_id: str
    visit_ref: str
    provider_ref: str
    registration_component_id: str
    execution: NativeLoveCollaborativeExecutionRecord
    scheduler_path: tuple[str, ...] = _COLLABORATION_SCHEDULER_PATH
    existing_scheduler_used: bool = True
    scheduler_created: bool = False
    scheduler_run_modified: bool = False
    parallel_queue_created: bool = False
    parallel_eventbus_created: bool = False
    parallel_registry_created: bool = False
    followup_visit_submitted: bool = False
    direct_specialist_invocation: bool = False

    def __post_init__(self) -> None:
        if self.schema != NATIVE_LOVE_COLLABORATION_SCHEDULER_RECEIPT_SCHEMA:
            raise NativeLoveCollaborationSchedulerBindingError(
                "unsupported collaboration receipt schema"
            )
        if not self.event_id:
            raise NativeLoveCollaborationSchedulerBindingError(
                "event_id must be non-empty"
            )
        if self.correlation_id != self.visit_ref:
            raise NativeLoveCollaborationSchedulerBindingError(
                "correlation_id must equal visit_ref"
            )
        if self.execution.request.visit_ref != self.visit_ref:
            raise NativeLoveCollaborationSchedulerBindingError(
                "execution request mismatch"
            )
        if self.execution.result.visit_ref != self.visit_ref:
            raise NativeLoveCollaborationSchedulerBindingError(
                "execution result mismatch"
            )
        if self.provider_ref != self.execution.provider_ref:
            raise NativeLoveCollaborationSchedulerBindingError(
                "provider_ref mismatch"
            )
        if self.registration_component_id != (
            NATIVE_LOVE_COLLABORATIVE_COMPONENT_ID
        ):
            raise NativeLoveCollaborationSchedulerBindingError(
                "registration component mismatch"
            )
        if self.scheduler_path != _COLLABORATION_SCHEDULER_PATH:
            raise NativeLoveCollaborationSchedulerBindingError(
                "Scheduler path changed"
            )
        forbidden = (
            not self.existing_scheduler_used,
            self.scheduler_created,
            self.scheduler_run_modified,
            self.parallel_queue_created,
            self.parallel_eventbus_created,
            self.parallel_registry_created,
            self.followup_visit_submitted,
            self.direct_specialist_invocation,
        )
        if any(forbidden):
            raise NativeLoveCollaborationSchedulerBindingError(
                "receipt must preserve the single-Scheduler architecture"
            )

    @property
    def receipt_ref(self) -> str:
        return f"scheduler-receipt:{self.event_id}"

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "receipt_ref": self.receipt_ref,
            "event_id": self.event_id,
            "event_type": "LABORATORY_VISIT_REQUEST",
            "correlation_id": self.correlation_id,
            "visit_ref": self.visit_ref,
            "provider_ref": self.provider_ref,
            "registration_component_id": self.registration_component_id,
            "execution": self.execution.to_mapping(),
            "scheduler_path": list(self.scheduler_path),
            "existing_scheduler_used": self.existing_scheduler_used,
            "scheduler_created": self.scheduler_created,
            "scheduler_run_modified": self.scheduler_run_modified,
            "parallel_queue_created": self.parallel_queue_created,
            "parallel_eventbus_created": self.parallel_eventbus_created,
            "parallel_registry_created": self.parallel_registry_created,
            "followup_visit_submitted": self.followup_visit_submitted,
            "direct_specialist_invocation": self.direct_specialist_invocation,
        }


@dataclass(frozen=True, slots=True)
class NativeLoveCollaborativeVisitRequestHandler:
    """Existing-Dispatcher handler for one authorized visit."""

    provider: NativeLoveCollaborativeLaboratoryProvider

    async def handle(
        self,
        event: Event,
    ) -> NativeLoveCollaborationSchedulerVisitReceipt:
        if event.type is not EventType.LABORATORY_VISIT_REQUEST:
            raise NativeLoveCollaborationSchedulerBindingError(
                "handler requires LABORATORY_VISIT_REQUEST"
            )
        if event.dest != NATIVE_LOVE_COLLABORATION_EVENT_DESTINATION:
            raise NativeLoveCollaborationSchedulerBindingError(
                "laboratory visit destination must remain scheduler"
            )
        if not isinstance(event.payload, LaboratoryVisitRequest):
            raise NativeLoveCollaborationSchedulerBindingError(
                "event payload must be LaboratoryVisitRequest"
            )
        execution = execute_native_love_collaborative_visit(
            event.payload,
            provider=self.provider,
        )
        return NativeLoveCollaborationSchedulerVisitReceipt(
            schema=NATIVE_LOVE_COLLABORATION_SCHEDULER_RECEIPT_SCHEMA,
            event_id=event.id,
            correlation_id=event.correlation_id or event.payload.visit_ref,
            visit_ref=event.payload.visit_ref,
            provider_ref=execution.provider_ref,
            registration_component_id=NATIVE_LOVE_COLLABORATIVE_COMPONENT_ID,
            execution=execution,
        )


def build_native_love_collaboration_visit_event(
    request: LaboratoryVisitRequest,
    *,
    priority: int = 0,
    source: str = NATIVE_LOVE_COLLABORATION_EVENT_SOURCE,
) -> Event:
    """Build one immutable command event for the existing Scheduler."""

    if not isinstance(request, LaboratoryVisitRequest):
        raise TypeError("request must be LaboratoryVisitRequest")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be non-empty")
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise TypeError("priority must be an integer")
    metadata = MappingProxyType(
        {
            "schema": (
                "missipy.laboratory.scheduler_visit_event."
                "love_collaborative.v1"
            ),
            "visit_ref": request.visit_ref,
            "laboratory_ref": request.laboratory_ref,
            "specialist_ref": request.specialist_ref,
            "registration_component_id": (
                NATIVE_LOVE_COLLABORATIVE_COMPONENT_ID
            ),
            "command": True,
            "followup_visit_submitted": False,
            "scheduler_created": False,
            "scheduler_run_modified": False,
        }
    )
    return Event(
        type=EventType.LABORATORY_VISIT_REQUEST,
        source=source.strip(),
        dest=NATIVE_LOVE_COLLABORATION_EVENT_DESTINATION,
        payload=request,
        priority=priority,
        correlation_id=request.visit_ref,
        metadata=metadata,
    )


def register_native_love_collaboration_visit_handler(
    dispatcher: NativeLoveCollaborationVisitDispatcher,
    *,
    provider: NativeLoveCollaborativeLaboratoryProvider,
) -> NativeLoveCollaborativeVisitRequestHandler:
    """Register the r11 handler on the existing Dispatcher."""

    handler = NativeLoveCollaborativeVisitRequestHandler(provider=provider)
    dispatcher.register(EventType.LABORATORY_VISIT_REQUEST, handler)
    return handler


async def submit_native_love_collaboration_visit(
    scheduler: SchedulerContract,
    request: LaboratoryVisitRequest,
    *,
    priority: int = 0,
    timeout: float | None = None,
    source: str = NATIVE_LOVE_COLLABORATION_EVENT_SOURCE,
) -> NativeLoveCollaborationSchedulerVisitReceipt:
    """Submit exactly one visit through the already-running Scheduler."""

    if not isinstance(scheduler, SchedulerContract):
        raise TypeError("scheduler must implement SchedulerContract")
    effective_timeout = (
        request.resource_budget.max_duration_ms / 1_000.0
        if timeout is None
        else timeout
    )
    if effective_timeout <= 0:
        raise ValueError("timeout must be > 0")
    loop = asyncio.get_running_loop()
    reply = loop.create_future()
    event = build_native_love_collaboration_visit_event(
        request,
        priority=priority,
        source=source,
    ).with_request(Request(reply=reply, timeout=effective_timeout))
    await scheduler.emit(event)
    try:
        result = await asyncio.wait_for(reply, timeout=effective_timeout)
    except TimeoutError as exc:
        raise NativeLoveCollaborationSchedulerBindingError(
            "existing Scheduler did not return the visit before timeout"
        ) from exc
    if not isinstance(result, NativeLoveCollaborationSchedulerVisitReceipt):
        raise NativeLoveCollaborationSchedulerBindingError(
            "existing Scheduler returned an unexpected reply"
        )
    if result.visit_ref != request.visit_ref:
        raise NativeLoveCollaborationSchedulerBindingError(
            "Scheduler reply visit_ref mismatch"
        )
    return result


__all__ = (
    "NATIVE_LOVE_COLLABORATION_EVENT_DESTINATION",
    "NATIVE_LOVE_COLLABORATION_EVENT_SOURCE",
    "NATIVE_LOVE_COLLABORATION_SCHEDULER_BINDING_VERSION",
    "NATIVE_LOVE_COLLABORATION_SCHEDULER_RECEIPT_SCHEMA",
    "NativeLoveCollaborationSchedulerBindingError",
    "NativeLoveCollaborationSchedulerVisitReceipt",
    "NativeLoveCollaborativeVisitRequestHandler",
    "build_native_love_collaboration_visit_event",
    "register_native_love_collaboration_visit_handler",
    "submit_native_love_collaboration_visit",
)
