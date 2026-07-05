from __future__ import annotations

from pathlib import Path

from runtime.controlproxy_prepare import ROUTE_PREPARE_STATUS_SCHEMA, RoutePrepareDecision
from runtime.mmap_fixed_slot_route import route_file_size
from runtime.route_generation_lock import route_generation_lock_path
from runtime.route_generation_table import load_route_generation_table
from runtime.route_runtime_manager import RouteRuntimeManager


def _decision(
    *,
    route_id: str = "route-a",
    generation: int = 1,
    action: str = "create_route_generation",
    status: str = "ready",
    slot_size: int = 512,
    slot_count: int = 2,
) -> RoutePrepareDecision:
    route_handle = None if action == "deny" else f"{route_id}@g{generation}"
    return RoutePrepareDecision(
        schema=ROUTE_PREPARE_STATUS_SCHEMA,
        request_id=f"prep:{route_id}:g{generation}",
        route_id=route_id,
        route_handle=route_handle,
        task_id="task-a",
        zone="workers",
        status=status,  # type: ignore[arg-type]
        action=action,  # type: ignore[arg-type]
        reason="pytest route runtime manager",
        required_frame_bytes=128,
        current_generation=(generation - 1) if generation > 1 else None,
        next_generation=None if action == "deny" else generation,
        current_slot_size=None,
        slot_size=slot_size if action != "deny" else None,
        slot_count=slot_count if action != "deny" else None,
        max_frame_bytes=slot_size if action != "deny" else None,
        max_ring_bytes=slot_size * slot_count * 8,
        max_prepare_ms=25,
        drain_timeout_ms=100,
        lease_switch_timeout_ms=10,
        notify="eventfd" if action != "deny" else None,
        overflow_policy="reject" if action != "deny" else None,
        decided_at="2026-07-05T00:00:00Z",
    )


def test_route_runtime_manager_materializes_generation_under_lock(tmp_path: Path) -> None:
    manager = RouteRuntimeManager.from_roots(
        controlfs_root=tmp_path / "controlfs",
        runtime_root=tmp_path / "runtime",
    )

    result = manager.handle_prepare_decision(_decision(generation=1))

    assert result.action == "materialize_generation"
    assert result.status == "candidate"
    assert result.generation == 1
    record = result.payload["record"]
    ring_path = Path(record["ring_path"])
    assert ring_path.exists()
    assert ring_path.stat().st_size == route_file_size(512, 2)
    assert route_generation_lock_path(tmp_path / "controlfs", "route-a").exists()

    table = load_route_generation_table(tmp_path / "controlfs", "route-a")
    assert table.next_generation == 2
    assert table.generations[0].state == "candidate"


def test_route_runtime_manager_runs_lifecycle_and_closed_cleanup(tmp_path: Path) -> None:
    manager = RouteRuntimeManager.from_roots(
        controlfs_root=tmp_path / "controlfs",
        runtime_root=tmp_path / "runtime",
    )
    candidate = manager.materialize_generation(_decision(generation=1))
    runtime_route_dir = Path(candidate.payload["record"]["runtime_route_dir"])
    assert runtime_route_dir.exists()

    active = manager.activate_generation(route_id="route-a", generation=1)
    assert active.action == "activate_generation"
    assert active.status == "active"

    draining = manager.mark_draining(route_id="route-a", generation=1)
    assert draining.action == "mark_draining"
    assert draining.status == "draining"

    closed = manager.mark_closed(route_id="route-a", generation=1)
    assert closed.action == "mark_closed"
    assert closed.status == "closed"

    cleanup = manager.cleanup_closed(
        route_id="route-a",
        generation=1,
        cleaned_at="2026-07-05T01:00:00Z",
    )
    assert cleanup.action == "cleanup_closed"
    assert cleanup.status == "removed"
    assert not runtime_route_dir.exists()


def test_route_runtime_manager_denied_and_reuse_decisions_have_no_runtime_effect(tmp_path: Path) -> None:
    manager = RouteRuntimeManager.from_roots(
        controlfs_root=tmp_path / "controlfs",
        runtime_root=tmp_path / "runtime",
    )

    denied = manager.handle_prepare_decision(_decision(action="deny", status="denied"))
    assert denied.action == "denied"
    assert denied.status == "no_runtime_effect"
    assert not (tmp_path / "runtime" / "routes").exists()

    reuse_decision = _decision(action="reuse_active", generation=1)
    reuse = manager.handle_prepare_decision(reuse_decision)
    assert reuse.action == "reuse_active_route"
    assert reuse.status == "no_runtime_effect"
    assert not (tmp_path / "runtime" / "routes").exists()


def test_route_runtime_manager_load_table_returns_stable_projection(tmp_path: Path) -> None:
    manager = RouteRuntimeManager.from_roots(
        controlfs_root=tmp_path / "controlfs",
        runtime_root=tmp_path / "runtime",
    )

    empty = manager.load_table("route-a")
    assert empty.action == "load_table"
    assert empty.status == "loaded"
    assert empty.payload["next_generation"] == 1

    manager.materialize_generation(_decision(generation=1))
    loaded = manager.load_table("route-a")
    assert loaded.payload["next_generation"] == 2
    assert loaded.payload["generations"][0]["route_handle"] == "route-a@g1"
