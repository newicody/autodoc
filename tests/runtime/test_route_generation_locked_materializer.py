from __future__ import annotations

from pathlib import Path

import pytest

from runtime.controlproxy_prepare import ROUTE_PREPARE_STATUS_SCHEMA, RoutePrepareDecision
from runtime.mmap_fixed_slot_route import route_dir_for_handle, route_file_size
from runtime.route_generation_lock import (
    RouteGenerationFileLock,
    RouteGenerationLockUnavailable,
    route_generation_lock_path,
)
from runtime.route_generation_locked_materializer import (
    materialize_route_generation_candidate_with_lock,
)
from runtime.route_generation_table import load_route_generation_table, next_generation_for_route


def _decision(
    *,
    route_id: str = "route-a",
    generation: int = 1,
    action: str = "create_route_generation",
    slot_size: int = 512,
    slot_count: int = 2,
    status: str = "ready",
) -> RoutePrepareDecision:
    return RoutePrepareDecision(
        schema=ROUTE_PREPARE_STATUS_SCHEMA,
        request_id=f"prep:{route_id}:g{generation}",
        route_id=route_id,
        route_handle=f"{route_id}@g{generation}",
        task_id="task-a",
        zone="workers",
        status=status,  # type: ignore[arg-type]
        action=action,  # type: ignore[arg-type]
        reason="pytest locked generation allocation",
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


def test_locked_materializer_materializes_g1_then_g2_under_route_lock(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"

    first = materialize_route_generation_candidate_with_lock(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=_decision(generation=1, slot_size=512, slot_count=2),
    )

    g1_ring = Path(first.record.ring_path)
    assert g1_ring.exists()
    assert g1_ring.stat().st_size == route_file_size(512, 2)
    assert route_generation_lock_path(controlfs_root, "route-a").exists()
    assert first.table.next_generation == 2

    second = materialize_route_generation_candidate_with_lock(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=_decision(
            generation=2,
            action="create_next_generation",
            slot_size=1024,
            slot_count=3,
        ),
    )

    assert g1_ring.stat().st_size == route_file_size(512, 2)
    assert Path(second.record.ring_path).stat().st_size == route_file_size(1024, 3)
    assert second.record.route_handle == "route-a@g2"
    assert second.table.next_generation == 3
    assert [record.generation for record in second.table.generations] == [1, 2]
    assert next_generation_for_route(controlfs_root, "route-a") == 3


def test_locked_materializer_refuses_allocation_when_route_lock_is_held(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"

    with RouteGenerationFileLock(controlfs_root=controlfs_root, route_id="route-a"):
        with pytest.raises(RouteGenerationLockUnavailable):
            materialize_route_generation_candidate_with_lock(
                controlfs_root=controlfs_root,
                runtime_root=runtime_root,
                decision=_decision(generation=1),
                blocking=False,
            )

    assert not (route_dir_for_handle(runtime_root, "route-a@g1") / "ring.bin").exists()
    assert next_generation_for_route(controlfs_root, "route-a") == 1


def test_locked_materializer_releases_lock_after_table_error(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"

    with pytest.raises(Exception, match="only ready decisions"):
        materialize_route_generation_candidate_with_lock(
            controlfs_root=controlfs_root,
            runtime_root=runtime_root,
            decision=_decision(status="denied"),
        )

    result = materialize_route_generation_candidate_with_lock(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=_decision(generation=1),
        blocking=False,
    )

    assert result.record.generation == 1
    assert load_route_generation_table(controlfs_root, "route-a").next_generation == 2
