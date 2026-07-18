from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

import context.github_research_scheduler_dispatch_0287 as module
from context.github_research_scheduler_dispatch_0287 import (
    GitHubResearchSchedulerDispatchCommand,
    dispatch_authorized_research_through_existing_scheduler,
    register_existing_scheduler_route_handler,
)
from context.github_research_scheduler_intake_0287 import (
    SCHEMA as INTAKE_SCHEMA,
)
from contracts.event import EventType
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler
from runtime.scheduler_route_adapter import SCHEDULER_ROUTE_REPLY_SCHEMA


def _intake() -> dict[str, object]:
    decision_id = "policy-decision:github-research-auto:abcdef"
    return {
        "schema": INTAKE_SCHEMA,
        "valid": True,
        "authorized": True,
        "status": "scheduler-request-ready",
        "policy_decision": {
            "policy_decision_id": decision_id,
            "decision": "approve",
            "automatic": True,
        },
        "scheduler_route_request": {
            "schema": "missipy.scheduler.route_adapter_request.v1",
            "request_id": "request-research-15",
            "route_id": "route-research-15",
            "task_id": "task-research-15",
            "holder": "scheduler",
            "scope": "route.write",
            "authorized": True,
            "policy_decision_id": decision_id,
            "ttl_seconds": 300,
            "activate": True,
            "requested_at": "2026-07-18T12:00:00Z",
        },
        "scheduler_dispatch_started": False,
        "laboratory_execution_started": False,
    }


def _reply(payload: object) -> dict[str, object]:
    assert isinstance(payload, dict)
    return {
        "schema": SCHEDULER_ROUTE_REPLY_SCHEMA,
        "request_id": payload["request_id"],
        "status": "ready",
        "route_id": payload["route_id"],
        "route_handle": "route-handle:test",
        "task_id": payload["task_id"],
        "holder": payload["holder"],
        "scope": payload["scope"],
        "lease_id": "lease:test",
        "lease_state": "active",
        "policy_decision_id": payload["policy_decision_id"],
        "ring_path": "/dev/shm/test",
        "mmap_status_path": "/dev/shm/test.status",
        "active_status_path": "/dev/shm/test.active",
        "lease_path": "/dev/shm/test.lease",
        "reused_existing_lease": False,
        "bus_event_count": 1,
        "bus_context_count": 1,
        "replied_at": payload["requested_at"],
    }


@pytest.mark.asyncio
async def test_authorized_research_is_emitted_through_real_scheduler_objects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_bus = EventBus()
    dispatcher = Dispatcher(event_bus)
    scheduler = Scheduler(
        PriorityQueue(),
        dispatcher,
        event_bus,
        Registry(),
    )
    ports = SimpleNamespace(scheduler=scheduler, dispatcher=dispatcher)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    observed = event_bus.subscribe(EventType.SCHEDULER_ROUTE_REQUEST)

    scheduler_task = asyncio.create_task(scheduler.run())
    await asyncio.sleep(0)
    try:
        result = await dispatch_authorized_research_through_existing_scheduler(
            GitHubResearchSchedulerDispatchCommand(
                runtime_ports=ports,  # type: ignore[arg-type]
                scheduler_intake=_intake(),
                route_request_handler=_reply,
            )
        )
        event = await asyncio.wait_for(observed.get(), timeout=1)
    finally:
        await scheduler.shutdown()
        await scheduler_task

    assert result.valid is True
    assert result.status == "route-ready"
    assert result.registration_action == "registered"
    assert result.route_reply["status"] == "ready"
    assert event.type is EventType.SCHEDULER_ROUTE_REQUEST
    assert event.source == "github.research.scheduler-intake"
    mapping = result.to_mapping()
    assert mapping["scheduler_created"] is False
    assert mapping["scheduler_started"] is False
    assert mapping["scheduler_dispatch_started"] is True
    assert mapping["scheduler_dispatch_completed"] is True
    assert mapping["laboratory_execution_started"] is False


def test_registration_is_idempotent_and_rejects_foreign_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispatcher = Dispatcher(EventBus())
    ports = SimpleNamespace(scheduler=object(), dispatcher=dispatcher)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    assert (
        register_existing_scheduler_route_handler(
            ports,  # type: ignore[arg-type]
            route_request_handler=_reply,
        )
        == "registered"
    )
    assert (
        register_existing_scheduler_route_handler(
            ports,  # type: ignore[arg-type]
            route_request_handler=_reply,
        )
        == "replay"
    )

    dispatcher.handlers[EventType.SCHEDULER_ROUTE_REQUEST] = SimpleNamespace()
    with pytest.raises(
        module.GitHubResearchSchedulerDispatchError,
        match="different handler",
    ):
        register_existing_scheduler_route_handler(
            ports,  # type: ignore[arg-type]
            route_request_handler=_reply,
        )


@pytest.mark.asyncio
async def test_stopped_scheduler_is_rejected_without_starting_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_bus = EventBus()
    dispatcher = Dispatcher(event_bus)
    scheduler = Scheduler(
        PriorityQueue(),
        dispatcher,
        event_bus,
        Registry(),
    )
    ports = SimpleNamespace(scheduler=scheduler, dispatcher=dispatcher)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    result = await dispatch_authorized_research_through_existing_scheduler(
        GitHubResearchSchedulerDispatchCommand(
            runtime_ports=ports,  # type: ignore[arg-type]
            scheduler_intake=_intake(),
            route_request_handler=_reply,
        )
    )

    assert result.valid is False
    assert result.status == "scheduler-not-running"
    assert scheduler.running is False
    assert result.to_mapping()["scheduler_started"] is False


@pytest.mark.asyncio
async def test_unauthorized_or_already_started_intake_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intake = _intake()
    intake["scheduler_dispatch_started"] = True
    ports = SimpleNamespace(scheduler=object(), dispatcher=object())
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    result = await dispatch_authorized_research_through_existing_scheduler(
        GitHubResearchSchedulerDispatchCommand(
            runtime_ports=ports,  # type: ignore[arg-type]
            scheduler_intake=intake,
        )
    )

    assert result.valid is False
    assert result.status == "rejected"
    assert result.to_mapping()["scheduler_dispatch_started"] is False


def test_event_type_and_source_keep_scheduler_as_only_orchestrator() -> None:
    source = __import__("pathlib").Path(module.__file__).read_text(
        encoding="utf-8"
    )

    assert EventType.SCHEDULER_ROUTE_REQUEST.name == "SCHEDULER_ROUTE_REQUEST"
    assert "scheduler.emit(event)" in source
    assert "ControlProxySchedulerRouteRequestHandler" in source
    assert "validate_imported_actions_runtime_ports" in source
    assert "Scheduler(" not in source
    assert "Dispatcher(" not in source
    assert "EventBus(" not in source
    assert "scheduler.run(" not in source
    assert "create_task(scheduler.run" not in source
    assert "LABORATORY_VISIT_REQUEST" not in source
    assert "handle_scheduler_route_command(" not in source
