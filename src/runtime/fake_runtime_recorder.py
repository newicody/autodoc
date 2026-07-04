"""Recorder ingestion for the fake local runtime surface.

This module implements the P6-prep recorder ingestion step.

It deliberately does not:
- create shared memory
- create semaphores
- implement a ring buffer
- start a Recorder daemon
- call Scheduler
- call RouteProxy
- mutate ControlFS
- require ZFS
- implement NetworkBridge or HardwareBridge

It only reads the fake JSONL runtime surface, validates runtime messages and
writes a deterministic JSONL journal that can later be replaced by the real
Recorder/ZFS path.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from typing import Any, Iterable, Mapping

from runtime.fake_route_transport import FakeLocalRouteTransport, load_fake_bus_messages
from runtime.shm_runtime_schema import (
    ContextBusMessage,
    DataHandle,
    EventBusMessage,
    RouteMessage,
)


RUNTIME_JOURNAL_RECORD_SCHEMA = "missipy.recorder.runtime_journal_record.v1"


@dataclass(frozen=True)
class RuntimeJournalRecord:
    """One validated fake runtime message persisted as a recorder journal fact."""

    schema: str
    record_id: str
    source_surface: str
    message_schema: str
    message_kind: str
    payload_hash: str
    message: dict[str, Any]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "record_id": self.record_id,
            "source_surface": self.source_surface,
            "message_schema": self.message_schema,
            "message_kind": self.message_kind,
            "payload_hash": self.payload_hash,
            "message": self.message,
        }


@dataclass(frozen=True)
class FakeRuntimeRecorderSummary:
    """Summary of fake runtime ingestion."""

    runtime_root: str
    journal_path: str
    record_count: int
    data_handle_count: int
    event_count: int
    context_count: int
    route_message_count: int
    route_ids: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "runtime_root": self.runtime_root,
            "journal_path": self.journal_path,
            "record_count": self.record_count,
            "data_handle_count": self.data_handle_count,
            "event_count": self.event_count,
            "context_count": self.context_count,
            "route_message_count": self.route_message_count,
            "route_ids": list(self.route_ids),
        }


def ingest_fake_runtime_to_journal(
    runtime_root: Path | str,
    journal_path: Path | str,
    *,
    append: bool = False,
) -> FakeRuntimeRecorderSummary:
    """Ingest a fake runtime surface into a deterministic JSONL journal.

    The input layout is produced by `write_projection_to_fake_runtime`:

    <runtime_root>/
      data.index.jsonl
      event.bus.jsonl
      context.bus.jsonl
      routes/<route_id>/messages.jsonl

    The output journal is a JSONL sequence of RuntimeJournalRecord objects.
    """

    root = Path(runtime_root)
    journal = Path(journal_path)

    data_handles = tuple(
        item for item in load_fake_bus_messages(root / "data.index.jsonl")
        if isinstance(item, DataHandle)
    )
    events = tuple(
        item for item in load_fake_bus_messages(root / "event.bus.jsonl")
        if isinstance(item, EventBusMessage)
    )
    contexts = tuple(
        item for item in load_fake_bus_messages(root / "context.bus.jsonl")
        if isinstance(item, ContextBusMessage)
    )

    transport = FakeLocalRouteTransport(root)
    route_ids = transport.route_ids()
    route_messages: list[RouteMessage] = []
    for route_id in route_ids:
        route_messages.extend(transport.receive(route_id))

    records: list[RuntimeJournalRecord] = []
    records.extend(_records_from_messages("data.index", data_handles))
    records.extend(_records_from_messages("event.bus", events))
    records.extend(_records_from_messages("context.bus", contexts))
    for route_id in route_ids:
        route_records = _records_from_messages(
            f"routes/{route_id}",
            tuple(message for message in route_messages if message.route_id == route_id),
        )
        records.extend(route_records)

    journal.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with journal.open(mode, encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_mapping(), sort_keys=True, separators=(",", ":")))
            handle.write("\n")

    return FakeRuntimeRecorderSummary(
        runtime_root=str(root),
        journal_path=str(journal),
        record_count=len(records),
        data_handle_count=len(data_handles),
        event_count=len(events),
        context_count=len(contexts),
        route_message_count=len(route_messages),
        route_ids=route_ids,
    )


def load_runtime_journal(path: Path | str) -> tuple[RuntimeJournalRecord, ...]:
    """Load journal records written by ingest_fake_runtime_to_journal."""

    p = Path(path)
    if not p.exists():
        return ()

    records: list[RuntimeJournalRecord] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        records.append(
            RuntimeJournalRecord(
                schema=str(raw["schema"]),
                record_id=str(raw["record_id"]),
                source_surface=str(raw["source_surface"]),
                message_schema=str(raw["message_schema"]),
                message_kind=str(raw["message_kind"]),
                payload_hash=str(raw["payload_hash"]),
                message=dict(raw["message"]),
            )
        )
    return tuple(records)


def _records_from_messages(
    source_surface: str,
    messages: Iterable[DataHandle | EventBusMessage | ContextBusMessage | RouteMessage],
) -> tuple[RuntimeJournalRecord, ...]:
    records: list[RuntimeJournalRecord] = []
    for index, message in enumerate(messages):
        mapping = message.to_mapping()
        records.append(
            RuntimeJournalRecord(
                schema=RUNTIME_JOURNAL_RECORD_SCHEMA,
                record_id=_record_id(source_surface, mapping, index),
                source_surface=source_surface,
                message_schema=str(mapping["schema"]),
                message_kind=_message_kind(message),
                payload_hash=_stable_hash(mapping),
                message=mapping,
            )
        )
    return tuple(records)


def _message_kind(message: DataHandle | EventBusMessage | ContextBusMessage | RouteMessage) -> str:
    if isinstance(message, DataHandle):
        return "data_handle"
    if isinstance(message, EventBusMessage):
        return "event"
    if isinstance(message, ContextBusMessage):
        return "context"
    if isinstance(message, RouteMessage):
        return "route"
    raise TypeError(f"unsupported message type: {type(message).__name__}")


def _record_id(source_surface: str, mapping: Mapping[str, Any], index: int) -> str:
    for key in ("event_id", "message_id", "context_id", "handle_id"):
        value = mapping.get(key)
        if value:
            return f"{source_surface}:{value}"
    return f"{source_surface}:{index}"


def _stable_hash(mapping: Mapping[str, Any]) -> str:
    data = json.dumps(dict(mapping), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()
