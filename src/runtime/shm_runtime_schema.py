"""SHM Runtime message schemas.

This module implements the P3 schema-only phase for the local SHM Runtime.

It deliberately does not:
- create shared memory
- create semaphores
- implement a ring buffer
- call Scheduler
- call RouteProxy
- write ControlFS
- access ZFS
- implement NetworkBridge or HardwareBridge

It only validates compact message structures that can later be transported by
event.bus, context.bus, data.index and routes/<route_id>.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Mapping


EVENT_BUS_MESSAGE_SCHEMA = "missipy.shm.event_message.v1"
CONTEXT_BUS_MESSAGE_SCHEMA = "missipy.shm.context_message.v1"
DATA_HANDLE_SCHEMA = "missipy.shm.data_handle.v1"
ROUTE_MESSAGE_SCHEMA = "missipy.shm.route_message.v1"

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
_TOPIC_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
_HASH_RE = re.compile(r"^[a-z0-9][a-z0-9_:+./=-]{0,255}$")
_STORAGE_VALUES = {"memfd", "shm", "tmpfs", "zfs", "nvme", "remote", "hardware"}
_ROUTE_KIND_VALUES = {"request", "reply", "event", "context_patch", "data_handle", "control"}
_MAX_COMPACT_PAYLOAD_BYTES = 64 * 1024


class RuntimeSchemaValidationError(ValueError):
    """Raised when a SHM Runtime schema object is invalid."""


@dataclass(frozen=True)
class DataHandle:
    """Compact reference to payload stored outside the hot bus."""

    schema: str
    handle_id: str
    storage: str
    uri: str
    content_schema: str
    size_bytes: int
    hash: str
    producer: str
    zone: str
    created_at: str
    ttl_seconds: int | None = None

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "DataHandle":
        required = {
            "schema", "handle_id", "storage", "uri", "content_schema",
            "size_bytes", "hash", "producer", "zone", "created_at",
        }
        missing = sorted(required.difference(raw))
        if missing:
            raise RuntimeSchemaValidationError(
                "data handle missing required fields: " + ", ".join(missing)
            )

        return cls(
            schema=_require_schema(raw, "schema", DATA_HANDLE_SCHEMA),
            handle_id=_require_id(raw, "handle_id"),
            storage=_require_value(raw, "storage", _STORAGE_VALUES),
            uri=_require_uri(raw, "uri"),
            content_schema=_require_missipy_schema(raw, "content_schema"),
            size_bytes=_require_non_negative_int(raw, "size_bytes"),
            hash=_require_hash(raw, "hash"),
            producer=_require_id(raw, "producer"),
            zone=_require_id(raw, "zone"),
            created_at=_require_timestamp(raw, "created_at"),
            ttl_seconds=_optional_positive_int(raw, "ttl_seconds"),
        )

    @classmethod
    def from_json(cls, text: str) -> "DataHandle":
        return cls.from_mapping(_json_object(text, "data handle"))

    def to_mapping(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": self.schema,
            "handle_id": self.handle_id,
            "storage": self.storage,
            "uri": self.uri,
            "content_schema": self.content_schema,
            "size_bytes": self.size_bytes,
            "hash": self.hash,
            "producer": self.producer,
            "zone": self.zone,
            "created_at": self.created_at,
        }
        if self.ttl_seconds is not None:
            payload["ttl_seconds"] = self.ttl_seconds
        return payload


@dataclass(frozen=True)
class EventBusMessage:
    """Lightweight fact message for event.bus."""

    schema: str
    event_id: str
    topic: str
    source: str
    occurred_at: str
    zone: str
    payload_schema: str
    payload: dict[str, Any]
    data_handles: tuple[DataHandle, ...] = ()

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "EventBusMessage":
        required = {"schema", "event_id", "topic", "source", "occurred_at", "zone", "payload_schema", "payload"}
        missing = sorted(required.difference(raw))
        if missing:
            raise RuntimeSchemaValidationError("event message missing required fields: " + ", ".join(missing))
        payload = _require_payload(raw, "payload")
        _reject_large_payload(payload, "event payload")
        return cls(
            schema=_require_schema(raw, "schema", EVENT_BUS_MESSAGE_SCHEMA),
            event_id=_require_id(raw, "event_id"),
            topic=_require_topic(raw, "topic"),
            source=_require_id(raw, "source"),
            occurred_at=_require_timestamp(raw, "occurred_at"),
            zone=_require_id(raw, "zone"),
            payload_schema=_require_missipy_schema(raw, "payload_schema"),
            payload=payload,
            data_handles=_optional_data_handles(raw),
        )

    @classmethod
    def from_json(cls, text: str) -> "EventBusMessage":
        return cls.from_mapping(_json_object(text, "event message"))

    def to_mapping(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": self.schema,
            "event_id": self.event_id,
            "topic": self.topic,
            "source": self.source,
            "occurred_at": self.occurred_at,
            "zone": self.zone,
            "payload_schema": self.payload_schema,
            "payload": self.payload,
        }
        if self.data_handles:
            payload["data_handles"] = [handle.to_mapping() for handle in self.data_handles]
        return payload


@dataclass(frozen=True)
class ContextBusMessage:
    """Compact active context message for context.bus."""

    schema: str
    context_id: str
    context_version: int
    topic: str
    source: str
    occurred_at: str
    zone: str
    payload_schema: str
    payload: dict[str, Any]
    data_handles: tuple[DataHandle, ...] = ()

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ContextBusMessage":
        required = {"schema", "context_id", "context_version", "topic", "source", "occurred_at", "zone", "payload_schema", "payload"}
        missing = sorted(required.difference(raw))
        if missing:
            raise RuntimeSchemaValidationError("context message missing required fields: " + ", ".join(missing))
        payload = _require_payload(raw, "payload")
        _reject_large_payload(payload, "context payload")
        return cls(
            schema=_require_schema(raw, "schema", CONTEXT_BUS_MESSAGE_SCHEMA),
            context_id=_require_id(raw, "context_id"),
            context_version=_require_positive_int(raw, "context_version"),
            topic=_require_topic(raw, "topic"),
            source=_require_id(raw, "source"),
            occurred_at=_require_timestamp(raw, "occurred_at"),
            zone=_require_id(raw, "zone"),
            payload_schema=_require_missipy_schema(raw, "payload_schema"),
            payload=payload,
            data_handles=_optional_data_handles(raw),
        )

    @classmethod
    def from_json(cls, text: str) -> "ContextBusMessage":
        return cls.from_mapping(_json_object(text, "context message"))

    def to_mapping(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": self.schema,
            "context_id": self.context_id,
            "context_version": self.context_version,
            "topic": self.topic,
            "source": self.source,
            "occurred_at": self.occurred_at,
            "zone": self.zone,
            "payload_schema": self.payload_schema,
            "payload": self.payload,
        }
        if self.data_handles:
            payload["data_handles"] = [handle.to_mapping() for handle in self.data_handles]
        return payload


@dataclass(frozen=True)
class RouteMessage:
    """Compact message sent over a materialized route."""

    schema: str
    route_id: str
    message_id: str
    kind: str
    source: str
    target: str
    occurred_at: str
    payload_schema: str
    payload: dict[str, Any]
    data_handles: tuple[DataHandle, ...] = ()

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "RouteMessage":
        required = {"schema", "route_id", "message_id", "kind", "source", "target", "occurred_at", "payload_schema", "payload"}
        missing = sorted(required.difference(raw))
        if missing:
            raise RuntimeSchemaValidationError("route message missing required fields: " + ", ".join(missing))
        payload = _require_payload(raw, "payload")
        _reject_large_payload(payload, "route payload")
        return cls(
            schema=_require_schema(raw, "schema", ROUTE_MESSAGE_SCHEMA),
            route_id=_require_id(raw, "route_id"),
            message_id=_require_id(raw, "message_id"),
            kind=_require_value(raw, "kind", _ROUTE_KIND_VALUES),
            source=_require_id(raw, "source"),
            target=_require_id(raw, "target"),
            occurred_at=_require_timestamp(raw, "occurred_at"),
            payload_schema=_require_missipy_schema(raw, "payload_schema"),
            payload=payload,
            data_handles=_optional_data_handles(raw),
        )

    @classmethod
    def from_json(cls, text: str) -> "RouteMessage":
        return cls.from_mapping(_json_object(text, "route message"))

    def to_mapping(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": self.schema,
            "route_id": self.route_id,
            "message_id": self.message_id,
            "kind": self.kind,
            "source": self.source,
            "target": self.target,
            "occurred_at": self.occurred_at,
            "payload_schema": self.payload_schema,
            "payload": self.payload,
        }
        if self.data_handles:
            payload["data_handles"] = [handle.to_mapping() for handle in self.data_handles]
        return payload


def classify_runtime_message(raw: Mapping[str, Any]) -> str:
    """Classify a runtime schema object by its schema field."""

    schema = _require_str(raw, "schema")
    if schema == EVENT_BUS_MESSAGE_SCHEMA:
        return "event"
    if schema == CONTEXT_BUS_MESSAGE_SCHEMA:
        return "context"
    if schema == DATA_HANDLE_SCHEMA:
        return "data"
    if schema == ROUTE_MESSAGE_SCHEMA:
        return "route"
    raise RuntimeSchemaValidationError(f"unknown runtime message schema: {schema!r}")


def parse_runtime_message(raw: Mapping[str, Any]) -> EventBusMessage | ContextBusMessage | DataHandle | RouteMessage:
    """Parse any known SHM Runtime schema object."""

    kind = classify_runtime_message(raw)
    if kind == "event":
        return EventBusMessage.from_mapping(raw)
    if kind == "context":
        return ContextBusMessage.from_mapping(raw)
    if kind == "data":
        return DataHandle.from_mapping(raw)
    if kind == "route":
        return RouteMessage.from_mapping(raw)
    raise AssertionError(f"unhandled runtime message kind: {kind}")


def parse_runtime_json(text: str) -> EventBusMessage | ContextBusMessage | DataHandle | RouteMessage:
    """Parse any known SHM Runtime JSON object."""

    return parse_runtime_message(_json_object(text, "runtime message"))


def _json_object(text: str, label: str) -> dict[str, Any]:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeSchemaValidationError(f"invalid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise RuntimeSchemaValidationError(f"{label} JSON must be an object")
    return raw


def _require_str(raw: Mapping[str, Any], field: str) -> str:
    value = raw[field]
    if not isinstance(value, str) or not value:
        raise RuntimeSchemaValidationError(f"{field} must be a non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise RuntimeSchemaValidationError(f"{field} must not contain path traversal")
    return value


def _require_id(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if not _ID_RE.fullmatch(value):
        raise RuntimeSchemaValidationError(f"{field} contains invalid characters")
    return value


def _require_topic(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if not _TOPIC_RE.fullmatch(value):
        raise RuntimeSchemaValidationError(f"{field} contains invalid characters")
    if "." not in value:
        raise RuntimeSchemaValidationError(f"{field} should be dotted, e.g. route.opened")
    return value


def _require_schema(raw: Mapping[str, Any], field: str, expected: str) -> str:
    value = _require_str(raw, field)
    if value != expected:
        raise RuntimeSchemaValidationError(f"{field} must be {expected!r}")
    return value


def _require_missipy_schema(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if not value.startswith("missipy."):
        raise RuntimeSchemaValidationError(f"{field} must start with missipy.")
    return value


def _require_value(raw: Mapping[str, Any], field: str, allowed: set[str]) -> str:
    value = _require_str(raw, field)
    if value not in allowed:
        raise RuntimeSchemaValidationError(f"{field} must be one of: " + ", ".join(sorted(allowed)))
    return value


def _require_uri(raw: Mapping[str, Any], field: str) -> str:
    value = raw[field]
    if not isinstance(value, str) or not value:
        raise RuntimeSchemaValidationError(f"{field} must be a non-empty string")
    if "\x00" in value:
        raise RuntimeSchemaValidationError(f"{field} must not contain NUL bytes")
    return value


def _require_hash(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if not _HASH_RE.fullmatch(value):
        raise RuntimeSchemaValidationError(f"{field} contains invalid characters")
    return value


def _require_timestamp(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if "T" not in value or not value.endswith("Z"):
        raise RuntimeSchemaValidationError(f"{field} must be a UTC timestamp ending with Z")
    return value


def _require_payload(raw: Mapping[str, Any], field: str) -> dict[str, Any]:
    value = raw[field]
    if not isinstance(value, dict):
        raise RuntimeSchemaValidationError(f"{field} must be an object")
    return dict(value)


def _require_non_negative_int(raw: Mapping[str, Any], field: str) -> int:
    value = raw[field]
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RuntimeSchemaValidationError(f"{field} must be a non-negative integer")
    return value


def _require_positive_int(raw: Mapping[str, Any], field: str) -> int:
    value = raw[field]
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise RuntimeSchemaValidationError(f"{field} must be a positive integer")
    return value


def _optional_positive_int(raw: Mapping[str, Any], field: str) -> int | None:
    if field not in raw or raw[field] is None:
        return None
    value = raw[field]
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise RuntimeSchemaValidationError(f"{field} must be a positive integer")
    return value


def _optional_data_handles(raw: Mapping[str, Any]) -> tuple[DataHandle, ...]:
    if "data_handles" not in raw:
        return ()
    value = raw["data_handles"]
    if not isinstance(value, list):
        raise RuntimeSchemaValidationError("data_handles must be a list")
    return tuple(DataHandle.from_mapping(item) for item in value)


def _reject_large_payload(payload: Mapping[str, Any], label: str) -> None:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > _MAX_COMPACT_PAYLOAD_BYTES:
        raise RuntimeSchemaValidationError(f"{label} is too large for compact bus payload; use DataHandle")
