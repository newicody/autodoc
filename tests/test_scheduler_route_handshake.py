import json
from pathlib import Path

import pytest

from context.baby_fork_controlfs import build_route_sizing_hints_from_messages, write_baby_fork_desired_manifests
from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection
from runtime.controlproxy_route_lease import load_route_lease
from runtime.fake_route_transport import load_fake_bus_messages
from runtime.scheduler_route_handshake import SchedulerRouteHandshakeError, prepare_route_for_scheduler
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


def test_prepare_route_for_scheduler_pumps_acquires_and_activates_lease(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    result = prepare_route_for_scheduler(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        route_id="baby_fork.retrieval",
        holder="scheduler",
        scope="route.write",
    )

    assert result.schema == "missipy.scheduler.route_handshake.v1"
    assert result.route_id == "baby_fork.retrieval"
    assert result.route_handle == "baby_fork.retrieval@g1"
    assert result.lease_state == "active"
    assert result.reused_existing_lease is False
    assert result.pump_materialized_count == 3
    assert Path(result.ring_path).exists()
    assert Path(result.lease_path).exists()

    lease = load_route_lease(controlfs_root, "baby_fork.retrieval")
    assert lease.state == "active"
    assert lease.holder == "scheduler"
    assert lease.scope == "route.write"


def test_prepare_route_for_scheduler_is_idempotent_for_same_holder_scope(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    first = prepare_route_for_scheduler(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        route_id="baby_fork.retrieval",
        holder="scheduler",
        scope="route.write",
    )
    second = prepare_route_for_scheduler(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        route_id="baby_fork.retrieval",
        holder="scheduler",
        scope="route.write",
    )

    assert second.reused_existing_lease is True
    assert second.lease_id == first.lease_id
    assert second.lease_state == "active"
    assert second.pump_materialized_count == 0
    assert second.pump_skipped_count == 3


def test_prepare_route_for_scheduler_rejects_different_holder(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    prepare_route_for_scheduler(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        route_id="baby_fork.retrieval",
        holder="scheduler",
        scope="route.write",
    )

    with pytest.raises(SchedulerRouteHandshakeError, match="different holder/scope"):
        prepare_route_for_scheduler(
            controlfs_root=controlfs_root,
            runtime_root=runtime_root,
            route_id="baby_fork.retrieval",
            holder="other_scheduler",
            scope="route.write",
        )


def test_prepare_route_for_scheduler_rejects_different_scope(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    prepare_route_for_scheduler(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        route_id="baby_fork.retrieval",
        holder="scheduler",
        scope="route.write",
    )

    with pytest.raises(SchedulerRouteHandshakeError, match="different holder/scope"):
        prepare_route_for_scheduler(
            controlfs_root=controlfs_root,
            runtime_root=runtime_root,
            route_id="baby_fork.retrieval",
            holder="scheduler",
            scope="route.read",
        )


def test_prepare_route_for_scheduler_writes_bus_facts(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    result = prepare_route_for_scheduler(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        route_id="baby_fork.retrieval",
        holder="scheduler",
        scope="route.write",
    )

    events = load_fake_bus_messages(runtime_root / "event.bus.jsonl")
    contexts = load_fake_bus_messages(runtime_root / "context.bus.jsonl")

    assert result.bus_event_count == 4
    assert result.bus_context_count == 4
    assert all(isinstance(event, EventBusMessage) for event in events)
    assert all(isinstance(context, ContextBusMessage) for context in contexts)
    assert "scheduler.route.handshake.ready" in {event.topic for event in events}
    assert "scheduler.route.lease.active" in {context.topic for context in contexts}


def test_prepare_route_for_scheduler_errors_when_route_missing(tmp_path: Path) -> None:
    with pytest.raises(SchedulerRouteHandshakeError, match="route is not active after pump"):
        prepare_route_for_scheduler(
            controlfs_root=tmp_path / "controlfs",
            runtime_root=tmp_path / "runtime",
            route_id="baby_fork.retrieval",
            holder="scheduler",
            scope="route.write",
        )
