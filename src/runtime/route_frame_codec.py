"""Byte-level RouteMessage frame codec.

This module implements phase 0077.

It deliberately does not:
- create shared memory
- use mmap
- create semaphores
- use eventfd
- use futex
- implement a ring buffer
- start RouteProxy
- watch ControlFS
- call Scheduler
- provide zero-copy transport
- implement NetworkBridge or HardwareBridge

It only encodes a validated RouteMessage into a deterministic bytes frame and
decodes that frame back into a validated RouteMessage.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import struct
from typing import Any, Mapping

from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA, RouteMessage, parse_runtime_message


FRAME_MAGIC = b"MSPYRTF1"
FRAME_VERSION = 1
FRAME_HEADER_FORMAT = ">8sHHII32s"
FRAME_HEADER_SIZE = struct.calcsize(FRAME_HEADER_FORMAT)
FRAME_SCHEMA = "missipy.shm.route_frame.v1"


class RouteFrameError(ValueError):
    """Base error for route frame codec failures."""


class RouteFrameDecodeError(RouteFrameError):
    """Raised when a route frame cannot be decoded or validated."""


@dataclass(frozen=True)
class RouteFrameHeader:
    """Fixed route frame header."""

    magic: bytes
    version: int
    flags: int
    header_size: int
    payload_size: int
    payload_sha256: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "magic": self.magic.decode("ascii", errors="replace"),
            "version": self.version,
            "flags": self.flags,
            "header_size": self.header_size,
            "payload_size": self.payload_size,
            "payload_sha256": self.payload_sha256,
        }


@dataclass(frozen=True)
class RouteFrame:
    """Decoded route frame with validated RouteMessage payload."""

    schema: str
    header: RouteFrameHeader
    message: RouteMessage
    payload_bytes: bytes

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "header": self.header.to_mapping(),
            "message": self.message.to_mapping(),
        }


def encode_route_message_frame(message: RouteMessage | Mapping[str, Any], *, flags: int = 0) -> bytes:
    """Encode a validated RouteMessage into a deterministic bytes frame.

    The payload is canonical JSON for now. The frame wrapper is binary and
    already checks magic, version, size and SHA-256 during decode.
    """

    if not isinstance(flags, int) or isinstance(flags, bool) or flags < 0 or flags > 0xFFFF:
        raise ValueError("flags must be an integer in range 0..65535")

    route_message = _route_message(message)
    payload = _canonical_payload(route_message)
    digest = hashlib.sha256(payload).digest()

    header = struct.pack(
        FRAME_HEADER_FORMAT,
        FRAME_MAGIC,
        FRAME_VERSION,
        flags,
        FRAME_HEADER_SIZE,
        len(payload),
        digest,
    )
    return header + payload


def decode_route_message_frame(frame: bytes | bytearray | memoryview) -> RouteFrame:
    """Decode a route frame and validate its RouteMessage payload."""

    data = bytes(frame)
    if len(data) < FRAME_HEADER_SIZE:
        raise RouteFrameDecodeError("frame is shorter than header")

    magic, version, flags, header_size, payload_size, digest = struct.unpack(
        FRAME_HEADER_FORMAT,
        data[:FRAME_HEADER_SIZE],
    )

    if magic != FRAME_MAGIC:
        raise RouteFrameDecodeError("invalid frame magic")
    if version != FRAME_VERSION:
        raise RouteFrameDecodeError(f"unsupported frame version: {version}")
    if header_size != FRAME_HEADER_SIZE:
        raise RouteFrameDecodeError(f"unsupported header size: {header_size}")

    expected_size = header_size + payload_size
    if len(data) != expected_size:
        raise RouteFrameDecodeError(
            f"invalid frame length: got {len(data)}, expected {expected_size}"
        )

    payload = data[header_size:]
    if hashlib.sha256(payload).digest() != digest:
        raise RouteFrameDecodeError("payload SHA-256 mismatch")

    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RouteFrameDecodeError(f"invalid payload JSON: {exc}") from exc

    parsed = parse_runtime_message(raw)
    if not isinstance(parsed, RouteMessage):
        raise RouteFrameDecodeError(f"expected RouteMessage payload, got {type(parsed).__name__}")

    if parsed.schema != ROUTE_MESSAGE_SCHEMA:
        raise RouteFrameDecodeError(f"unexpected route message schema: {parsed.schema}")

    return RouteFrame(
        schema=FRAME_SCHEMA,
        header=RouteFrameHeader(
            magic=magic,
            version=version,
            flags=flags,
            header_size=header_size,
            payload_size=payload_size,
            payload_sha256="sha256:" + digest.hex(),
        ),
        message=parsed,
        payload_bytes=payload,
    )


def inspect_route_message_frame(frame: bytes | bytearray | memoryview) -> dict[str, Any]:
    """Decode a frame and return a JSON-serializable inspection mapping."""

    return decode_route_message_frame(frame).to_mapping()


def _route_message(message: RouteMessage | Mapping[str, Any]) -> RouteMessage:
    if isinstance(message, RouteMessage):
        return message
    parsed = parse_runtime_message(message)
    if not isinstance(parsed, RouteMessage):
        raise TypeError(f"expected RouteMessage, got {type(parsed).__name__}")
    return parsed


def _canonical_payload(message: RouteMessage) -> bytes:
    return json.dumps(
        message.to_mapping(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
