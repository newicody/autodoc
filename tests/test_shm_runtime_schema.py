import json

import pytest

from runtime.shm_runtime_schema import (
    CONTEXT_BUS_MESSAGE_SCHEMA,
    DATA_HANDLE_SCHEMA,
    EVENT_BUS_MESSAGE_SCHEMA,
    ROUTE_MESSAGE_SCHEMA,
    ContextBusMessage,
    DataHandle,
    EventBusMessage,
    RouteMessage,
    RuntimeSchemaValidationError,
    classify_runtime_message,
    parse_runtime_json,
)


def _handle() -> dict:
    return {
        "schema": DATA_HANDLE_SCHEMA,
        "handle_id": "evidence-set-001",
        "storage": "zfs",
        "uri": "zfs://fast_pool/autodoc/artifacts/evidence-set-001.json",
        "content_schema": "missipy.baby_fork.evidence_set.v1",
        "size_bytes": 4096,
        "hash": "sha256:abc123",
        "producer": "retrieval_worker",
        "zone": "workers",
        "created_at": "2026-07-04T20:00:00Z",
        "ttl_seconds": 3600,
    }


def _event() -> dict:
    return {
        "schema": EVENT_BUS_MESSAGE_SCHEMA,
        "event_id": "evt-001",
        "topic": "retrieval.completed",
        "source": "retrieval_worker",
        "occurred_at": "2026-07-04T20:00:00Z",
        "zone": "workers",
        "payload_schema": "missipy.baby_fork.retrieval_completed.v1",
        "payload": {"route_id": "baby_fork.retrieval", "retrieved_count": 2},
        "data_handles": [_handle()],
    }


def _context() -> dict:
    return {
        "schema": CONTEXT_BUS_MESSAGE_SCHEMA,
        "context_id": "baby_fork_smoke",
        "context_version": 2,
        "topic": "context.versioned",
        "source": "context_gate",
        "occurred_at": "2026-07-04T20:00:00Z",
        "zone": "context",
        "payload_schema": "missipy.task_context.patch.v1",
        "payload": {"selected_variant_id": "variant-1"},
    }


def _route() -> dict:
    return {
        "schema": ROUTE_MESSAGE_SCHEMA,
        "route_id": "baby_fork.retrieval",
        "message_id": "msg-001",
        "kind": "request",
        "source": "scheduler",
        "target": "retrieval_worker",
        "occurred_at": "2026-07-04T20:00:00Z",
        "payload_schema": "missipy.baby_fork.retrieval_request.v1",
        "payload": {"context_id": "baby_fork_smoke", "context_version": 1},
    }


def test_data_handle_round_trip() -> None:
    handle = DataHandle.from_mapping(_handle())

    assert handle.handle_id == "evidence-set-001"
    assert handle.storage == "zfs"
    assert handle.to_mapping()["content_schema"] == "missipy.baby_fork.evidence_set.v1"


def test_event_message_with_data_handle() -> None:
    event = EventBusMessage.from_mapping(_event())

    assert event.topic == "retrieval.completed"
    assert event.data_handles[0].handle_id == "evidence-set-001"


def test_context_bus_message() -> None:
    message = ContextBusMessage.from_mapping(_context())

    assert message.context_id == "baby_fork_smoke"
    assert message.context_version == 2


def test_route_message() -> None:
    message = RouteMessage.from_mapping(_route())

    assert message.route_id == "baby_fork.retrieval"
    assert message.kind == "request"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (_event(), "event"),
        (_context(), "context"),
        (_handle(), "data"),
        (_route(), "route"),
    ],
)
def test_classify_runtime_message(payload: dict, expected: str) -> None:
    assert classify_runtime_message(payload) == expected


def test_parse_runtime_json_returns_matching_type() -> None:
    parsed = parse_runtime_json(json.dumps(_route()))

    assert isinstance(parsed, RouteMessage)
    assert parsed.message_id == "msg-001"


def test_reject_large_event_payload_requires_data_handle() -> None:
    raw = _event()
    raw.pop("data_handles")
    raw["payload"] = {"blob": "x" * (70 * 1024)}

    with pytest.raises(RuntimeSchemaValidationError, match="use DataHandle"):
        EventBusMessage.from_mapping(raw)


def test_reject_invalid_storage_value() -> None:
    raw = _handle()
    raw["storage"] = "database"

    with pytest.raises(RuntimeSchemaValidationError, match="storage"):
        DataHandle.from_mapping(raw)


def test_reject_non_utc_timestamp() -> None:
    raw = _route()
    raw["occurred_at"] = "2026-07-04 20:00:00"

    with pytest.raises(RuntimeSchemaValidationError, match="UTC timestamp"):
        RouteMessage.from_mapping(raw)


def test_reject_unknown_schema() -> None:
    raw = {"schema": "missipy.unknown.v1"}

    with pytest.raises(RuntimeSchemaValidationError, match="unknown runtime message schema"):
        classify_runtime_message(raw)
