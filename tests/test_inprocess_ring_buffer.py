import pytest

from runtime.inprocess_ring_buffer import (
    InProcessRingBuffer,
    InProcessRouteRuntime,
    RingBufferOverflowError,
)
from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA


def _route_message(message_id: str = "msg-001", route_id: str = "baby_fork.retrieval") -> dict:
    return {
        "schema": ROUTE_MESSAGE_SCHEMA,
        "route_id": route_id,
        "message_id": message_id,
        "kind": "reply",
        "source": "retrieval_worker",
        "target": "scheduler",
        "occurred_at": "2026-07-04T20:00:00Z",
        "payload_schema": "missipy.baby_fork.route_reply.v1",
        "payload": {"context_id": "ctx-baby-fork-001"},
    }


def test_ring_buffer_preserves_fifo_order_and_sequences() -> None:
    ring = InProcessRingBuffer(capacity=3)

    ring.write(_route_message("msg-001"))
    ring.write(_route_message("msg-002"))
    ring.write(_route_message("msg-003"))

    drained = ring.drain()

    assert [slot.sequence for slot in drained] == [0, 1, 2]
    assert [slot.message.message_id for slot in drained] == ["msg-001", "msg-002", "msg-003"]
    assert ring.stats().occupancy == 0
    assert ring.stats().read_sequence == 3
    assert ring.stats().write_sequence == 3


def test_ring_buffer_rejects_overflow_by_default() -> None:
    ring = InProcessRingBuffer(capacity=1)

    ring.write(_route_message("msg-001"))

    with pytest.raises(RingBufferOverflowError):
        ring.write(_route_message("msg-002"))

    assert ring.stats().occupancy == 1
    assert ring.stats().dropped_count == 0


def test_ring_buffer_drop_oldest_is_explicit_and_counted() -> None:
    ring = InProcessRingBuffer(capacity=2, overflow_policy="drop_oldest")

    ring.write(_route_message("msg-001"))
    ring.write(_route_message("msg-002"))
    ring.write(_route_message("msg-003"))

    drained = ring.drain()

    assert [slot.message.message_id for slot in drained] == ["msg-002", "msg-003"]
    assert ring.stats().dropped_count == 1
    assert ring.stats().read_sequence == 3


def test_route_runtime_sends_to_route_specific_buffers() -> None:
    runtime = InProcessRouteRuntime(route_capacity=2)

    runtime.send(_route_message("msg-001", "baby_fork.retrieval"))
    runtime.send(_route_message("msg-002", "baby_fork.variant_stub"))

    assert runtime.route_ids() == ("baby_fork.retrieval", "baby_fork.variant_stub")
    assert runtime.stats()["baby_fork.retrieval"]["occupancy"] == 1
    assert runtime.stats()["baby_fork.variant_stub"]["occupancy"] == 1

    retrieved = runtime.drain_route("baby_fork.retrieval")
    assert retrieved[0].message.message_id == "msg-001"


def test_ring_rejects_non_route_message_mapping() -> None:
    ring = InProcessRingBuffer(capacity=1)

    with pytest.raises(TypeError):
        ring.write({
            "schema": "missipy.shm.data_handle.v1",
            "handle_id": "h1",
            "storage": "zfs",
            "uri": "zfs://example",
            "content_schema": "missipy.example.v1",
            "size_bytes": 1,
            "hash": "sha256:abc",
            "producer": "test",
            "zone": "workers",
            "created_at": "2026-07-04T20:00:00Z",
        })
