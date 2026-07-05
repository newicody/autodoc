"""Recorder/journal ingestion for drained RouteMessage objects.

This module implements phase 0090. It ingests RouteMessage objects already
returned by the 0089 RouteSelectorDrainResult and writes deterministic JSONL
journal records.

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
- resize live mmap routes
- own notifier lifecycle
- read mmap routes directly
- implement route generation g2/g3
- perform drain/closed cleanup
- implement inter-process locks
- require /dev/shm
- use Qdrant
- use an LLM
- use OpenVINO

The journal records are facts about RouteMessage objects that were already
drained. They are not commands and they do not authorize transport.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from runtime.route_write_notify_drain import RouteSelectorDrainResult
from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA, RouteMessage

ROUTE_MESSAGE_JOURNAL_RECORD_SCHEMA = "missipy.recorder.route_message_journal_record.v1"


@dataclass(frozen=True, slots=True)
class RouteMessageJournalRecord:
    """One RouteMessage drained from a route and persisted as a journal fact."""

    schema: str
    record_id: str
    source_surface: str
    route_handle: str
    sequence: int
    message_schema: str
    message_id: str
    route_id: str
    kind: str
    source: str
    target: str
    occurred_at: str
    payload_schema: str
    payload_hash: str
    message: dict[str, Any]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "record_id": self.record_id,
            "source_surface": self.source_surface,
            "route_handle": self.route_handle,
            "sequence": self.sequence,
            "message_schema": self.message_schema,
            "message_id": self.message_id,
            "route_id": self.route_id,
            "kind": self.kind,
            "source": self.source,
            "target": self.target,
            "occurred_at": self.occurred_at,
            "payload_schema": self.payload_schema,
            "payload_hash": self.payload_hash,
            "message": dict(self.message),
        }


@dataclass(frozen=True, slots=True)
class RouteMessageJournalSummary:
    """Summary of one drained-route journal write."""

    journal_path: str
    route_handle: str
    record_count: int
    appended: bool
    sequences: tuple[int, ...]
    message_ids: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "journal_path": self.journal_path,
            "route_handle": self.route_handle,
            "record_count": self.record_count,
            "appended": self.appended,
            "sequences": list(self.sequences),
            "message_ids": list(self.message_ids),
        }


def records_from_drained_route_messages(
    drained: RouteSelectorDrainResult,
) -> tuple[RouteMessageJournalRecord, ...]:
    """Convert a RouteSelectorDrainResult into immutable journal records.

    The function assumes upstream Scheduler/policy/zone already authorized the
    route work. It only records facts about messages that were drained.
    """

    _validate_drained_result(drained)
    source_surface = f"routes/{drained.route_handle}"
    records: list[RouteMessageJournalRecord] = []
    for sequence, message in zip(drained.drained_sequences, drained.messages, strict=True):
        records.append(_record_from_message(source_surface, drained.route_handle, sequence, message))
    return tuple(records)


def write_drained_route_messages_journal(
    journal_path: Path | str,
    drained: RouteSelectorDrainResult,
    *,
    append: bool = False,
) -> RouteMessageJournalSummary:
    """Write drained RouteMessage records to a deterministic JSONL journal."""

    records = records_from_drained_route_messages(drained)
    path = Path(journal_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_mapping(), sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    return RouteMessageJournalSummary(
        journal_path=str(path),
        route_handle=drained.route_handle,
        record_count=len(records),
        appended=append,
        sequences=tuple(record.sequence for record in records),
        message_ids=tuple(record.message_id for record in records),
    )


def load_route_message_journal(path: Path | str) -> tuple[RouteMessageJournalRecord, ...]:
    """Load records written by write_drained_route_messages_journal."""

    journal_path = Path(path)
    if not journal_path.exists():
        return ()
    records: list[RouteMessageJournalRecord] = []
    for line in journal_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        records.append(_record_from_mapping(raw))
    return tuple(records)


def _record_from_message(
    source_surface: str,
    route_handle: str,
    sequence: int,
    message: RouteMessage,
) -> RouteMessageJournalRecord:
    mapping = message.to_mapping()
    message_schema = str(mapping["schema"])
    if message_schema != ROUTE_MESSAGE_SCHEMA:
        raise ValueError("journal only accepts RouteMessage records")
    return RouteMessageJournalRecord(
        schema=ROUTE_MESSAGE_JOURNAL_RECORD_SCHEMA,
        record_id=f"{source_surface}:{sequence}:{message.message_id}",
        source_surface=source_surface,
        route_handle=route_handle,
        sequence=sequence,
        message_schema=message_schema,
        message_id=message.message_id,
        route_id=message.route_id,
        kind=message.kind,
        source=message.source,
        target=message.target,
        occurred_at=message.occurred_at,
        payload_schema=message.payload_schema,
        payload_hash=_stable_hash(mapping),
        message=mapping,
    )


def _record_from_mapping(raw: Mapping[str, Any]) -> RouteMessageJournalRecord:
    schema = str(raw["schema"])
    if schema != ROUTE_MESSAGE_JOURNAL_RECORD_SCHEMA:
        raise ValueError("unsupported route message journal record schema")
    message = dict(raw["message"])
    RouteMessage.from_mapping(message)
    return RouteMessageJournalRecord(
        schema=schema,
        record_id=str(raw["record_id"]),
        source_surface=str(raw["source_surface"]),
        route_handle=str(raw["route_handle"]),
        sequence=_require_int(raw, "sequence"),
        message_schema=str(raw["message_schema"]),
        message_id=str(raw["message_id"]),
        route_id=str(raw["route_id"]),
        kind=str(raw["kind"]),
        source=str(raw["source"]),
        target=str(raw["target"]),
        occurred_at=str(raw["occurred_at"]),
        payload_schema=str(raw["payload_schema"]),
        payload_hash=str(raw["payload_hash"]),
        message=message,
    )


def _validate_drained_result(drained: RouteSelectorDrainResult) -> None:
    if drained.drained_count != len(drained.drained_sequences):
        raise ValueError("drained result is inconsistent")
    if drained.drained_count != len(drained.messages):
        raise ValueError("drained result is inconsistent")
    if drained.drained_count != len(drained.message_ids):
        raise ValueError("drained result is inconsistent")
    for expected, message in zip(drained.message_ids, drained.messages, strict=True):
        if expected != message.message_id:
            raise ValueError("drained result message_ids do not match messages")


def _require_int(raw: Mapping[str, Any], field: str) -> int:
    value = raw[field]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    return value


def _stable_hash(mapping: Mapping[str, Any]) -> str:
    data = json.dumps(dict(mapping), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


__all__ = (
    "ROUTE_MESSAGE_JOURNAL_RECORD_SCHEMA",
    "RouteMessageJournalRecord",
    "RouteMessageJournalSummary",
    "load_route_message_journal",
    "records_from_drained_route_messages",
    "write_drained_route_messages_journal",
)
