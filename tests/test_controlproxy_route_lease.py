import json
from pathlib import Path

import pytest

from context.baby_fork_controlfs import build_route_sizing_hints_from_messages, write_baby_fork_desired_manifests
from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection
from runtime.controlfs_manifest import RouteManifest, route_manifest_path
from runtime.controlproxy_active_routes import active_status_path, materialize_active_route
from runtime.controlproxy_prepare import decide_route_prepare, route_prepare_request_from_message
from runtime.controlproxy_route_lease import (
    ROUTE_LEASE_SCHEMA,
    RouteLeaseTransitionError,
    acquire_route_lease,
    activate_route_lease,
    begin_route_drain,
    close_route_lease,
    lease_path,
    load_route_lease,
    route_lease_summary,
    transition_route_lease,
)
from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA


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


def _message(route_id: str = "baby_fork.retrieval") -> dict:
    return {
        "schema": ROUTE_MESSAGE_SCHEMA,
        "route_id": route_id,
        "message_id": "msg:baby_fork.retrieval.reply",
        "kind": "reply",
        "source": "retrieval_worker",
        "target": "scheduler",
        "occurred_at": "2026-07-04T20:00:00Z",
        "payload_schema": "missipy.baby_fork.route_reply.v1",
        "payload": {
            "context_id": "ctx-baby-fork-001",
            "retrieved_ids": ["baby-silicone-fork", "rounded-stainless-soft-handle"],
            "rejected_ids": ["nasa-antenna"],
        },
    }


def _materialize(tmp_path: Path):
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    projection = build_baby_fork_runtime_projection(_report())
    hints = build_route_sizing_hints_from_messages(projection.routes)
    write_baby_fork_desired_manifests(
        controlfs_root,
        context_id="ctx-baby-fork-001",
        sizing_hints=hints,
    )
    manifest = RouteManifest.from_path(route_manifest_path(controlfs_root, "baby_fork.retrieval"))
    request = route_prepare_request_from_message(
        _message(),
        task_id=manifest.task_id,
        zone=manifest.zone,
        scope=manifest.scope,
    )
    decision = decide_route_prepare(request)
    decision = type(decision)(
        schema=decision.schema,
        request_id=decision.request_id,
        route_id=decision.route_id,
        route_handle=decision.route_handle,
        task_id=decision.task_id,
        zone=decision.zone,
        status=decision.status,
        action=decision.action,
        reason=decision.reason,
        required_frame_bytes=decision.required_frame_bytes,
        current_generation=decision.current_generation,
        next_generation=decision.next_generation,
        current_slot_size=decision.current_slot_size,
        slot_size=manifest.slot_size,
        slot_count=manifest.slot_count,
        max_frame_bytes=manifest.max_frame_bytes,
        max_ring_bytes=decision.max_ring_bytes,
        max_prepare_ms=decision.max_prepare_ms,
        drain_timeout_ms=decision.drain_timeout_ms,
        lease_switch_timeout_ms=decision.lease_switch_timeout_ms,
        notify=manifest.notify,
        overflow_policy=manifest.overflow_policy,
        decided_at=decision.decided_at,
    )
    record = materialize_active_route(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=decision,
        desired_manifest=manifest,
    )
    return controlfs_root, record


def test_acquire_route_lease_writes_lease_json_and_updates_status(tmp_path: Path) -> None:
    controlfs_root, record = _materialize(tmp_path)

    lease = acquire_route_lease(
        controlfs_root=controlfs_root,
        route_id=record.route_id,
        holder="scheduler",
        scope="route.write",
        lease_id="lease:baby_fork.retrieval:g1:scheduler",
    )

    assert lease.schema == ROUTE_LEASE_SCHEMA
    assert lease.state == "leased"
    assert lease.route_handle == "baby_fork.retrieval@g1"
    assert lease.holder == "scheduler"
    assert lease_path(controlfs_root, record.route_id).exists()

    status = json.loads(active_status_path(controlfs_root, record.route_id).read_text(encoding="utf-8"))
    assert status["lease_state"] == "leased"
    assert status["current_lease_id"] == lease.lease_id
    assert status["current_lease_holder"] == "scheduler"


def test_route_lease_state_machine_full_path(tmp_path: Path) -> None:
    controlfs_root, record = _materialize(tmp_path)

    acquire_route_lease(controlfs_root=controlfs_root, route_id=record.route_id, holder="scheduler", scope="route.write")
    t1 = activate_route_lease(controlfs_root=controlfs_root, route_id=record.route_id)
    t2 = begin_route_drain(controlfs_root=controlfs_root, route_id=record.route_id)
    t3 = close_route_lease(controlfs_root=controlfs_root, route_id=record.route_id)

    assert (t1.previous_state, t1.next_state) == ("leased", "active")
    assert (t2.previous_state, t2.next_state) == ("active", "draining")
    assert (t3.previous_state, t3.next_state) == ("draining", "closed")
    assert load_route_lease(controlfs_root, record.route_id).state == "closed"

    status = json.loads(active_status_path(controlfs_root, record.route_id).read_text(encoding="utf-8"))
    assert status["lease_state"] == "closed"
    assert status["state"] == "closed"


def test_route_lease_allows_leased_to_closed_shortcut(tmp_path: Path) -> None:
    controlfs_root, record = _materialize(tmp_path)
    acquire_route_lease(controlfs_root=controlfs_root, route_id=record.route_id, holder="scheduler", scope="route.write")
    transition = close_route_lease(controlfs_root=controlfs_root, route_id=record.route_id)
    assert (transition.previous_state, transition.next_state) == ("leased", "closed")


def test_route_lease_rejects_invalid_transition_without_lease(tmp_path: Path) -> None:
    controlfs_root, record = _materialize(tmp_path)

    with pytest.raises(FileNotFoundError):
        transition_route_lease(controlfs_root=controlfs_root, route_id=record.route_id, next_state="active")


def test_route_lease_rejects_double_acquire(tmp_path: Path) -> None:
    controlfs_root, record = _materialize(tmp_path)

    acquire_route_lease(controlfs_root=controlfs_root, route_id=record.route_id, holder="scheduler", scope="route.write")

    with pytest.raises(RouteLeaseTransitionError, match="leased -> leased"):
        acquire_route_lease(controlfs_root=controlfs_root, route_id=record.route_id, holder="scheduler", scope="route.write")


def test_route_lease_rejects_active_to_leased(tmp_path: Path) -> None:
    controlfs_root, record = _materialize(tmp_path)

    acquire_route_lease(controlfs_root=controlfs_root, route_id=record.route_id, holder="scheduler", scope="route.write")
    activate_route_lease(controlfs_root=controlfs_root, route_id=record.route_id)

    with pytest.raises(RouteLeaseTransitionError, match="active -> leased"):
        transition_route_lease(controlfs_root=controlfs_root, route_id=record.route_id, next_state="leased")


def test_route_lease_summary(tmp_path: Path) -> None:
    controlfs_root, record = _materialize(tmp_path)

    lease = acquire_route_lease(controlfs_root=controlfs_root, route_id=record.route_id, holder="scheduler", scope="route.write")
    summary = route_lease_summary(controlfs_root, record.route_id)

    assert summary["route_id"] == "baby_fork.retrieval"
    assert summary["lease_state"] == "leased"
    assert summary["current_lease_id"] == lease.lease_id
    assert summary["current_lease_holder"] == "scheduler"
    assert summary["lease"]["state"] == "leased"
