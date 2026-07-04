import pytest

from runtime.inprocess_frame_ring import (
    FrameRingOverflowError,
    FrameTooLargeError,
    InProcessFrameRingBuffer,
    InProcessFrameRouteRuntime,
)
from runtime.route_frame_codec import encode_route_message_frame
from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA


def _route_message(message_id: str = "msg-001", route_id: str = "baby_fork.variant_stub") -> dict:
    return {
        "schema": ROUTE_MESSAGE_SCHEMA,
        "route_id": route_id,
        "message_id": message_id,
        "kind": "event",
        "source": "variant_generator_stub",
        "target": "scheduler",
        "occurred_at": "2026-07-04T20:00:00Z",
        "payload_schema": "missipy.baby_fork.variants_generated.v1",
        "payload": {
            "context_id": "ctx-baby-fork-001",
            "variant_count": 2,
            "variant_ids": ["variant-1", "variant-2"],
        },
    }


def test_frame_ring_stores_encoded_frames_and_decodes_on_drain() -> None:
    ring = InProcessFrameRingBuffer(capacity=2)

    ring.write_message(_route_message("msg-001"))
    ring.write_message(_route_message("msg-002"))

    drained = ring.drain()

    assert [slot.sequence for slot in drained] == [0, 1]
    assert [slot.decode().message.message_id for slot in drained] == ["msg-001", "msg-002"]
    assert all(slot.frame_size > 0 for slot in drained)
    assert ring.stats().occupancy == 0
    assert ring.stats().write_sequence == 2
    assert ring.stats().read_sequence == 2


def test_frame_ring_rejects_overflow() -> None:
    ring = InProcessFrameRingBuffer(capacity=1)

    ring.write_message(_route_message("msg-001"))

    with pytest.raises(FrameRingOverflowError):
        ring.write_message(_route_message("msg-002"))

    assert ring.stats().dropped_count == 0


def test_frame_ring_drop_oldest_is_explicit() -> None:
    ring = InProcessFrameRingBuffer(capacity=2, overflow_policy="drop_oldest")

    ring.write_message(_route_message("msg-001"))
    ring.write_message(_route_message("msg-002"))
    ring.write_message(_route_message("msg-003"))

    drained = ring.drain()

    assert [slot.decode().message.message_id for slot in drained] == ["msg-002", "msg-003"]
    assert ring.stats().dropped_count == 1


def test_frame_ring_enforces_max_frame_bytes() -> None:
    ring = InProcessFrameRingBuffer(capacity=1, max_frame_bytes=8)

    with pytest.raises(FrameTooLargeError):
        ring.write_message(_route_message("msg-001"))


def test_frame_route_runtime_sends_to_route_specific_frame_rings() -> None:
    runtime = InProcessFrameRouteRuntime(route_capacity=2)

    runtime.send_message(_route_message("msg-001", "baby_fork.retrieval"))
    runtime.send_message(_route_message("msg-002", "baby_fork.variant_stub"))

    assert runtime.route_ids() == ("baby_fork.retrieval", "baby_fork.variant_stub")
    assert runtime.stats()["baby_fork.retrieval"]["occupancy"] == 1
    assert runtime.stats()["baby_fork.variant_stub"]["occupancy"] == 1

    drained = runtime.drain_route("baby_fork.variant_stub")
    assert drained[0].decode().message.message_id == "msg-002"


def test_frame_route_runtime_accepts_preencoded_frame() -> None:
    runtime = InProcessFrameRouteRuntime(route_capacity=1)
    frame = encode_route_message_frame(_route_message("msg-001", "baby_fork.context_gate"))

    slot = runtime.send_frame(frame)

    assert slot.decode().message.route_id == "baby_fork.context_gate"
    assert runtime.stats()["baby_fork.context_gate"]["total_frame_bytes"] == len(frame)
