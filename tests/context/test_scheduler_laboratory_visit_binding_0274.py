import asyncio
import json

import pytest

from contracts.event import Event, EventType
from context.laboratory_framework_contract_0273 import (
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
)
from context.scheduler_laboratory_visit_binding_0274 import (
    LaboratorySchedulerBindingError,
    LaboratorySchedulerVisitReceipt,
    LaboratoryVisitRequestHandler,
    build_laboratory_visit_event,
    register_laboratory_visit_handler,
    submit_laboratory_visit,
)
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler


def visit_request(*, scenario: str = "completed") -> LaboratoryVisitRequest:
    return LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref=f"laboratory-visit:scheduler-{scenario}",
        laboratory_ref="laboratory:local-fake",
        specialist_ref="specialist:technical",
        objective_ref=f"orientation:scheduler-{scenario}",
        source_candidate_ref=f"source-candidate:scheduler-{scenario}",
        context_generation=1,
        input_contract_ref="contract:missipy.specialist.demand.v1",
        expected_output_contract_ref=(
            "contract:missipy.laboratory.visit_result.v1"
        ),
        resource_budget=LaboratoryResourceBudget(
            max_duration_ms=2_000,
        ),
        return_route_ref=f"route:laboratory/scheduler-{scenario}/result",
        context_refs=(f"sql:context:scheduler-{scenario}",),
        evidence_refs=(f"artifact:evidence:scheduler-{scenario}",),
        metadata=(("fake_scenario", scenario),),
    )


def test_event_builder_targets_existing_scheduler() -> None:
    request = visit_request()
    event = build_laboratory_visit_event(request, priority=7)

    assert event.type is EventType.LABORATORY_VISIT_REQUEST
    assert event.dest == "scheduler"
    assert event.payload is request
    assert event.priority == 7
    assert event.correlation_id == request.visit_ref
    assert event.metadata["scheduler_created"] is False
    assert event.metadata["scheduler_run_modified"] is False


def test_handler_executes_provider_without_owning_scheduler() -> None:
    async def scenario() -> LaboratorySchedulerVisitReceipt:
        handler = LaboratoryVisitRequestHandler()
        return await handler.handle(build_laboratory_visit_event(visit_request()))

    receipt = asyncio.run(scenario())
    payload = receipt.to_mapping()

    assert receipt.execution.result.status == "completed"
    assert payload["existing_scheduler_used"] is True
    assert payload["scheduler_created"] is False
    assert payload["scheduler_run_modified"] is False
    assert payload["parallel_queue_created"] is False
    assert payload["parallel_eventbus_created"] is False
    assert payload["parallel_registry_created"] is False
    assert payload["result_event_published"] is False
    json.dumps(payload, sort_keys=True)


def test_handler_rejects_wrong_event_type_and_payload() -> None:
    handler = LaboratoryVisitRequestHandler()

    async def wrong_type() -> None:
        await handler.handle(
            Event(
                type=EventType.TICK,
                source="test",
                payload=visit_request(),
            )
        )

    async def wrong_payload() -> None:
        await handler.handle(
            Event(
                type=EventType.LABORATORY_VISIT_REQUEST,
                source="test",
                payload={"not": "a request"},
            )
        )

    with pytest.raises(
        LaboratorySchedulerBindingError,
        match="requires LABORATORY_VISIT_REQUEST",
    ):
        asyncio.run(wrong_type())
    with pytest.raises(
        LaboratorySchedulerBindingError,
        match="payload must be LaboratoryVisitRequest",
    ):
        asyncio.run(wrong_payload())


def test_registration_uses_existing_dispatcher_surface() -> None:
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    handler = register_laboratory_visit_handler(dispatcher)

    assert (
        dispatcher.handlers[EventType.LABORATORY_VISIT_REQUEST]
        is handler
    )


def test_existing_scheduler_runs_visit_end_to_end() -> None:
    async def scenario():
        event_bus = EventBus()
        observed = event_bus.subscribe(EventType.LABORATORY_VISIT_REQUEST)
        dispatcher = Dispatcher(event_bus)
        register_laboratory_visit_handler(dispatcher)

        scheduler = Scheduler(
            queue=PriorityQueue(),
            dispatcher=dispatcher,
            event_bus=event_bus,
            registry=Registry(),
            context_interval=60.0,
        )
        run_task = asyncio.create_task(scheduler.run())
        try:
            receipt = await submit_laboratory_visit(
                scheduler,
                visit_request(),
                priority=11,
                timeout=1.0,
            )
            observed_event = await asyncio.wait_for(observed.get(), timeout=1.0)
        finally:
            await scheduler.shutdown()
            await asyncio.wait_for(run_task, timeout=1.0)
        return receipt, observed_event

    receipt, observed_event = asyncio.run(scenario())

    assert receipt.execution.result.status == "completed"
    assert receipt.existing_scheduler_used is True
    assert receipt.scheduler_created is False
    assert observed_event.type is EventType.LABORATORY_VISIT_REQUEST
    assert observed_event.correlation_id == receipt.visit_ref


def test_existing_scheduler_preserves_fake_followup_scenario() -> None:
    async def scenario():
        event_bus = EventBus()
        dispatcher = Dispatcher(event_bus)
        register_laboratory_visit_handler(dispatcher)
        scheduler = Scheduler(
            queue=PriorityQueue(),
            dispatcher=dispatcher,
            event_bus=event_bus,
            registry=Registry(),
            context_interval=60.0,
        )
        run_task = asyncio.create_task(scheduler.run())
        try:
            return await submit_laboratory_visit(
                scheduler,
                visit_request(scenario="needs_specialist"),
                timeout=1.0,
            )
        finally:
            await scheduler.shutdown()
            await asyncio.wait_for(run_task, timeout=1.0)

    receipt = asyncio.run(scenario())

    assert receipt.execution.result.status == "needs_specialist"
    assert receipt.execution.result.requested_specialist_refs == (
        "specialist:validator",
    )


def test_submit_requires_already_running_scheduler() -> None:
    async def scenario() -> None:
        event_bus = EventBus()
        dispatcher = Dispatcher(event_bus)
        register_laboratory_visit_handler(dispatcher)
        scheduler = Scheduler(
            queue=PriorityQueue(),
            dispatcher=dispatcher,
            event_bus=event_bus,
            registry=Registry(),
            context_interval=60.0,
        )
        await submit_laboratory_visit(
            scheduler,
            visit_request(),
            timeout=0.01,
        )

    with pytest.raises(
        LaboratorySchedulerBindingError,
        match="did not return laboratory visit",
    ):
        asyncio.run(scenario())
