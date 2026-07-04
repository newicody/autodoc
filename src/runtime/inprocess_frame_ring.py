"""In-process frame ring integration.

This module implements phase 0078.

It deliberately does not:
- create shared memory
- use mmap
- create semaphores
- use eventfd
- use futex
- start RouteProxy
- watch ControlFS
- call Scheduler
- provide zero-copy transport
- provide thread/process safety
- implement NetworkBridge or HardwareBridge

It integrates the phase 0077 RouteMessage frame codec with an in-process
bounded ring model. The ring stores bytes frames and decodes them back to
validated RouteMessage payloads when read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from runtime.route_frame_codec import (
    RouteFrame,
    decode_route_message_frame,
    encode_route_message_frame,
)
from runtime.shm_runtime_schema import RouteMessage


OverflowPolicy = Literal["reject", "drop_oldest"]


class FrameRingError(RuntimeError):
    """Base error for in-process frame ring failures."""


class FrameRingOverflowError(FrameRingError):
    """Raised when a frame ring is full and overflow policy is reject."""


class FrameTooLargeError(FrameRingError):
    """Raised when a frame exceeds max_frame_bytes."""


@dataclass(frozen=True)
class FrameRingSlot:
    """One encoded bytes frame slot."""

    sequence: int
    frame: bytes

    @property
    def frame_size(self) -> int:
        return len(self.frame)

    def decode(self) -> RouteFrame:
        return decode_route_message_frame(self.frame)

    def to_mapping(self) -> dict[str, Any]:
        decoded = self.decode()
        return {
            "sequence": self.sequence,
            "frame_size": self.frame_size,
            "route_id": decoded.message.route_id,
            "message_id": decoded.message.message_id,
            "payload_size": decoded.header.payload_size,
            "payload_sha256": decoded.header.payload_sha256,
        }


@dataclass(frozen=True)
class FrameRingStats:
    """Current frame ring stats."""

    capacity: int
    occupancy: int
    total_frame_bytes: int
    max_frame_bytes: int | None
    write_sequence: int
    read_sequence: int
    dropped_count: int
    overflow_policy: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "occupancy": self.occupancy,
            "total_frame_bytes": self.total_frame_bytes,
            "max_frame_bytes": self.max_frame_bytes,
            "write_sequence": self.write_sequence,
            "read_sequence": self.read_sequence,
            "dropped_count": self.dropped_count,
            "overflow_policy": self.overflow_policy,
        }


class InProcessFrameRingBuffer:
    """Bounded in-process ring that stores encoded RouteMessage frames."""

    def __init__(
        self,
        capacity: int,
        *,
        overflow_policy: OverflowPolicy = "reject",
        max_frame_bytes: int | None = None,
    ):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        if overflow_policy not in ("reject", "drop_oldest"):
            raise ValueError("overflow_policy must be 'reject' or 'drop_oldest'")
        if max_frame_bytes is not None and (
            not isinstance(max_frame_bytes, int)
            or isinstance(max_frame_bytes, bool)
            or max_frame_bytes < 1
        ):
            raise ValueError("max_frame_bytes must be a positive integer or None")

        self.capacity = capacity
        self.overflow_policy: OverflowPolicy = overflow_policy
        self.max_frame_bytes = max_frame_bytes
        self._slots: list[FrameRingSlot] = []
        self._next_sequence = 0
        self._read_sequence = 0
        self._dropped_count = 0

    def write_message(self, message: RouteMessage | Mapping[str, Any]) -> FrameRingSlot:
        """Encode and write a RouteMessage as a bytes frame."""

        return self.write_frame(encode_route_message_frame(message))

    def write_frame(self, frame: bytes | bytearray | memoryview) -> FrameRingSlot:
        """Validate and write an existing encoded frame."""

        raw = bytes(frame)
        if self.max_frame_bytes is not None and len(raw) > self.max_frame_bytes:
            raise FrameTooLargeError(
                f"frame has {len(raw)} bytes, max_frame_bytes is {self.max_frame_bytes}"
            )

        # Validate before modifying the ring.
        decode_route_message_frame(raw)

        if len(self._slots) >= self.capacity:
            if self.overflow_policy == "reject":
                raise FrameRingOverflowError("frame ring is full")
            dropped = self._slots.pop(0)
            self._dropped_count += 1
            self._read_sequence = max(self._read_sequence, dropped.sequence + 1)

        slot = FrameRingSlot(sequence=self._next_sequence, frame=raw)
        self._slots.append(slot)
        self._next_sequence += 1
        return slot

    def peek(self, max_items: int | None = None) -> tuple[FrameRingSlot, ...]:
        """Read frame slots without consuming them."""

        if max_items is None:
            return tuple(self._slots)
        if max_items < 0:
            raise ValueError("max_items must be non-negative")
        return tuple(self._slots[:max_items])

    def drain(self, max_items: int | None = None) -> tuple[FrameRingSlot, ...]:
        """Read and consume frame slots in FIFO order."""

        if max_items is None:
            count = len(self._slots)
        else:
            if max_items < 0:
                raise ValueError("max_items must be non-negative")
            count = min(max_items, len(self._slots))

        drained = tuple(self._slots[:count])
        del self._slots[:count]

        if drained:
            self._read_sequence = drained[-1].sequence + 1

        return drained

    def stats(self) -> FrameRingStats:
        """Return current frame ring stats."""

        return FrameRingStats(
            capacity=self.capacity,
            occupancy=len(self._slots),
            total_frame_bytes=sum(slot.frame_size for slot in self._slots),
            max_frame_bytes=self.max_frame_bytes,
            write_sequence=self._next_sequence,
            read_sequence=self._read_sequence,
            dropped_count=self._dropped_count,
            overflow_policy=self.overflow_policy,
        )


class InProcessFrameRouteRuntime:
    """Route registry using InProcessFrameRingBuffer per route."""

    def __init__(
        self,
        *,
        route_capacity: int = 16,
        overflow_policy: OverflowPolicy = "reject",
        max_frame_bytes: int | None = None,
    ):
        if not isinstance(route_capacity, int) or isinstance(route_capacity, bool) or route_capacity < 1:
            raise ValueError("route_capacity must be a positive integer")
        self.route_capacity = route_capacity
        self.overflow_policy: OverflowPolicy = overflow_policy
        self.max_frame_bytes = max_frame_bytes
        self._routes: dict[str, InProcessFrameRingBuffer] = {}

    def route_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._routes))

    def ensure_route(self, route_id: str) -> InProcessFrameRingBuffer:
        if "/" in route_id or "\\" in route_id or ".." in route_id or not route_id:
            raise ValueError("route_id must be a logical route id, not a path")
        if route_id not in self._routes:
            self._routes[route_id] = InProcessFrameRingBuffer(
                self.route_capacity,
                overflow_policy=self.overflow_policy,
                max_frame_bytes=self.max_frame_bytes,
            )
        return self._routes[route_id]

    def send_message(self, message: RouteMessage | Mapping[str, Any]) -> FrameRingSlot:
        """Encode and write a RouteMessage into the matching route frame ring."""

        frame = encode_route_message_frame(message)
        decoded = decode_route_message_frame(frame)
        return self.ensure_route(decoded.message.route_id).write_frame(frame)

    def send_frame(self, frame: bytes | bytearray | memoryview) -> FrameRingSlot:
        """Write an already encoded RouteMessage frame into the matching route frame ring."""

        decoded = decode_route_message_frame(frame)
        return self.ensure_route(decoded.message.route_id).write_frame(frame)

    def drain_route(self, route_id: str, max_items: int | None = None) -> tuple[FrameRingSlot, ...]:
        return self.ensure_route(route_id).drain(max_items=max_items)

    def stats(self) -> dict[str, dict[str, Any]]:
        return {
            route_id: self._routes[route_id].stats().to_mapping()
            for route_id in self.route_ids()
        }
