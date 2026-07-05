from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.controlproxy_prepare import ROUTE_PREPARE_STATUS_SCHEMA, RoutePrepareDecision
from runtime.route_generation_lifecycle import (
    ROUTE_GENERATION_CLEANUP_SCHEMA,
    RouteGenerationLifecycleError,
    activate_route_generation,
    cleanup_closed_route_generation,
    mark_route_generation_closed,
    mark_route_generation_draining,
    route_generation_cleanup_path,
)
from runtime.route_generation_table import (
    load_route_generation_table,
    materialize_route_generation_candidate,
    route_generation_status_path,
)


def _decision(
    *,
    route_id: str = "route-a",
    generation: int = 1,
    action: str = "create_route_generation",
    slot_size: int = 512,
    slot_count: int = 2,
) -> RoutePrepareDecision:
    return RoutePrepareDecision(
        schema=ROUTE_PREPARE_STATUS_SCHEMA,
        request_id=f"prep:{route_id}:g{generation}",
        route_id=route_id,
        route_handle=f"{route_id}@g{generation}",
        task_id="task-a",
        zone="workers",
        status="ready",
        action=action,  # type: ignore[arg-type]
        reason="pytest generation lifecycle",
        required_frame_bytes=128,
        current_generation=(generation - 1) if generation > 1 else None,
        next_generation=generation,
        current_slot_size=None,
        slot_size=slot_size,
        slot_count=slot_count,
        max_frame_bytes=slot_size,
        max_ring_bytes=slot_size * slot_count * 8,
        max_prepare_ms=25,
        drain_timeout_ms=100,
        lease_switch_timeout_ms=10,
        notify="eventfd",
        overflow_policy="reject",
        decided_at="2026-07-05T00:00:00Z",
    )


def test_route_generation_lifecycle_drains_closes_and_cleans_runtime_dir(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"

    candidate = materialize_route_generation_candidate(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=_decision(generation=1),
    )
    runtime_route_dir = Path(candidate.record.runtime_route_dir)
    ring_path = Path(candidate.record.ring_path)
    assert runtime_route_dir.exists()
    assert ring_path.exists()

    active = activate_route_generation(
        controlfs_root=controlfs_root,
        route_id="route-a",
        generation=1,
    )
    assert active.previous_state == "candidate"
    assert active.record.state == "active"
    assert active.table.active_generation == 1

    draining = mark_route_generation_draining(
        controlfs_root=controlfs_root,
        route_id="route-a",
        generation=1,
    )
    assert draining.previous_state == "active"
    assert draining.record.state == "draining"
    assert draining.table.active_generation is None

    closed = mark_route_generation_closed(
        controlfs_root=controlfs_root,
        route_id="route-a",
        generation=1,
    )
    assert closed.previous_state == "draining"
    assert closed.record.state == "closed"

    status = json.loads(route_generation_status_path(controlfs_root, "route-a", 1).read_text(encoding="utf-8"))
    assert status["state"] == "closed"

    cleanup = cleanup_closed_route_generation(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        route_id="route-a",
        generation=1,
        cleaned_at="2026-07-05T01:00:00Z",
    )
    assert cleanup.schema == ROUTE_GENERATION_CLEANUP_SCHEMA
    assert cleanup.removed_runtime_route_dir is True
    assert not runtime_route_dir.exists()
    assert not ring_path.exists()

    cleanup_payload = json.loads(route_generation_cleanup_path(controlfs_root, "route-a", 1).read_text(encoding="utf-8"))
    assert cleanup_payload["schema"] == ROUTE_GENERATION_CLEANUP_SCHEMA
    assert cleanup_payload["generation"] == 1
    assert cleanup_payload["removed_runtime_route_dir"] is True

    loaded = load_route_generation_table(controlfs_root, "route-a")
    assert loaded.active_generation is None
    assert loaded.generations[0].state == "closed"


def test_route_generation_lifecycle_rejects_unsafe_transitions(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    materialize_route_generation_candidate(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=_decision(generation=1),
    )

    with pytest.raises(RouteGenerationLifecycleError, match="cleanup is allowed for closed generations only"):
        cleanup_closed_route_generation(
            controlfs_root=controlfs_root,
            runtime_root=runtime_root,
            route_id="route-a",
            generation=1,
        )

    with pytest.raises(RouteGenerationLifecycleError, match="only draining generations"):
        mark_route_generation_closed(
            controlfs_root=controlfs_root,
            route_id="route-a",
            generation=1,
        )

    activate_route_generation(controlfs_root=controlfs_root, route_id="route-a", generation=1)
    with pytest.raises(RouteGenerationLifecycleError, match="only candidate generations"):
        activate_route_generation(controlfs_root=controlfs_root, route_id="route-a", generation=1)


def test_route_generation_lifecycle_requires_active_generation_to_drain_before_next_active(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"

    materialize_route_generation_candidate(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=_decision(generation=1),
    )
    activate_route_generation(controlfs_root=controlfs_root, route_id="route-a", generation=1)

    materialize_route_generation_candidate(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=_decision(generation=2, action="create_next_generation", slot_size=1024),
    )

    with pytest.raises(RouteGenerationLifecycleError, match="another active generation must be drained first"):
        activate_route_generation(controlfs_root=controlfs_root, route_id="route-a", generation=2)
