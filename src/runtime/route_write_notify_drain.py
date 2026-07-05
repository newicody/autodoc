"""Route write/notify/drain end-to-end primitive.

This module implements phase 0089.

It provides an importable, testable path for:

producer write mmap + notifier.notify + consumer selector/drain

The path intentionally composes existing primitives instead of creating a new
runtime authority:

- ``MmapFixedSlotRoute.write_message()`` writes a RouteMessage frame.
- ``RouteNotifier.notify()`` signals availability.
- ``selectors.DefaultSelector`` observes notifier readability.
- ``MmapFixedSlotRoute.drain()`` consumes committed route frames.

It deliberately does not:

- create a daemon
- start a service
- use OpenRC
- run forever
- watch ControlFS
- sleep or poll
- add a CLI
- call Scheduler
- decide security policy
- grant leases
- implement lease handoff
- resize live mmap routes
- implement route generation g2/g3
- implement Recorder/journal ingestion
- perform drain/closed cleanup
- implement inter-process locks
- create POSIX shared memory with shm_open
- require /dev/shm
- create semaphores
- create futex
- use Qdrant
- use an LLM
- use OpenVINO
- implement NetworkBridge or HardwareBridge
- implement VisPy or browser adapters

It is a small importable bridge for the 0089 E2E primitive, not a service and
not an operator boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
import selectors
from typing import Any, Mapping

from runtime.mmap_fixed_slot_route import MmapFixedSlotRoute, MmapSlot
from runtime.route_notification import (
    RouteNotifier,
    drain_ready_count,
    notify_after_write,
)
from runtime.shm_runtime_schema import RouteMessage


@dataclass(frozen=True, slots=True)
class RouteWriteNotifyResult:
    """Result of one producer write followed by one notification."""

    route_handle: str
    message_id: str
    written_sequence: int
    written_count: int
    frame_size: int
    frame_sha256: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "route_handle": self.route_handle,
            "message_id": self.message_id,
            "written_sequence": self.written_sequence,
            "written_count": self.written_count,
            "frame_size": self.frame_size,
            "frame_sha256": self.frame_sha256,
        }


@dataclass(frozen=True, slots=True)
class RouteSelectorDrainResult:
    """Result of selector readiness, notification drain and mmap drain."""

    route_handle: str
    selector_ready: bool
    notification_count: int
    drained_count: int
    drained_sequences: tuple[int, ...]
    message_ids: tuple[str, ...]
    messages: tuple[RouteMessage, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "route_handle": self.route_handle,
            "selector_ready": self.selector_ready,
            "notification_count": self.notification_count,
            "drained_count": self.drained_count,
            "drained_sequences": list(self.drained_sequences),
            "message_ids": list(self.message_ids),
            "messages": [message.to_mapping() for message in self.messages],
        }


def write_route_message_and_notify(
    route: MmapFixedSlotRoute,
    notifier: RouteNotifier,
    message: RouteMessage | Mapping[str, Any],
) -> RouteWriteNotifyResult:
    """Write one RouteMessage to mmap and notify the consumer side.

    The function does not decide whether the route is authorized, leased or in
    scope. Those decisions are upstream Scheduler/policy/zone concerns. This
    function only performs the already-authorized producer-side transport step.
    """

    slot = route.write_message(message)
    route_message = slot.message()
    notify_after_write(notifier, written_count=1)
    return RouteWriteNotifyResult(
        route_handle=route.route_handle,
        message_id=route_message.message_id,
        written_sequence=slot.sequence,
        written_count=1,
        frame_size=slot.frame_size,
        frame_sha256=slot.frame_sha256,
    )


def drain_notified_route_messages(
    route: MmapFixedSlotRoute,
    notifier: RouteNotifier,
    *,
    timeout: float | None = 0.0,
) -> RouteSelectorDrainResult:
    """Select on notifier readability and drain signalled mmap route messages.

    The selector is created for this call and closed before returning. There is
    no resident watcher, no daemon loop and no sleep/poll loop.
    """

    if timeout is not None and timeout < 0:
        raise ValueError("timeout must be non-negative or None")

    selector = selectors.DefaultSelector()
    try:
        selector.register(notifier.fileno(), selectors.EVENT_READ)
        ready = bool(selector.select(timeout))
    finally:
        selector.close()

    if not ready:
        return _drain_result(
            route_handle=route.route_handle,
            selector_ready=False,
            notification_count=0,
            slots=(),
        )

    notification_count = drain_ready_count(notifier)
    slots = route.drain(max_items=notification_count)
    return _drain_result(
        route_handle=route.route_handle,
        selector_ready=True,
        notification_count=notification_count,
        slots=slots,
    )


def _drain_result(
    *,
    route_handle: str,
    selector_ready: bool,
    notification_count: int,
    slots: tuple[MmapSlot, ...],
) -> RouteSelectorDrainResult:
    messages = tuple(slot.message() for slot in slots)
    return RouteSelectorDrainResult(
        route_handle=route_handle,
        selector_ready=selector_ready,
        notification_count=notification_count,
        drained_count=len(slots),
        drained_sequences=tuple(slot.sequence for slot in slots),
        message_ids=tuple(message.message_id for message in messages),
        messages=messages,
    )


__all__ = (
    "RouteSelectorDrainResult",
    "RouteWriteNotifyResult",
    "drain_notified_route_messages",
    "write_route_message_and_notify",
)
