from __future__ import annotations

from pathlib import Path

import pytest

from contracts.event import Event, EventType
from runtime.controlproxy_prepare import ROUTE_PREPARE_STATUS_SCHEMA, RoutePrepareDecision
from runtime.controlproxy_route_runtime_handler import (
    build_controlproxy_route_runtime_request_handler,
)
from runtime.controlproxy_scheduler_handler import ControlProxySchedulerRouteRequestHandler
from runtime.mmap_fixed_slot_route import route_file_size
from runtime.route_generation_table import load_route_generation_table
from runtime.route_runtime_manager import RouteRuntimeManager


def _decision(
    *,
    route_id: str = "route-live",
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
        task_id="task-live",
        zone="workers",
        status="ready",
        action=action,  # type: ignore[arg-type]
        reason="0108 live path route runtime scenario",
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


def _payload(decision: RoutePrepareDecision) -> dict[str, object]:
    return {
        "route_id": decision.route_id,
        "zone": decision.zone,
        "policy_decision_id": f"policy:{decision.route_id}:g{decision.next_generation}",
        "authorized": True,
        "source": "pytest.scheduler",
        "decision": decision.to_mapping(),
    }


def _event(payload: object) -> Event:
    return Event(
        EventType.CONTEXT_REQUEST,
        source="pytest.scheduler",
        dest="controlproxy.route",
        payload=payload,
    )


@pytest.mark.asyncio
async def test_controlproxy_route_runtime_live_path_materializes_g1_g2_then_cleans_closed_g1(
    tmp_path: Path,
) -> None:
    """Walking-skeleton scenario for the simplified ControlProxy route path.

    This is intentionally not a full Scheduler.run() test. It validates the
    durable slice after Dispatcher has selected the thin Handler:

    ControlProxySchedulerRouteRequestHandler -> RouteRuntimeManager ->
    ControlFS + mmap/eventfd data plane.
    """

    manager = RouteRuntimeManager.from_roots(
        controlfs_root=tmp_path / "controlfs",
        runtime_root=tmp_path / "runtime",
    )
    handler = ControlProxySchedulerRouteRequestHandler(
        route_request_handler=build_controlproxy_route_runtime_request_handler(manager)
    )

    g1 = await handler.handle(
        _event(
            _payload(
                _decision(generation=1, action="create_route_generation", slot_size=512, slot_count=2)
            )
        )
    )

    assert g1.action == "materialize_generation"
    assert g1.status == "candidate"
    assert g1.generation == 1
    g1_record = g1.payload["record"]
    g1_ring = Path(g1_record["ring_path"])
    g1_runtime_dir = Path(g1_record["runtime_route_dir"])
    assert g1_ring.exists()
    assert g1_ring.stat().st_size == route_file_size(512, 2)

    active = manager.activate_generation(route_id="route-live", generation=1)
    assert active.action == "activate_generation"
    assert active.status == "active"

    g2 = await handler.handle(
        _event(
            _payload(
                _decision(
                    generation=2,
                    action="create_next_generation",
                    slot_size=1024,
                    slot_count=3,
                )
            )
        )
    )

    assert g2.action == "materialize_generation"
    assert g2.status == "candidate"
    assert g2.generation == 2
    g2_record = g2.payload["record"]
    g2_ring = Path(g2_record["ring_path"])
    assert g2_ring.exists()
    assert g2_ring.stat().st_size == route_file_size(1024, 3)

    # g2/g3 style updates are new generations. The active g1 ring is never
    # resized in place.
    assert g1_ring.exists()
    assert g1_ring.stat().st_size == route_file_size(512, 2)

    draining = manager.mark_draining(route_id="route-live", generation=1)
    assert draining.action == "mark_draining"
    assert draining.status == "draining"

    closed = manager.mark_closed(route_id="route-live", generation=1)
    assert closed.action == "mark_closed"
    assert closed.status == "closed"

    cleanup = manager.cleanup_closed(route_id="route-live", generation=1)
    assert cleanup.action == "cleanup_closed"
    assert cleanup.status == "removed"
    assert not g1_runtime_dir.exists()
    assert g2_ring.exists()

    table = load_route_generation_table(tmp_path / "controlfs", "route-live")
    assert table.next_generation == 3
    assert [record.generation for record in table.generations] == [1, 2]
    assert [record.state for record in table.generations] == ["closed", "candidate"]
