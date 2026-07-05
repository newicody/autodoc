from __future__ import annotations

import pytest

from runtime.route_bridge_boundary import (
    ROUTE_BRIDGE_BOUNDARY_SCHEMA,
    RouteBridgeBoundaryError,
    RouteBridgeBoundarySpec,
    build_route_bridge_plan,
    route_bridge_spec_from_mapping,
)


def test_route_bridge_spec_roundtrip_for_network_boundary() -> None:
    spec = RouteBridgeBoundarySpec(
        bridge_id="bridge-net-a",
        kind="network",
        route_id="route-a",
        zone="zone-a",
        enabled=False,
        metadata={"target": "future-network-adapter"},
    )

    loaded = route_bridge_spec_from_mapping(spec.to_mapping())

    assert loaded == spec
    assert loaded.to_mapping()["schema"] == ROUTE_BRIDGE_BOUNDARY_SCHEMA


def test_route_bridge_plan_has_no_runtime_effect_even_when_enabled() -> None:
    spec = RouteBridgeBoundarySpec(
        bridge_id="bridge-hw-a",
        kind="hardware",
        route_id="route-a",
        zone="zone-a",
        enabled=True,
    )

    plan = build_route_bridge_plan(spec)

    assert plan.status == "declared"
    assert plan.effect == "none"
    assert "real adapter is not implemented in 0112" in plan.reason
    assert plan.to_mapping()["spec"]["kind"] == "hardware"


def test_disabled_route_bridge_plan_is_recorded_without_adapter_selection() -> None:
    spec = RouteBridgeBoundarySpec(
        bridge_id="bridge-net-disabled",
        kind="network",
        route_id="route-b",
        zone="zone-b",
    )

    plan = build_route_bridge_plan(spec)

    assert plan.status == "disabled"
    assert plan.effect == "none"
    assert "no runtime adapter is selected" in plan.reason


@pytest.mark.parametrize("kind", ["", "storage", "eventbus"])
def test_route_bridge_spec_rejects_unknown_kind(kind: str) -> None:
    with pytest.raises(RouteBridgeBoundaryError, match="kind must be network or hardware"):
        RouteBridgeBoundarySpec(
            bridge_id="bridge-a",
            kind=kind,  # type: ignore[arg-type]
            route_id="route-a",
            zone="zone-a",
        )


def test_route_bridge_spec_rejects_bad_schema() -> None:
    raw = {
        "schema": "bad",
        "bridge_id": "bridge-a",
        "kind": "network",
        "route_id": "route-a",
        "zone": "zone-a",
        "enabled": False,
    }

    with pytest.raises(RouteBridgeBoundaryError, match="unsupported route bridge boundary schema"):
        route_bridge_spec_from_mapping(raw)
