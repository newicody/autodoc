from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

import pytest

from runtime.route_dispatch_filter_envelope import (
    RouteDispatchFilterEnvelope,
    evaluate_route_dispatch_filter,
    require_route_dispatch_filter_envelope,
)


@dataclass(frozen=True, slots=True)
class RequestObject:
    route_id: str
    zone: str
    policy_decision_id: str
    authorized: bool
    source: str = "pytest.scheduler"
    metadata: MappingProxyType[str, object] = MappingProxyType({})


def test_evaluate_route_dispatch_filter_accepts_mapping_payload() -> None:
    decision = evaluate_route_dispatch_filter(
        {
            "route_id": "route-a",
            "zone": "zone-control",
            "policy_decision_id": "policy-1",
            "authorized": True,
            "source": "scheduler",
            "metadata": {"priority": "hot"},
        }
    )

    assert decision.accepted is True
    assert decision.reason == "accepted for policy/zone dispatch filtering"
    assert decision.envelope is not None
    assert decision.envelope.route_id == "route-a"
    assert decision.envelope.zone == "zone-control"
    assert decision.envelope.policy_decision_id == "policy-1"
    assert decision.envelope.to_mapping()["purpose"] == "policy/zone dispatch filtering, not a security objective"


def test_evaluate_route_dispatch_filter_accepts_object_payload() -> None:
    request = RequestObject(
        route_id="route-b",
        zone="zone-producer",
        policy_decision_id="policy-2",
        authorized=True,
        metadata=MappingProxyType({"producer": "p1"}),
    )

    envelope = require_route_dispatch_filter_envelope(request)

    assert envelope.route_id == "route-b"
    assert envelope.zone == "zone-producer"
    assert envelope.source == "pytest.scheduler"
    assert envelope.metadata == {"producer": "p1"}


def test_evaluate_route_dispatch_filter_rejects_missing_zone() -> None:
    decision = evaluate_route_dispatch_filter(
        {
            "route_id": "route-c",
            "policy_decision_id": "policy-3",
            "authorized": True,
        }
    )

    assert decision.accepted is False
    assert decision.envelope is None
    assert decision.reason == "missing dispatch filter envelope fields"
    assert decision.missing_fields == ("zone",)


def test_evaluate_route_dispatch_filter_rejects_unauthorized_without_deciding_policy() -> None:
    decision = evaluate_route_dispatch_filter(
        {
            "route_id": "route-d",
            "zone": "zone-control",
            "policy_decision_id": "policy-4",
            "authorized": False,
        }
    )

    assert decision.accepted is False
    assert decision.reason == "authorized flag is not true"
    assert decision.to_mapping()["envelope"] is None


def test_require_route_dispatch_filter_envelope_raises_stable_error() -> None:
    with pytest.raises(ValueError, match="route dispatch filter rejected payload"):
        require_route_dispatch_filter_envelope({"route_id": "route-e"})


def test_route_dispatch_filter_envelope_copies_metadata() -> None:
    metadata = {"mutable": []}
    envelope = RouteDispatchFilterEnvelope(
        route_id="route-f",
        zone="zone-control",
        policy_decision_id="policy-5",
        authorized=True,
        metadata=metadata,
    )

    metadata["new"] = "outside"

    assert "new" not in envelope.metadata
    with pytest.raises(TypeError):
        envelope.metadata["blocked"] = True  # type: ignore[index]
