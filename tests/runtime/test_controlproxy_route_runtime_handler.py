from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from contracts.event import Event, EventType
from runtime.controlproxy_prepare import ROUTE_PREPARE_STATUS_SCHEMA, RoutePrepareDecision
from runtime.controlproxy_route_runtime_handler import (
    ControlProxyRouteRuntimeHandlerError,
    ControlProxyRouteRuntimeHandlerRequest,
    build_controlproxy_route_runtime_request_handler,
    handle_controlproxy_route_runtime_request,
    route_prepare_decision_from_payload,
)
from runtime.controlproxy_scheduler_handler import ControlProxySchedulerRouteRequestHandler
from runtime.route_runtime_manager import RouteRuntimeManager


@dataclass(frozen=True, slots=True)
class PayloadObject:
    route_id: str
    zone: str
    policy_decision_id: str
    authorized: bool
    decision: RoutePrepareDecision
    source: str = "pytest.scheduler"


def _decision(*, route_id: str = "route-a", zone: str = "workers") -> RoutePrepareDecision:
    return RoutePrepareDecision(
        schema=ROUTE_PREPARE_STATUS_SCHEMA,
        request_id=f"prep:{route_id}",
        route_id=route_id,
        route_handle=f"{route_id}@g1",
        task_id="task-a",
        zone=zone,
        status="ready",
        action="create_route_generation",
        reason="pytest controlproxy route runtime handler",
        required_frame_bytes=128,
        current_generation=None,
        next_generation=1,
        current_slot_size=None,
        slot_size=512,
        slot_count=2,
        max_frame_bytes=512,
        max_ring_bytes=8192,
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
        "policy_decision_id": "policy-1",
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
async def test_scheduler_handler_can_delegate_to_route_runtime_manager(tmp_path: Path) -> None:
    manager = RouteRuntimeManager.from_roots(
        controlfs_root=tmp_path / "controlfs",
        runtime_root=tmp_path / "runtime",
    )
    request_handler = build_controlproxy_route_runtime_request_handler(manager)
    handler = ControlProxySchedulerRouteRequestHandler(route_request_handler=request_handler)

    result = await handler.handle(_event(_payload(_decision())))

    assert result.action == "materialize_generation"
    assert result.status == "candidate"
    assert result.route_id == "route-a"
    assert Path(result.payload["record"]["ring_path"]).exists()


def test_runtime_handler_accepts_payload_object_and_decision_object(tmp_path: Path) -> None:
    manager = RouteRuntimeManager.from_roots(
        controlfs_root=tmp_path / "controlfs",
        runtime_root=tmp_path / "runtime",
    )
    decision = _decision(route_id="route-b", zone="workers")
    payload = PayloadObject(
        route_id="route-b",
        zone="workers",
        policy_decision_id="policy-2",
        authorized=True,
        decision=decision,
    )

    result = handle_controlproxy_route_runtime_request(payload, manager=manager)

    assert result.action == "materialize_generation"
    assert result.route_id == "route-b"


def test_route_runtime_handler_request_rejects_missing_decision() -> None:
    with pytest.raises(ControlProxyRouteRuntimeHandlerError, match="requires a decision field"):
        ControlProxyRouteRuntimeHandlerRequest.from_payload(
            {
                "route_id": "route-c",
                "zone": "workers",
                "policy_decision_id": "policy-3",
                "authorized": True,
            }
        )


def test_route_runtime_handler_rejects_mismatched_envelope_and_decision() -> None:
    payload = _payload(_decision(route_id="route-d"))
    payload["route_id"] = "other-route"

    with pytest.raises(ControlProxyRouteRuntimeHandlerError, match="route_id must match"):
        ControlProxyRouteRuntimeHandlerRequest.from_payload(payload)


def test_route_prepare_decision_from_payload_accepts_mapping_projection() -> None:
    decision = _decision(route_id="route-e")

    parsed = route_prepare_decision_from_payload(decision.to_mapping())

    assert parsed == decision
