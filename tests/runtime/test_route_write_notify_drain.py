from __future__ import annotations

from pathlib import Path

import pytest

from runtime.mmap_fixed_slot_route import MmapFixedSlotRoute, route_file_size
from runtime.route_notification import RouteNotifier
from runtime.route_write_notify_drain import (
    RouteSelectorDrainResult,
    RouteWriteNotifyResult,
    drain_notified_route_messages,
    write_route_message_and_notify,
)
from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA, RouteMessage


def _route(tmp_path: Path) -> MmapFixedSlotRoute:
    ring_path = tmp_path / "ring.bin"
    with ring_path.open("wb") as handle:
        handle.truncate(route_file_size(slot_size=768, slot_count=4))
    route = MmapFixedSlotRoute.open(
        ring_path,
        route_handle="route-a",
        status_path=tmp_path / "status.json",
        overflow_policy="reject",
    )
    route.initialize(slot_size=768, slot_count=4)
    return route


def _message(message_id: str = "msg-001") -> RouteMessage:
    return RouteMessage(
        schema=ROUTE_MESSAGE_SCHEMA,
        route_id="route-a",
        message_id=message_id,
        kind="event",
        source="producer-a",
        target="consumer-a",
        occurred_at="2026-07-05T00:00:00Z",
        payload_schema="missipy.test.route_payload.v1",
        payload={"value": 42},
    )


def test_write_notify_then_selector_drain_round_trips_route_message(tmp_path: Path) -> None:
    route = _route(tmp_path)
    try:
        with RouteNotifier.create("route-a", backend="pipe") as notifier:
            write_result = write_route_message_and_notify(route, notifier, _message())

            assert isinstance(write_result, RouteWriteNotifyResult)
            assert write_result.route_handle == "route-a"
            assert write_result.message_id == "msg-001"
            assert write_result.written_sequence == 0
            assert write_result.written_count == 1
            assert write_result.frame_size > 0
            assert write_result.frame_sha256.startswith("sha256:")
            assert route.stats().occupancy == 1

            drain_result = drain_notified_route_messages(
                route,
                notifier,
                timeout=0.1,
            )

            assert isinstance(drain_result, RouteSelectorDrainResult)
            assert drain_result.route_handle == "route-a"
            assert drain_result.selector_ready is True
            assert drain_result.notification_count == 1
            assert drain_result.drained_count == 1
            assert drain_result.drained_sequences == (0,)
            assert drain_result.message_ids == ("msg-001",)
            assert drain_result.messages == (_message(),)
            assert route.stats().occupancy == 0
    finally:
        route.close()


def test_selector_drain_without_notification_is_empty(tmp_path: Path) -> None:
    route = _route(tmp_path)
    try:
        with RouteNotifier.create("route-a", backend="pipe") as notifier:
            result = drain_notified_route_messages(route, notifier, timeout=0.0)

            assert result.selector_ready is False
            assert result.notification_count == 0
            assert result.drained_count == 0
            assert result.drained_sequences == ()
            assert result.message_ids == ()
            assert result.messages == ()
            assert route.stats().occupancy == 0
    finally:
        route.close()


def test_drain_rejects_negative_timeout(tmp_path: Path) -> None:
    route = _route(tmp_path)
    try:
        with RouteNotifier.create("route-a", backend="pipe") as notifier:
            with pytest.raises(ValueError, match="timeout must be non-negative"):
                drain_notified_route_messages(route, notifier, timeout=-0.1)
    finally:
        route.close()
