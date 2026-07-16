"""Existing-Scheduler binding for the concrete love laboratory in r10.

The module reuses LABORATORY_VISIT_REQUEST and the existing Dispatcher handler
surface.  It never creates or runs a Scheduler, queue, EventBus, registry, or
laboratory-local orchestrator.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol

from contracts.event import Event, EventType, Request
from contracts.scheduler import SchedulerContract
from context.laboratory_framework_contract_0273 import LaboratoryVisitRequest
from context.native_love_laboratory_first_specialist_0287 import (
    NATIVE_LOVE_LABORATORY_COMPONENT_ID,
    NativeLoveLaboratoryExecutionRecord,
    NativeLoveLaboratoryProvider,
    execute_native_love_laboratory_visit,
)

NATIVE_LOVE_SCHEDULER_BINDING_VERSION = "0287.r7.r10"
NATIVE_LOVE_SCHEDULER_RECEIPT_SCHEMA = (
    "missipy.laboratory.scheduler_visit_receipt.love_native.v1"
)
NATIVE_LOVE_SCHEDULER_EVENT_SOURCE = "laboratory.love_native.scheduler_binding"
NATIVE_LOVE_SCHEDULER_EVENT_DESTINATION = "scheduler"
_NATIVE_SCHEDULER_PATH = (
    "Scheduler.emit()",
    "PolicyEngine.decide()",
    "PriorityQueue",
    "Scheduler.run()",
    "Dispatcher",
    "NativeLoveLaboratoryVisitRequestHandler",
    "NativeLoveLaboratoryProvider.execute()",
)


class NativeLoveSchedulerBindingError(RuntimeError):
    """Raised when the existing Scheduler path cannot close a native visit."""


class NativeLoveVisitDispatcher(Protocol):
    """Existing Dispatcher registration surface used by the binding."""

    def register(self, event_type: EventType, handler: object) -> None:
        """Register one handler on the existing Dispatcher."""


@dataclass(frozen=True, slots=True)
class NativeLoveSchedulerVisitReceipt:
    """Immutable reply returned through the existing Request future."""

    schema: str
    event_id: str
    correlation_id: str
    visit_ref: str
    provider_ref: str
    registration_component_id: str
    execution: NativeLoveLaboratoryExecutionRecord
    scheduler_path: tuple[str, ...] = _NATIVE_SCHEDULER_PATH
    existing_scheduler_used: bool = True
    scheduler_created: bool = False
    scheduler_run_modified: bool = False
    parallel_queue_created: bool = False
    parallel_eventbus_created: bool = False
    parallel_registry_created: bool = False
    result_event_reserved: str = "LABORATORY_VISIT_RESULT"
    result_event_published: bool = False

    def __post_init__(self) -> None:
        if self.schema != NATIVE_LOVE_SCHEDULER_RECEIPT_SCHEMA:
            raise NativeLoveSchedulerBindingError("unsupported receipt schema")
        if not self.event_id:
            raise NativeLoveSchedulerBindingError("event_id must be non-empty")
        if self.correlation_id != self.visit_ref:
            raise NativeLoveSchedulerBindingError(
                "correlation_id must equal visit_ref"
            )
        if self.execution.request.visit_ref != self.visit_ref:
            raise NativeLoveSchedulerBindingError("execution request mismatch")
        if self.execution.result.visit_ref != self.visit_ref:
            raise NativeLoveSchedulerBindingError("execution result mismatch")
        if self.provider_ref != self.execution.provider_ref:
            raise NativeLoveSchedulerBindingError("provider_ref mismatch")
        if self.registration_component_id != NATIVE_LOVE_LABORATORY_COMPONENT_ID:
            raise NativeLoveSchedulerBindingError("registration component mismatch")
        if self.scheduler_path != _NATIVE_SCHEDULER_PATH:
            raise NativeLoveSchedulerBindingError("Scheduler path changed")
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
            raise NativeLoveSchedulerBindingError(
                "receipt must preserve the single-Scheduler architecture"
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
            "eventbus_role": "observation copy only",
            "publication_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class NativeLoveLaboratoryVisitRequestHandler:
    """Existing-Dispatcher handler for one native love visit."""

    provider: NativeLoveLaboratoryProvider

    async def handle(self, event: Event) -> NativeLoveSchedulerVisitReceipt:
        if event.type is not EventType.LABORATORY_VISIT_REQUEST:
            raise NativeLoveSchedulerBindingError(
                "handler requires LABORATORY_VISIT_REQUEST"
            )
        if event.dest != NATIVE_LOVE_SCHEDULER_EVENT_DESTINATION:
            raise NativeLoveSchedulerBindingError(
                "laboratory visit destination must remain scheduler"
            )
        if not isinstance(event.payload, LaboratoryVisitRequest):
            raise NativeLoveSchedulerBindingError(
                "event payload must be LaboratoryVisitRequest"
            )
        execution = execute_native_love_laboratory_visit(
            event.payload,
            provider=self.provider,
        )
        return NativeLoveSchedulerVisitReceipt(
            schema=NATIVE_LOVE_SCHEDULER_RECEIPT_SCHEMA,
            event_id=event.id,
            correlation_id=event.correlation_id or event.payload.visit_ref,
            visit_ref=event.payload.visit_ref,
            provider_ref=execution.provider_ref,
            registration_component_id=NATIVE_LOVE_LABORATORY_COMPONENT_ID,
            execution=execution,
        )


def build_native_love_laboratory_visit_event(
    request: LaboratoryVisitRequest,
    *,
    priority: int = 0,
    source: str = NATIVE_LOVE_SCHEDULER_EVENT_SOURCE,
) -> Event:
    """Build the immutable command event submitted to the existing Scheduler."""

    if not isinstance(request, LaboratoryVisitRequest):
        raise TypeError("request must be LaboratoryVisitRequest")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be non-empty")
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise TypeError("priority must be an integer")
    metadata = MappingProxyType(
        {
            "schema": "missipy.laboratory.scheduler_visit_event.love_native.v1",
            "visit_ref": request.visit_ref,
            "laboratory_ref": request.laboratory_ref,
            "specialist_ref": request.specialist_ref,
            "registration_component_id": NATIVE_LOVE_LABORATORY_COMPONENT_ID,
            "command": True,
            "scheduler_created": False,
            "scheduler_run_modified": False,
        }
    )
    return Event(
        type=EventType.LABORATORY_VISIT_REQUEST,
        source=source.strip(),
        dest=NATIVE_LOVE_SCHEDULER_EVENT_DESTINATION,
        payload=request,
        priority=priority,
        correlation_id=request.visit_ref,
        metadata=metadata,
    )


def register_native_love_laboratory_visit_handler(
    dispatcher: NativeLoveVisitDispatcher,
    *,
    provider: NativeLoveLaboratoryProvider,
) -> NativeLoveLaboratoryVisitRequestHandler:
    """Register the concrete handler on the existing Dispatcher."""

    handler = NativeLoveLaboratoryVisitRequestHandler(provider=provider)
    dispatcher.register(EventType.LABORATORY_VISIT_REQUEST, handler)
    return handler


async def submit_native_love_laboratory_visit(
    scheduler: SchedulerContract,
    request: LaboratoryVisitRequest,
    *,
    priority: int = 0,
    timeout: float | None = None,
    source: str = NATIVE_LOVE_SCHEDULER_EVENT_SOURCE,
) -> NativeLoveSchedulerVisitReceipt:
    """Submit through the already-running Scheduler and await its reply."""

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
    event = build_native_love_laboratory_visit_event(
        request,
        priority=priority,
        source=source,
    ).with_request(Request(reply=reply, timeout=effective_timeout))
    await scheduler.emit(event)
    try:
        result = await asyncio.wait_for(reply, timeout=effective_timeout)
    except TimeoutError as exc:
        raise NativeLoveSchedulerBindingError(
            "existing Scheduler did not return native visit before timeout"
        ) from exc
    if not isinstance(result, NativeLoveSchedulerVisitReceipt):
        raise NativeLoveSchedulerBindingError(
            "existing Scheduler returned an unexpected reply"
        )
    if result.visit_ref != request.visit_ref:
        raise NativeLoveSchedulerBindingError("Scheduler reply visit_ref mismatch")
    return result


__all__ = (
    "NATIVE_LOVE_SCHEDULER_BINDING_VERSION",
    "NATIVE_LOVE_SCHEDULER_EVENT_DESTINATION",
    "NATIVE_LOVE_SCHEDULER_EVENT_SOURCE",
    "NATIVE_LOVE_SCHEDULER_RECEIPT_SCHEMA",
    "NativeLoveLaboratoryVisitRequestHandler",
    "NativeLoveSchedulerBindingError",
    "NativeLoveSchedulerVisitReceipt",
    "NativeLoveVisitDispatcher",
    "build_native_love_laboratory_visit_event",
    "register_native_love_laboratory_visit_handler",
    "submit_native_love_laboratory_visit",
)
