from __future__ import annotations

from pathlib import Path

import pytest

from runtime.controlproxy_prepare import ROUTE_PREPARE_STATUS_SCHEMA, RoutePrepareDecision
from runtime.mmap_fixed_slot_route import route_file_size
from runtime.route_generation_table import (
    RouteGenerationTableError,
    load_route_generation_table,
    materialize_route_generation_candidate,
    next_generation_for_route,
    route_generation_state_path,
    route_generation_status_path,
    route_handle_for_generation,
)


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
        reason="pytest generation allocation",
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


def test_generation_table_materializes_g1_then_g2_without_live_resize(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"

    first = materialize_route_generation_candidate(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=_decision(generation=1, slot_size=512, slot_count=2),
    )

    g1_ring = Path(first.record.ring_path)
    assert first.record.generation == 1
    assert first.record.state == "candidate"
    assert first.record.route_handle == "route-a@g1"
    assert g1_ring.exists()
    assert g1_ring.stat().st_size == route_file_size(512, 2)
    assert first.table.active_generation is None
    assert first.table.next_generation == 2
    assert route_generation_state_path(controlfs_root, "route-a").exists()
    assert route_generation_status_path(controlfs_root, "route-a", 1).exists()

    second = materialize_route_generation_candidate(
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


@pytest.mark.parametrize(
    ("decision", "message"),
    [
        (_decision(status="denied"), "only ready decisions"),
        (_decision(action="reuse_active"), "allocate generations"),
        (_decision(generation=1, route_id="route-a"), "table next_generation"),
    ],
)
def test_generation_table_rejects_invalid_or_stale_allocations(
    tmp_path: Path,
    decision: RoutePrepareDecision,
    message: str,
) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"

    if message == "table next_generation":
        materialize_route_generation_candidate(
            controlfs_root=controlfs_root,
            runtime_root=runtime_root,
            decision=_decision(generation=1),
        )

    with pytest.raises(RouteGenerationTableError, match=message):
        materialize_route_generation_candidate(
            controlfs_root=controlfs_root,
            runtime_root=runtime_root,
            decision=decision,
        )


def test_generation_table_rejects_wrong_handle_for_allocated_generation(tmp_path: Path) -> None:
    decision = _decision(generation=1)
    wrong = RoutePrepareDecision(
        **{
            **decision.to_mapping(),
            "route_handle": "route-a@g2",
            "current_generation": decision.current_generation,
            "current_slot_size": decision.current_slot_size,
            "slot_count": decision.slot_count,
            "max_frame_bytes": decision.max_frame_bytes,
            "notify": decision.notify,
            "overflow_policy": decision.overflow_policy,
        }
    )

    with pytest.raises(RouteGenerationTableError, match="route_handle"):
        materialize_route_generation_candidate(
            controlfs_root=tmp_path / "controlfs",
            runtime_root=tmp_path / "runtime",
            decision=wrong,
        )


def test_generation_table_roundtrip_and_handle_helpers(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"

    assert route_handle_for_generation("route-a", 3) == "route-a@g3"
    assert next_generation_for_route(controlfs_root, "route-a") == 1

    materialize_route_generation_candidate(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=_decision(generation=1),
    )

    loaded = load_route_generation_table(controlfs_root, "route-a")
    assert loaded.route_id == "route-a"
    assert loaded.next_generation == 2
    assert loaded.generations[0].route_handle == "route-a@g1"
