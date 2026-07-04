import json

from context.baby_fork_runtime_projection import (
    BABY_FORK_CONTEXT_GATE_ROUTE,
    BABY_FORK_RETRIEVAL_ROUTE,
    BABY_FORK_VARIANT_ROUTE,
    build_baby_fork_runtime_projection,
    build_baby_fork_runtime_projection_json,
)
from runtime.shm_runtime_schema import (
    CONTEXT_BUS_MESSAGE_SCHEMA,
    DATA_HANDLE_SCHEMA,
    EVENT_BUS_MESSAGE_SCHEMA,
    ROUTE_MESSAGE_SCHEMA,
    parse_runtime_message,
)


def _report() -> dict:
    return {
        "ok": True,
        "snapshot_count": 6,
        "retrieval": {
            "retrieved_ids": ["baby-silicone-fork", "rounded-stainless-soft-handle"],
            "rejected_ids": ["nasa-antenna"],
        },
        "variants": [
            {"variant_id": "variant-1", "label": "soft silicone baby fork", "score": 0.86},
            {"variant_id": "variant-2", "label": "rounded stainless with soft handle", "score": 0.74},
        ],
        "final_context": {
            "context_id": "baby_fork_smoke",
            "context_version": 2,
            "selected_variant_id": "variant-1",
        },
    }


def test_projection_contains_locked_baby_fork_routes() -> None:
    projection = build_baby_fork_runtime_projection(_report())

    route_ids = {message.route_id for message in projection.routes}

    assert route_ids == {
        BABY_FORK_RETRIEVAL_ROUTE,
        BABY_FORK_VARIANT_ROUTE,
        BABY_FORK_CONTEXT_GATE_ROUTE,
    }


def test_projection_contains_event_context_and_data_handle_schemas() -> None:
    projection = build_baby_fork_runtime_projection(_report())

    assert projection.data_handles[0].schema == DATA_HANDLE_SCHEMA
    assert {event.schema for event in projection.events} == {EVENT_BUS_MESSAGE_SCHEMA}
    assert projection.contexts[0].schema == CONTEXT_BUS_MESSAGE_SCHEMA
    assert {route.schema for route in projection.routes} == {ROUTE_MESSAGE_SCHEMA}


def test_projection_preserves_retrieval_and_selection_summary() -> None:
    projection = build_baby_fork_runtime_projection(_report())

    retrieval = projection.events[0]
    context = projection.contexts[0]

    assert retrieval.topic == "retrieval.completed"
    assert retrieval.payload["retrieved_ids"] == ["baby-silicone-fork", "rounded-stainless-soft-handle"]
    assert retrieval.payload["rejected_ids"] == ["nasa-antenna"]
    assert context.topic == "context.versioned"
    assert context.payload["selected_variant_id"] == "variant-1"


def test_projection_json_round_trips_through_runtime_parser() -> None:
    payload = json.loads(build_baby_fork_runtime_projection_json(_report()))

    for section in ("data_handles", "events", "contexts", "routes"):
        assert payload[section], f"missing projection section: {section}"
        for item in payload[section]:
            parsed = parse_runtime_message(item)
            assert parsed.schema == item["schema"]
