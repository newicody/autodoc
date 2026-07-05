from __future__ import annotations

import pytest

from context.route_proxy_flow_control_contract import (
    RouteContextGenerationFence,
    RouteProxyLease,
    RouteProxyObservationFact,
    RouteWriterPermit,
    build_context_generation_fence,
    build_route_proxy_flow_control_packet,
)


def test_route_proxy_flow_control_packet_grants_writer_without_touching_dev_shm() -> None:
    packet = build_route_proxy_flow_control_packet(
        route_ref="route:deliberation/cycle-1/round-1/opinion-thermal",
        owner_ref="specialist:thermal",
        context_ref="cycle-state:cycle-1",
        context_generation=3,
        priority=900,
        dev_shm_path="/dev/shm/autodoc/routes/deliberation/cycle-1/round-1/opinion-thermal.frame",
        mirrored_registry_refs=("vector-registry:default", "sql:context-store"),
    )

    data = packet.to_mapping()
    assert data["scheduler_is_orchestrator"] is True
    assert data["route_proxy_is_fast_data_plane_control"] is True
    assert data["event_bus_observation_only"] is True
    assert data["sql_is_durable_authority"] is True
    assert data["dev_shm_future_grid_seam"] is True
    assert packet.writer_permit.write_allowed is True
    assert packet.zone_state.pressure_level == "low"
    assert packet.registry_snapshot.mirrored_registry_refs == ("vector-registry:default", "sql:context-store")
    assert {fact.kind for fact in packet.observation_facts} == {
        "route.lease_granted",
        "route.writer_permit_granted",
        "route.registry_snapshot_published",
    }


def test_route_proxy_can_block_writer_when_route_or_context_is_not_ready() -> None:
    packet = build_route_proxy_flow_control_packet(
        route_ref="route:deliberation/cycle-1/round-2/opinion-material",
        owner_ref="specialist:material",
        context_ref="cycle-state:cycle-1",
        context_generation=4,
        priority=100,
        dev_shm_path="/dev/shm/autodoc/routes/deliberation/cycle-1/round-2/opinion-material.frame",
        write_allowed=False,
        pressure_level="high",
    )

    assert packet.lease.state == "blocked"
    assert packet.writer_permit.write_allowed is False
    assert packet.writer_permit.denial_reason == "route_proxy_blocked_writer"
    assert packet.pressure_signal is not None
    assert packet.pressure_signal.recommended_action == "refresh_context_or_wait"
    assert {fact.kind for fact in packet.observation_facts} >= {"route.lease_blocked", "route.writer_permit_denied"}


def test_context_generation_fence_marks_old_routes_stale() -> None:
    fence = build_context_generation_fence(
        route_root_ref="route:deliberation/cycle-1",
        old_generation=7,
        new_generation=8,
        stale_route_refs=(
            "route:deliberation/cycle-1/round-1/opinion-thermal",
            "route:deliberation/cycle-1/round-1/opinion-material",
        ),
    )

    assert isinstance(fence, RouteContextGenerationFence)
    assert fence.old_generation == 7
    assert fence.new_generation == 8
    assert fence.reason == "context_generation_changed"
    mapping = fence.to_mapping()
    assert mapping["blocks_old_writers_fast"] is True


def test_lease_mark_stale_requires_increasing_generation() -> None:
    lease = RouteProxyLease(
        lease_ref="route-lease:abc",
        route_ref="route:deliberation/cycle-1/round-1/opinion-thermal",
        owner_ref="specialist:thermal",
        context_ref="cycle-state:cycle-1",
        context_generation=2,
        priority=300,
        state="granted",
    )

    stale = lease.mark_stale(new_context_generation=3)
    assert stale.state == "stale"
    assert stale.context_generation == 3

    with pytest.raises(ValueError, match="new_context_generation must be greater"):
        lease.mark_stale(new_context_generation=2)


def test_writer_permit_denial_requires_reason() -> None:
    lease = RouteProxyLease(
        lease_ref="route-lease:def",
        route_ref="route:deliberation/cycle-1/round-1/opinion-psy",
        owner_ref="specialist:psy",
        context_ref="cycle-state:cycle-1",
        context_generation=2,
        priority=300,
    )

    with pytest.raises(ValueError, match="denial_reason must not be empty"):
        RouteWriterPermit.from_lease(lease, write_allowed=False)


def test_observation_fact_is_bus_ready_and_not_payload_command() -> None:
    fact = RouteProxyObservationFact(
        fact_ref="route-proxy-fact:abc",
        kind="route.priority_changed",
        route_ref="route:deliberation/cycle-1/round-3/demand-safety",
        owner_ref="scheduler-command:round-3",
        context_generation=9,
        metadata=(("reason", "scheduler_priority_changed"),),
    )

    mapping = fact.to_mapping()
    assert mapping["event_bus_role"] == "observation_only"
    assert mapping["payload_command"] is False
    assert mapping["metadata"] == {"reason": "scheduler_priority_changed"}


def test_invalid_dev_shm_path_is_rejected() -> None:
    with pytest.raises(ValueError, match="dev_shm_path must start with"):
        build_route_proxy_flow_control_packet(
            route_ref="route:bad",
            owner_ref="specialist:thermal",
            context_ref="cycle-state:bad",
            context_generation=1,
            priority=1,
            dev_shm_path="/tmp/not-a-route.frame",
        )
