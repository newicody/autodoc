from __future__ import annotations

from contracts.event import Event, EventType
from contracts.inference import InferenceRequest
from policy.engine import PolicyEngine


def test_policy_allows_normal_tick_event() -> None:
    policy = PolicyEngine()
    event = Event(EventType.TICK, source="component", dest="scheduler")

    decision = policy.decide(event)

    assert decision.allowed is True


def test_policy_rejects_empty_source() -> None:
    policy = PolicyEngine()
    event = Event(EventType.TICK, source="", dest="scheduler")

    decision = policy.decide(event)

    assert decision.allowed is False
    assert decision.rule == "event.source.required"


def test_policy_rejects_priority_outside_kernel_budget() -> None:
    policy = PolicyEngine()
    event = Event(EventType.TICK, source="component", priority=-10_000)

    decision = policy.decide(event)

    assert decision.allowed is False
    assert decision.rule == "event.priority.too_low"


def test_policy_rejects_component_shutdown() -> None:
    policy = PolicyEngine()
    event = Event(EventType.SHUTDOWN, source="component", dest="scheduler")

    decision = policy.decide(event)

    assert decision.allowed is False
    assert decision.rule == "shutdown.source.kernel_only"


def test_policy_allows_context_request_to_registered_component() -> None:
    policy = PolicyEngine()
    event = Event(EventType.CONTEXT_REQUEST, source="context.collector", dest="Worker")

    decision = policy.decide(event, registered_components={"Worker"})

    assert decision.allowed is True


def test_policy_rejects_unknown_inference_model() -> None:
    policy = PolicyEngine()
    event = Event(
        EventType.INFERENCE_REQUEST,
        source="component",
        dest="inference",
        payload=InferenceRequest(prompt="hello", model="missing"),
    )

    decision = policy.decide(event)

    assert decision.allowed is False
    assert decision.rule == "inference.model.denied"
