import json
from pathlib import Path

import pytest

from context.baby_fork_controlfs import (
    build_baby_fork_routeproxy_plan,
    build_route_sizing_hints_from_messages,
    write_baby_fork_desired_manifests,
)
from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection
from runtime.controlfs_manifest import RouteManifest, route_manifest_path
from runtime.controlproxy_active_routes import (
    ACTIVE_ROUTE_STATUS_SCHEMA,
    ActiveRouteMaterializationError,
    active_manifest_path,
    active_route_summary,
    active_status_path,
    build_post_materialization_plan,
    load_active_route_status,
    materialize_active_route,
    materialize_active_routes,
)
from runtime.controlproxy_prepare import decide_route_prepare, route_prepare_request_from_message
from runtime.mmap_fixed_slot_route import MmapFixedSlotRoute
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
        "message_id": f"msg:{route_id}.reply",
        "kind": "reply",
        "source": "retrieval_worker" if route_id.endswith("retrieval") else "variant_generator_stub",
        "target": "scheduler",
        "occurred_at": "2026-07-04T20:00:00Z",
        "payload_schema": "missipy.baby_fork.route_reply.v1",
        "payload": {
            "context_id": "ctx-baby-fork-001",
            "retrieved_ids": ["baby-silicone-fork", "rounded-stainless-soft-handle"],
            "rejected_ids": ["nasa-antenna"],
        },
    }


def _desired_manifest(controlfs_root: Path, route_id: str = "baby_fork.retrieval") -> RouteManifest:
    projection = build_baby_fork_runtime_projection(_report())
    hints = build_route_sizing_hints_from_messages(projection.routes)
    write_baby_fork_desired_manifests(
        controlfs_root,
        context_id="ctx-baby-fork-001",
        sizing_hints=hints,
    )
    return RouteManifest.from_path(route_manifest_path(controlfs_root, route_id))


def _decision_for_manifest(manifest: RouteManifest):
    request = route_prepare_request_from_message(
        _message(manifest.route_id),
        task_id=manifest.task_id,
        zone=manifest.zone,
        scope=manifest.scope,
    )
    decision = decide_route_prepare(request)
    # Use the exact accepted manifest sizing so materialization validates the seam.
    return type(decision)(
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


def test_materialize_active_route_writes_mmap_and_controlfs_active_state(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    manifest = _desired_manifest(controlfs_root)
    decision = _decision_for_manifest(manifest)

    record = materialize_active_route(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=decision,
        desired_manifest=manifest,
    )

    assert record.schema == ACTIVE_ROUTE_STATUS_SCHEMA
    assert record.route_id == "baby_fork.retrieval"
    assert record.route_handle == "baby_fork.retrieval@g1"
    assert record.state == "active"
    assert record.lease_state == "not_leased"
    assert Path(record.ring_path).exists()
    assert Path(record.mmap_status_path).exists()
    assert Path(record.active_manifest_path).exists()
    assert Path(record.active_status_path).exists()

    loaded = load_active_route_status(record.active_status_path)
    assert loaded == record

    active_manifest = RouteManifest.from_path(active_manifest_path(controlfs_root, "baby_fork.retrieval"))
    assert active_manifest.to_mapping() == manifest.to_mapping()


def test_materialized_active_route_can_reconcile_as_noop(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    manifest = _desired_manifest(controlfs_root)
    decision = _decision_for_manifest(manifest)

    materialize_active_route(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=decision,
        desired_manifest=manifest,
    )

    plan = build_post_materialization_plan(controlfs_root)
    retrieval_items = [item for item in plan.items if item.route_id == "baby_fork.retrieval"]

    assert len(retrieval_items) == 1
    assert retrieval_items[0].action == "noop"


def test_active_route_mmap_can_accept_frame_after_materialization(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    manifest = _desired_manifest(controlfs_root)
    decision = _decision_for_manifest(manifest)
    record = materialize_active_route(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=decision,
        desired_manifest=manifest,
    )

    route = MmapFixedSlotRoute.open(
        record.ring_path,
        route_handle=record.route_handle,
        status_path=record.mmap_status_path,
        overflow_policy=record.overflow_policy,
    )
    try:
        route.write_message(_message("baby_fork.retrieval"))
        drained = route.drain()
        assert len(drained) == 1
        assert drained[0].message().route_id == "baby_fork.retrieval"
    finally:
        route.close()


def test_materializer_rejects_mismatched_manifest(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    manifest = _desired_manifest(controlfs_root, "baby_fork.retrieval")
    other_manifest = _desired_manifest(controlfs_root, "baby_fork.variant_stub")
    decision = _decision_for_manifest(manifest)

    with pytest.raises(ActiveRouteMaterializationError, match="route_id"):
        materialize_active_route(
            controlfs_root=controlfs_root,
            runtime_root=tmp_path / "runtime",
            decision=decision,
            desired_manifest=other_manifest,
        )


def test_materialize_active_routes_summary(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    manifest = _desired_manifest(controlfs_root)
    decision = _decision_for_manifest(manifest)

    records = materialize_active_routes(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        pairs=[(decision, manifest)],
    )
    summary = active_route_summary(records)

    assert summary["active_route_count"] == 1
    assert summary["route_handles"] == ["baby_fork.retrieval@g1"]
    assert summary["routes"][0]["implementation_stage"] == "file_backed_mmap_fixed_slot"
