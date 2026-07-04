import pytest

from runtime.route_frame_codec import (
    FRAME_HEADER_SIZE,
    FRAME_MAGIC,
    FRAME_SCHEMA,
    RouteFrameDecodeError,
    decode_route_message_frame,
    encode_route_message_frame,
)
from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA


def _route_message(message_id: str = "msg-001") -> dict:
    return {
        "schema": ROUTE_MESSAGE_SCHEMA,
        "route_id": "baby_fork.variant_stub",
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


def test_route_frame_roundtrip_validates_route_message() -> None:
    encoded = encode_route_message_frame(_route_message())
    decoded = decode_route_message_frame(encoded)

    assert encoded.startswith(FRAME_MAGIC)
    assert decoded.schema == FRAME_SCHEMA
    assert decoded.header.header_size == FRAME_HEADER_SIZE
    assert decoded.header.payload_size == len(decoded.payload_bytes)
    assert decoded.header.payload_sha256.startswith("sha256:")
    assert decoded.message.route_id == "baby_fork.variant_stub"
    assert decoded.message.message_id == "msg-001"
    assert decoded.message.payload["variant_count"] == 2


def test_route_frame_is_deterministic_for_same_message() -> None:
    first = encode_route_message_frame(_route_message())
    second = encode_route_message_frame(_route_message())

    assert first == second


def test_route_frame_detects_payload_corruption() -> None:
    encoded = bytearray(encode_route_message_frame(_route_message()))
    encoded[-1] ^= 0x01

    with pytest.raises(RouteFrameDecodeError, match="SHA-256"):
        decode_route_message_frame(encoded)


def test_route_frame_detects_bad_magic() -> None:
    encoded = bytearray(encode_route_message_frame(_route_message()))
    encoded[0] = 0

    with pytest.raises(RouteFrameDecodeError, match="magic"):
        decode_route_message_frame(encoded)


def test_route_frame_rejects_non_route_payload_on_encode() -> None:
    with pytest.raises(TypeError):
        encode_route_message_frame({
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


def test_route_frame_rejects_trailing_bytes() -> None:
    encoded = encode_route_message_frame(_route_message()) + b"x"

    with pytest.raises(RouteFrameDecodeError, match="frame length"):
        decode_route_message_frame(encoded)
