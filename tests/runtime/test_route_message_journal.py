from __future__ import annotations

from pathlib import Path

import pytest

from runtime.mmap_fixed_slot_route import MmapFixedSlotRoute, route_file_size
from runtime.route_message_journal import (
    ROUTE_MESSAGE_JOURNAL_RECORD_SCHEMA,
    RouteMessageJournalSummary,
    load_route_message_journal,
    records_from_drained_route_messages,
    write_drained_route_messages_journal,
)
from runtime.route_notification import RouteNotifier
from runtime.route_write_notify_drain import (
    RouteSelectorDrainResult,
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


def _message(message_id: str = "msg-001", value: int = 42) -> RouteMessage:
    return RouteMessage(
        schema=ROUTE_MESSAGE_SCHEMA,
        route_id="route-a",
        message_id=message_id,
        kind="event",
        source="producer-a",
        target="consumer-a",
        occurred_at="2026-07-05T00:00:00Z",
        payload_schema="missipy.test.route_payload.v1",
        payload={"value": value},
    )


def test_journal_records_drained_route_messages_as_jsonl(tmp_path: Path) -> None:
    route = _route(tmp_path)
    try:
        with RouteNotifier.create("route-a", backend="pipe") as notifier:
            write_route_message_and_notify(route, notifier, _message("msg-001", 42))
            write_route_message_and_notify(route, notifier, _message("msg-002", 43))

            drained = drain_notified_route_messages(route, notifier, timeout=0.1)
            journal_path = tmp_path / "recorder" / "route_messages.jsonl"
            summary = write_drained_route_messages_journal(journal_path, drained)

        assert isinstance(summary, RouteMessageJournalSummary)
        assert summary.route_handle == "route-a"
        assert summary.record_count == 2
        assert summary.appended is False
        assert summary.sequences == (0, 1)
        assert summary.message_ids == ("msg-001", "msg-002")

        records = load_route_message_journal(journal_path)
        assert [record.schema for record in records] == [
            ROUTE_MESSAGE_JOURNAL_RECORD_SCHEMA,
            ROUTE_MESSAGE_JOURNAL_RECORD_SCHEMA,
        ]
        assert [record.source_surface for record in records] == ["routes/route-a", "routes/route-a"]
        assert [record.sequence for record in records] == [0, 1]
        assert [record.message_id for record in records] == ["msg-001", "msg-002"]
        assert records[0].message["payload"] == {"value": 42}
        assert records[1].payload_hash.startswith("sha256:")
    finally:
        route.close()


def test_empty_drain_writes_empty_journal(tmp_path: Path) -> None:
    drained = RouteSelectorDrainResult(
        route_handle="route-a",
        selector_ready=False,
        notification_count=0,
        drained_count=0,
        drained_sequences=(),
        message_ids=(),
        messages=(),
    )
    journal_path = tmp_path / "empty.jsonl"

    summary = write_drained_route_messages_journal(journal_path, drained)

    assert summary.record_count == 0
    assert journal_path.read_text(encoding="utf-8") == ""
    assert load_route_message_journal(journal_path) == ()


def test_records_reject_inconsistent_drain_result() -> None:
    drained = RouteSelectorDrainResult(
        route_handle="route-a",
        selector_ready=True,
        notification_count=1,
        drained_count=2,
        drained_sequences=(0,),
        message_ids=("msg-001",),
        messages=(_message("msg-001"),),
    )

    with pytest.raises(ValueError, match="drained result is inconsistent"):
        records_from_drained_route_messages(drained)
