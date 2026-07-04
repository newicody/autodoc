from __future__ import annotations

from dataclasses import dataclass

import pytest

from contracts.event import Event, EventType
from runtime import controlproxy_scheduler_handler as handler_module
from runtime.controlproxy_scheduler_handler import ControlProxySchedulerRouteRequestHandler


@dataclass(frozen=True, slots=True)
class DummyRouteRequest:
    route_id: str
    authorized: bool
    policy_decision_id: str


@dataclass(frozen=True, slots=True)
class DummyRouteReply:
    route_id: str
    prepared: bool


def _event(payload: object | None) -> Event:
    return Event(
        EventType.CONTEXT_REQUEST,
        source="pytest.scheduler",
        dest="controlproxy.route",
        payload=payload,
    )


@pytest.mark.asyncio
async def test_controlproxy_scheduler_handler_calls_injected_adapter() -> None:
    request = DummyRouteRequest(
        route_id="route-a",
        authorized=True,
        policy_decision_id="policy-1",
    )
    calls: list[DummyRouteRequest] = []

    def adapter(payload: object) -> DummyRouteReply:
        assert isinstance(payload, DummyRouteRequest)
        calls.append(payload)
        return DummyRouteReply(route_id=payload.route_id, prepared=True)

    handler = ControlProxySchedulerRouteRequestHandler(route_request_handler=adapter)

    result = await handler.handle(_event(request))

    assert result == DummyRouteReply(route_id="route-a", prepared=True)
    assert calls == [request]


@pytest.mark.asyncio
async def test_controlproxy_scheduler_handler_awaits_async_adapter() -> None:
    request = DummyRouteRequest(
        route_id="route-b",
        authorized=True,
        policy_decision_id="policy-2",
    )

    async def adapter(payload: object) -> DummyRouteReply:
        assert isinstance(payload, DummyRouteRequest)
        return DummyRouteReply(route_id=payload.route_id, prepared=True)

    handler = ControlProxySchedulerRouteRequestHandler(route_request_handler=adapter)

    result = await handler.handle(_event(request))

    assert result == DummyRouteReply(route_id="route-b", prepared=True)


@pytest.mark.asyncio
async def test_controlproxy_scheduler_handler_rejects_missing_payload() -> None:
    handler = ControlProxySchedulerRouteRequestHandler(route_request_handler=lambda payload: payload)

    with pytest.raises(ValueError, match="payload is required"):
        await handler.handle(_event(None))


def test_handle_scheduler_route_request_delegates_to_resolved_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    request = DummyRouteRequest(
        route_id="route-c",
        authorized=True,
        policy_decision_id="policy-3",
    )

    def adapter(payload: object) -> DummyRouteReply:
        assert payload is request
        return DummyRouteReply(route_id="route-c", prepared=True)

    monkeypatch.setattr(handler_module, "resolve_scheduler_route_request_handler", lambda: adapter)

    assert handler_module.handle_scheduler_route_request(request) == DummyRouteReply(
        route_id="route-c",
        prepared=True,
    )
