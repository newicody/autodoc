from pathlib import Path

import pytest

from context.baby_fork_controlfs import build_route_sizing_hints_from_messages, write_baby_fork_desired_manifests
from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection
from runtime.fake_route_transport import load_fake_bus_messages
from runtime.scheduler_route_adapter import (
    SCHEDULER_ROUTE_REPLY_SCHEMA,
    SCHEDULER_ROUTE_REQUEST_SCHEMA,
    SchedulerRouteAdapterError,
    SchedulerRouteRequest,
    handle_scheduler_route_request,
    scheduler_route_request_mapping,
)
from runtime.shm_runtime_schema import ContextBusMessage, EventBusMessage


def _report() -> dict:
    return {
        "retrieval": {
            "retrieved_ids": ["baby-silicone-fork", "rounded-stainless-soft-handle"],
            "rejected_ids": ["nasa-antenna"],
        },
        "variant_generator_stub": {
            "generated_variants": [
                {"variant_id": "variant-1"},
                {"variant_id": "variant-2"},
            ]
        },
        "final_context": {
            "context_id": "ctx-baby-fork-001",
            "context_version": 2,
            "selected_variant_id": "variant-1",
        },
    }


def _write_desired(controlfs_root: Path) -> None:
    projection = build_baby_fork_runtime_projection(_report())
    hints = build_route_sizing_hints_from_messages(projection.routes)
    write_baby_fork_desired_manifests(
        controlfs_root,
        context_id="ctx-baby-fork-001",
        sizing_hints=hints,
    )


def _request() -> dict:
    return scheduler_route_request_mapping(
        request_id="req:scheduler:route:001",
        route_id="baby_fork.retrieval",
        task_id="ctx-baby-fork-001",
        holder="scheduler",
        scope="route.write",
        policy_decision_id="policy:allow:route:001",
    )


def test_scheduler_route_request_from_mapping_requires_authorized_policy() -> None:
    request = SchedulerRouteRequest.from_mapping(_request())

    assert request.schema == SCHEDULER_ROUTE_REQUEST_SCHEMA
    assert request.authorized is True
    assert request.policy_decision_id == "policy:allow:route:001"

    raw = _request()
    raw["authorized"] = False
    with pytest.raises(SchedulerRouteAdapterError, match="already be authorized"):
        SchedulerRouteRequest.from_mapping(raw)


def test_handle_scheduler_route_request_returns_ready_reply(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    reply = handle_scheduler_route_request(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        request=_request(),
    )

    assert reply.schema == SCHEDULER_ROUTE_REPLY_SCHEMA
    assert reply.status == "ready"
    assert reply.route_id == "baby_fork.retrieval"
    assert reply.route_handle == "baby_fork.retrieval@g1"
    assert reply.lease_state == "active"
    assert reply.policy_decision_id == "policy:allow:route:001"
    assert Path(reply.ring_path).exists()
    assert Path(reply.lease_path).exists()
    assert reply.bus_event_count == 5
    assert reply.bus_context_count == 5


def test_handle_scheduler_route_request_is_idempotent_for_same_request(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    first = handle_scheduler_route_request(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        request=_request(),
    )
    second = handle_scheduler_route_request(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        request=_request(),
    )

    assert second.status == "ready"
    assert second.lease_id == first.lease_id
    assert second.reused_existing_lease is True


def test_handle_scheduler_route_request_rejects_conflicting_scope(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    handle_scheduler_route_request(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        request=_request(),
    )

    other = _request()
    other["scope"] = "route.read"
    other["request_id"] = "req:scheduler:route:002"

    with pytest.raises(Exception, match="different holder/scope"):
        handle_scheduler_route_request(
            controlfs_root=controlfs_root,
            runtime_root=runtime_root,
            request=other,
        )


def test_scheduler_route_adapter_writes_bus_facts(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    handle_scheduler_route_request(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        request=_request(),
    )

    events = load_fake_bus_messages(runtime_root / "event.bus.jsonl")
    contexts = load_fake_bus_messages(runtime_root / "context.bus.jsonl")

    assert all(isinstance(event, EventBusMessage) for event in events)
    assert all(isinstance(context, ContextBusMessage) for context in contexts)
    assert "scheduler.route.adapter.ready" in {event.topic for event in events}
    assert "scheduler.route.adapter.reply" in {context.topic for context in contexts}
    assert "scheduler.route.handshake.ready" in {event.topic for event in events}
    assert "controlproxy.pump.route_materialized" in {event.topic for event in events}
