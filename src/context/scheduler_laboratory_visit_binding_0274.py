"""Existing-Scheduler laboratory visit binding for phase 0274-r1.

This module connects ``missipy.laboratory.visit_request.v1`` to the existing
micro-kernel path:

    Scheduler.emit()
    -> PolicyEngine.decide()
    -> PriorityQueue
    -> existing Scheduler.run()
    -> Dispatcher
    -> LaboratoryVisitRequestHandler
    -> LaboratoryProvider.execute()

It does not create, wrap, subclass or own a Scheduler.  It also does not create
another queue, EventBus, registry or runtime manager.  The caller must submit
through the already-running platform Scheduler.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol

from contracts.event import Event, EventType, Request
from contracts.scheduler import SchedulerContract
from context.deterministic_fake_laboratory_provider_0273 import (
    DETERMINISTIC_FAKE_COMPONENT_ID,
    FakeLaboratoryExecutionRecord,
    LaboratoryProvider,
    execute_deterministic_fake_laboratory_visit,
)
from context.laboratory_framework_contract_0273 import (
    LaboratoryVisitRequest,
)

SCHEDULER_LABORATORY_VISIT_BINDING_VERSION = "0274.r1"
SCHEDULER_LABORATORY_VISIT_RECEIPT_SCHEMA = (
    "missipy.laboratory.scheduler_visit_receipt.v1"
)
SCHEDULER_LABORATORY_EVENT_SOURCE = "laboratory.scheduler_binding"
SCHEDULER_LABORATORY_EVENT_DESTINATION = "scheduler"

_SCHEDULER_PATH = (
    "Scheduler.emit()",
    "PolicyEngine.decide()",
    "PriorityQueue",
    "Scheduler.run()",
    "Dispatcher",
    "LaboratoryVisitRequestHandler",
    "LaboratoryProvider.execute()",
)


class LaboratorySchedulerBindingError(RuntimeError):
    """Raised when the existing Scheduler path cannot return a valid receipt."""


class LaboratoryVisitDispatcher(Protocol):
    """Only the existing Dispatcher registration surface used by this binding."""

    def register(self, event_type: EventType, handler: object) -> None:
        """Register one handler on the existing Dispatcher."""


@dataclass(frozen=True, slots=True)
class LaboratorySchedulerVisitReceipt:
    """Immutable receipt returned through the existing Request.reply future."""

    schema: str
    event_id: str
    correlation_id: str
    visit_ref: str
    provider_ref: str
    registration_component_id: str
    execution: FakeLaboratoryExecutionRecord
    scheduler_path: tuple[str, ...] = _SCHEDULER_PATH
    existing_scheduler_used: bool = True
    scheduler_created: bool = False
    scheduler_run_modified: bool = False
    parallel_queue_created: bool = False
    parallel_eventbus_created: bool = False
    parallel_registry_created: bool = False
    result_event_reserved: str = "LABORATORY_VISIT_RESULT"
    result_event_published: bool = False

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_LABORATORY_VISIT_RECEIPT_SCHEMA:
            raise LaboratorySchedulerBindingError(
                "unsupported laboratory Scheduler receipt schema"
            )
        if not self.event_id:
            raise LaboratorySchedulerBindingError("event_id must be non-empty")
        if self.correlation_id != self.visit_ref:
            raise LaboratorySchedulerBindingError(
                "correlation_id must equal visit_ref"
            )
        if self.execution.request.visit_ref != self.visit_ref:
            raise LaboratorySchedulerBindingError(
                "execution request must belong to visit_ref"
            )
        if self.execution.result.visit_ref != self.visit_ref:
            raise LaboratorySchedulerBindingError(
                "execution result must belong to visit_ref"
            )
        if self.provider_ref != self.execution.provider_ref:
            raise LaboratorySchedulerBindingError(
                "provider_ref must match execution provider_ref"
            )
        if (
            self.registration_component_id
            != self.execution.registration_component_id
        ):
            raise LaboratorySchedulerBindingError(
                "registration component must match execution"
            )
        if self.scheduler_path != _SCHEDULER_PATH:
            raise LaboratorySchedulerBindingError(
                "scheduler_path must preserve the canonical existing path"
            )
        forbidden = (
            not self.existing_scheduler_used,
            self.scheduler_created,
            self.scheduler_run_modified,
            self.parallel_queue_created,
            self.parallel_eventbus_created,
            self.parallel_registry_created,
            self.result_event_published,
        )
        if any(forbidden):
            raise LaboratorySchedulerBindingError(
                "laboratory receipt must not claim parallel orchestration"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
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
            "result_event_reserved": self.result_event_reserved,
            "result_event_published": self.result_event_published,
            "eventbus_role": "Dispatcher observation copy only",
            "publication_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class LaboratoryVisitRequestHandler:
    """Tiny existing-Dispatcher Handler for one laboratory visit request."""

    provider: LaboratoryProvider | None = None
    registration_component_id: str = DETERMINISTIC_FAKE_COMPONENT_ID

    async def handle(self, event: Event) -> LaboratorySchedulerVisitReceipt:
        if event.type is not EventType.LABORATORY_VISIT_REQUEST:
            raise LaboratorySchedulerBindingError(
                "handler requires LABORATORY_VISIT_REQUEST"
            )
        if event.dest != SCHEDULER_LABORATORY_EVENT_DESTINATION:
            raise LaboratorySchedulerBindingError(
                "laboratory visit event destination must remain scheduler"
            )
        if not isinstance(event.payload, LaboratoryVisitRequest):
            raise LaboratorySchedulerBindingError(
                "LABORATORY_VISIT_REQUEST payload must be LaboratoryVisitRequest"
            )
        execution = execute_deterministic_fake_laboratory_visit(
            event.payload,
            provider=self.provider,
        )
        return LaboratorySchedulerVisitReceipt(
            schema=SCHEDULER_LABORATORY_VISIT_RECEIPT_SCHEMA,
            event_id=event.id,
            correlation_id=event.correlation_id or event.payload.visit_ref,
            visit_ref=event.payload.visit_ref,
            provider_ref=execution.provider_ref,
            registration_component_id=self.registration_component_id,
            execution=execution,
        )


def build_laboratory_visit_event(
    request: LaboratoryVisitRequest,
    *,
    priority: int = 0,
    source: str = SCHEDULER_LABORATORY_EVENT_SOURCE,
) -> Event:
    """Build an immutable command event for the existing Scheduler."""

    if not isinstance(request, LaboratoryVisitRequest):
        raise TypeError("request must be a LaboratoryVisitRequest")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be non-empty")
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise TypeError("priority must be an integer")
    metadata = MappingProxyType(
        {
            "schema": "missipy.laboratory.scheduler_visit_event.v1",
            "visit_ref": request.visit_ref,
            "laboratory_ref": request.laboratory_ref,
            "specialist_ref": request.specialist_ref,
            "command": True,
            "scheduler_created": False,
            "scheduler_run_modified": False,
        }
    )
    return Event(
        type=EventType.LABORATORY_VISIT_REQUEST,
        source=source.strip(),
        dest=SCHEDULER_LABORATORY_EVENT_DESTINATION,
        payload=request,
        priority=priority,
        correlation_id=request.visit_ref,
        metadata=metadata,
    )


def register_laboratory_visit_handler(
    dispatcher: LaboratoryVisitDispatcher,
    *,
    provider: LaboratoryProvider | None = None,
) -> LaboratoryVisitRequestHandler:
    """Register the Handler on the existing Dispatcher and return it."""

    handler = LaboratoryVisitRequestHandler(provider=provider)
    dispatcher.register(EventType.LABORATORY_VISIT_REQUEST, handler)
    return handler


async def submit_laboratory_visit(
    scheduler: SchedulerContract,
    request: LaboratoryVisitRequest,
    *,
    priority: int = 0,
    timeout: float | None = None,
    source: str = SCHEDULER_LABORATORY_EVENT_SOURCE,
) -> LaboratorySchedulerVisitReceipt:
    """Submit a visit to an already-running Scheduler and await its reply.

    This helper never calls ``run()`` and never creates a Scheduler.  The
    platform bootstrap remains responsible for the one Scheduler lifecycle.
    """

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
    event = build_laboratory_visit_event(
        request,
        priority=priority,
        source=source,
    ).with_request(Request(reply=reply, timeout=effective_timeout))

    await scheduler.emit(event)
    try:
        result = await asyncio.wait_for(reply, timeout=effective_timeout)
    except TimeoutError as exc:
        raise LaboratorySchedulerBindingError(
            "existing Scheduler did not return laboratory visit before timeout"
        ) from exc

    if not isinstance(result, LaboratorySchedulerVisitReceipt):
        raise LaboratorySchedulerBindingError(
            "existing Scheduler returned an unexpected laboratory reply"
        )
    if result.visit_ref != request.visit_ref:
        raise LaboratorySchedulerBindingError(
            "Scheduler reply visit_ref does not match request"
        )
    return result


__all__ = (
    "LaboratorySchedulerBindingError",
    "LaboratorySchedulerVisitReceipt",
    "LaboratoryVisitDispatcher",
    "LaboratoryVisitRequestHandler",
    "SCHEDULER_LABORATORY_EVENT_DESTINATION",
    "SCHEDULER_LABORATORY_EVENT_SOURCE",
    "SCHEDULER_LABORATORY_VISIT_BINDING_VERSION",
    "SCHEDULER_LABORATORY_VISIT_RECEIPT_SCHEMA",
    "build_laboratory_visit_event",
    "register_laboratory_visit_handler",
    "submit_laboratory_visit",
)
