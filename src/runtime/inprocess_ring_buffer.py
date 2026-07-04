"""In-process ring buffer model for RouteMessage flow.

This module implements phase 0076.

It deliberately does not:
- create shared memory
- use mmap
- create semaphores
- use eventfd
- use futex
- implement a RouteProxy daemon
- watch ControlFS
- call Scheduler
- provide thread/process safety
- implement NetworkBridge or HardwareBridge

It only models bounded ring behavior in-process using validated RouteMessage
objects, so the runtime can test ordering, capacity and explicit overflow
semantics before real /dev/shm transport exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from runtime.shm_runtime_schema import RouteMessage, parse_runtime_message


OverflowPolicy = Literal["reject", "drop_oldest"]


class RingBufferError(RuntimeError):
    """Base error for in-process ring buffer failures."""


class RingBufferOverflowError(RingBufferError):
    """Raised when a ring buffer is full and overflow policy is reject."""


@dataclass(frozen=True)
class RingSlot:
    """One message slot in the in-process ring model."""

    sequence: int
    message: RouteMessage

    def to_mapping(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "message": self.message.to_mapping(),
        }


@dataclass(frozen=True)
class RingBufferStats:
    """Current in-process ring buffer stats."""

    capacity: int
    occupancy: int
    write_sequence: int
    read_sequence: int
    dropped_count: int
    overflow_policy: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "occupancy": self.occupancy,
            "write_sequence": self.write_sequence,
            "read_sequence": self.read_sequence,
            "dropped_count": self.dropped_count,
            "overflow_policy": self.overflow_policy,
        }


class InProcessRingBuffer:
    """Bounded in-process ring for validated RouteMessage objects.

    The model is intentionally small and deterministic:

    - single producer / single consumer assumption
    - no blocking
    - no concurrency guarantees
    - explicit overflow policy
    - no silent overwrite
    """

    def __init__(self, capacity: int, *, overflow_policy: OverflowPolicy = "reject"):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        if overflow_policy not in ("reject", "drop_oldest"):
            raise ValueError("overflow_policy must be 'reject' or 'drop_oldest'")

        self.capacity = capacity
        self.overflow_policy: OverflowPolicy = overflow_policy
        self._slots: list[RingSlot] = []
        self._next_sequence = 0
        self._read_sequence = 0
        self._dropped_count = 0

    def write(self, message: RouteMessage | Mapping[str, Any]) -> RingSlot:
        """Validate and write a RouteMessage into the ring.

        If the ring is full:
        - reject: raise RingBufferOverflowError
        - drop_oldest: explicitly drop the oldest unread slot
        """

        route_message = _route_message(message)

        if len(self._slots) >= self.capacity:
            if self.overflow_policy == "reject":
                raise RingBufferOverflowError("ring buffer is full")
            dropped = self._slots.pop(0)
            self._dropped_count += 1
            self._read_sequence = max(self._read_sequence, dropped.sequence + 1)

        slot = RingSlot(sequence=self._next_sequence, message=route_message)
        self._slots.append(slot)
        self._next_sequence += 1
        return slot

    def peek(self, max_items: int | None = None) -> tuple[RingSlot, ...]:
        """Read slots without consuming them."""

        if max_items is None:
            return tuple(self._slots)
        if max_items < 0:
            raise ValueError("max_items must be non-negative")
        return tuple(self._slots[:max_items])

    def drain(self, max_items: int | None = None) -> tuple[RingSlot, ...]:
        """Read and consume slots in FIFO order."""

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

    def clear(self) -> None:
        """Remove all buffered messages."""

        if self._slots:
            self._read_sequence = self._slots[-1].sequence + 1
        self._slots.clear()

    def stats(self) -> RingBufferStats:
        """Return current ring stats."""

        return RingBufferStats(
            capacity=self.capacity,
            occupancy=len(self._slots),
            write_sequence=self._next_sequence,
            read_sequence=self._read_sequence,
            dropped_count=self._dropped_count,
            overflow_policy=self.overflow_policy,
        )


class InProcessRouteRuntime:
    """Small route_id -> InProcessRingBuffer registry.

    This is still an in-process model, not a RouteProxy materialization layer.
    """

    def __init__(self, *, route_capacity: int = 16, overflow_policy: OverflowPolicy = "reject"):
        if not isinstance(route_capacity, int) or isinstance(route_capacity, bool) or route_capacity < 1:
            raise ValueError("route_capacity must be a positive integer")
        self.route_capacity = route_capacity
        self.overflow_policy: OverflowPolicy = overflow_policy
        self._routes: dict[str, InProcessRingBuffer] = {}

    def route_ids(self) -> tuple[str, ...]:
        """Return known route IDs."""

        return tuple(sorted(self._routes))

    def ensure_route(self, route_id: str) -> InProcessRingBuffer:
        """Create or return a route buffer."""

        if "/" in route_id or "\\" in route_id or ".." in route_id or not route_id:
            raise ValueError("route_id must be a logical route id, not a path")
        if route_id not in self._routes:
            self._routes[route_id] = InProcessRingBuffer(
                self.route_capacity,
                overflow_policy=self.overflow_policy,
            )
        return self._routes[route_id]

    def send(self, message: RouteMessage | Mapping[str, Any]) -> RingSlot:
        """Write a RouteMessage to the matching route buffer."""

        route_message = _route_message(message)
        return self.ensure_route(route_message.route_id).write(route_message)

    def drain_route(self, route_id: str, max_items: int | None = None) -> tuple[RingSlot, ...]:
        """Drain one route buffer."""

        return self.ensure_route(route_id).drain(max_items=max_items)

    def stats(self) -> dict[str, dict[str, Any]]:
        """Return stats for all route buffers."""

        return {
            route_id: self._routes[route_id].stats().to_mapping()
            for route_id in self.route_ids()
        }


def _route_message(message: RouteMessage | Mapping[str, Any]) -> RouteMessage:
    if isinstance(message, RouteMessage):
        return message
    parsed = parse_runtime_message(message)
    if not isinstance(parsed, RouteMessage):
        raise TypeError(f"expected RouteMessage, got {type(parsed).__name__}")
    return parsed
