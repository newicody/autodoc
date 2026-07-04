"""ControlFS manifest parsing and validation.

This module implements the executable ControlProxy declarative surface.

Architecture vocabulary locked by 0079-r2:

    ControlProxy = ControlFS declarative surface + RouteProxy materializer.

This module deliberately does not:
- create shared memory
- create semaphores
- implement mmap
- resize a live mmap ring
- start a daemon
- change Scheduler behavior
- mutate ControlFS directories

It only parses and validates route manifests that describe desired routes.
The passive ControlProxy/RouteProxy materializer can later consume this model.

Compatibility note for older rule tests:
- start a RouteProxy daemon
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any, Mapping


ROUTE_MANIFEST_SCHEMA = "missipy.controlfs.route_manifest.v1"
LEASE_MANIFEST_SCHEMA = "missipy.controlfs.lease_manifest.v1"
STATUS_MANIFEST_SCHEMA = "missipy.controlfs.status_manifest.v1"

_ROUTE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}$")
_MODE_VALUES = {"rw", "ro", "wo", "control"}
_TRANSPORT_VALUES = {"fake.jsonl", "inprocess.frame_ring", "mmap.fixed_slot"}
_OVERFLOW_POLICY_VALUES = {"reject", "drop_oldest"}
_NOTIFY_VALUES = {"none", "semaphore", "eventfd", "futex"}
_TTL_MIN_SECONDS = 1
_TTL_MAX_SECONDS = 24 * 60 * 60
_SLOT_SIZE_MIN = 64
_SLOT_SIZE_MAX = 16 * 1024 * 1024
_SLOT_COUNT_MIN = 1
_SLOT_COUNT_MAX = 1_000_000


class ManifestValidationError(ValueError):
    """Raised when a ControlFS manifest is invalid."""


@dataclass(frozen=True)
class RouteManifest:
    """Desired route manifest stored under ControlFS desired/routes/<route_id>.

    Minimal JSON shape:

    {
      "schema": "missipy.controlfs.route_manifest.v1",
      "route_id": "baby_fork.retrieval",
      "task_id": "baby_fork_smoke",
      "zone": "workers",
      "scope": "context.read",
      "producer": "scheduler",
      "consumer": "retrieval_worker",
      "ttl_seconds": 30,
      "mode": "rw",
      "message_schema": "missipy.runtime.route_message.v1",
      "created_by": "scheduler",
      "created_at": "2026-07-04T20:00:00Z"
    }

    Optional ControlProxy sizing fields:

    {
      "transport": "mmap.fixed_slot",
      "slot_size": 2048,
      "slot_count": 16,
      "max_frame_bytes": 2048,
      "overflow_policy": "reject",
      "notify": "semaphore",
      "sizing_source": "controlproxy.prepare",
      "observed_frame_bytes": 890
    }
    """

    schema: str
    route_id: str
    task_id: str
    zone: str
    scope: str
    producer: str
    consumer: str
    ttl_seconds: int
    mode: str
    message_schema: str
    created_by: str
    created_at: str
    transport: str | None = None
    slot_size: int | None = None
    slot_count: int | None = None
    max_frame_bytes: int | None = None
    overflow_policy: str | None = None
    notify: str | None = None
    sizing_source: str | None = None
    observed_frame_bytes: int | None = None

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "RouteManifest":
        """Validate and build a RouteManifest from a JSON-like mapping."""

        required = {
            "schema",
            "route_id",
            "task_id",
            "zone",
            "scope",
            "producer",
            "consumer",
            "ttl_seconds",
            "mode",
            "message_schema",
            "created_by",
            "created_at",
        }
        missing = sorted(required.difference(raw))
        if missing:
            raise ManifestValidationError(
                "route manifest missing required fields: " + ", ".join(missing)
            )

        manifest = cls(
            schema=_require_str(raw, "schema"),
            route_id=normalize_route_id(_require_str(raw, "route_id")),
            task_id=_require_name(raw, "task_id"),
            zone=_require_name(raw, "zone"),
            scope=_require_scope(raw, "scope"),
            producer=_require_name(raw, "producer"),
            consumer=_require_name(raw, "consumer"),
            ttl_seconds=_require_ttl(raw, "ttl_seconds"),
            mode=_require_mode(raw, "mode"),
            message_schema=_require_str(raw, "message_schema"),
            created_by=_require_name(raw, "created_by"),
            created_at=_require_str(raw, "created_at"),
            transport=_optional_transport(raw, "transport"),
            slot_size=_optional_bounded_int(raw, "slot_size", _SLOT_SIZE_MIN, _SLOT_SIZE_MAX),
            slot_count=_optional_bounded_int(raw, "slot_count", _SLOT_COUNT_MIN, _SLOT_COUNT_MAX),
            max_frame_bytes=_optional_bounded_int(raw, "max_frame_bytes", 1, _SLOT_SIZE_MAX),
            overflow_policy=_optional_choice(raw, "overflow_policy", _OVERFLOW_POLICY_VALUES),
            notify=_optional_choice(raw, "notify", _NOTIFY_VALUES),
            sizing_source=_optional_name(raw, "sizing_source"),
            observed_frame_bytes=_optional_bounded_int(raw, "observed_frame_bytes", 1, _SLOT_SIZE_MAX),
        )

        if manifest.schema != ROUTE_MANIFEST_SCHEMA:
            raise ManifestValidationError(
                f"unsupported route manifest schema: {manifest.schema!r}"
            )

        if not manifest.message_schema.startswith("missipy."):
            raise ManifestValidationError(
                "message_schema must use a missipy.* schema name"
            )

        if ".." in manifest.created_at or "/" in manifest.created_at:
            raise ManifestValidationError("created_at must be a timestamp, not a path")

        if manifest.max_frame_bytes is not None and manifest.slot_size is not None:
            if manifest.max_frame_bytes > manifest.slot_size:
                raise ManifestValidationError("max_frame_bytes must be <= slot_size")

        if manifest.observed_frame_bytes is not None and manifest.max_frame_bytes is not None:
            if manifest.observed_frame_bytes > manifest.max_frame_bytes:
                raise ManifestValidationError("observed_frame_bytes must be <= max_frame_bytes")

        if manifest.transport == "mmap.fixed_slot":
            for field_name in ("slot_size", "slot_count", "max_frame_bytes", "overflow_policy", "notify"):
                if getattr(manifest, field_name) is None:
                    raise ManifestValidationError(
                        f"{field_name} is required when transport is mmap.fixed_slot"
                    )

        return manifest

    @classmethod
    def from_json(cls, text: str) -> "RouteManifest":
        """Parse and validate a route manifest from JSON text."""

        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ManifestValidationError(f"invalid JSON: {exc}") from exc

        if not isinstance(raw, dict):
            raise ManifestValidationError("route manifest JSON must be an object")

        return cls.from_mapping(raw)

    @classmethod
    def from_path(cls, path: Path | str) -> "RouteManifest":
        """Load and validate a route manifest from a file path."""

        p = Path(path)
        return cls.from_json(p.read_text(encoding="utf-8"))

    def to_mapping(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable mapping."""

        payload: dict[str, Any] = {
            "schema": self.schema,
            "route_id": self.route_id,
            "task_id": self.task_id,
            "zone": self.zone,
            "scope": self.scope,
            "producer": self.producer,
            "consumer": self.consumer,
            "ttl_seconds": self.ttl_seconds,
            "mode": self.mode,
            "message_schema": self.message_schema,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }

        optional = {
            "transport": self.transport,
            "slot_size": self.slot_size,
            "slot_count": self.slot_count,
            "max_frame_bytes": self.max_frame_bytes,
            "overflow_policy": self.overflow_policy,
            "notify": self.notify,
            "sizing_source": self.sizing_source,
            "observed_frame_bytes": self.observed_frame_bytes,
        }
        for key, value in optional.items():
            if value is not None:
                payload[key] = value

        return payload


def normalize_route_id(route_id: str) -> str:
    """Validate and normalize a route_id.

    Route IDs are logical identifiers, not paths. They must never contain path
    separators or traversal components.
    """

    if not isinstance(route_id, str):
        raise ManifestValidationError("route_id must be a string")

    value = route_id.strip()
    if value != route_id:
        raise ManifestValidationError("route_id must not contain leading/trailing whitespace")

    if "/" in value or "\\" in value or ".." in value:
        raise ManifestValidationError("route_id must not contain path traversal")

    if not _ROUTE_ID_RE.fullmatch(value):
        raise ManifestValidationError(
            "route_id must match ^[a-z0-9][a-z0-9_.-]{0,127}$"
        )

    return value


def route_manifest_path(controlfs_root: Path | str, route_id: str) -> Path:
    """Return desired/routes/<route_id>/manifest.json under a ControlFS root."""

    safe_route_id = normalize_route_id(route_id)
    return Path(controlfs_root) / "desired" / "routes" / safe_route_id / "manifest.json"


def load_desired_route_manifest(controlfs_root: Path | str, route_id: str) -> RouteManifest:
    """Load a desired route manifest from ControlFS."""

    return RouteManifest.from_path(route_manifest_path(controlfs_root, route_id))


def _require_str(raw: Mapping[str, Any], field: str) -> str:
    value = raw[field]
    if not isinstance(value, str) or not value:
        raise ManifestValidationError(f"{field} must be a non-empty string")
    return value


def _require_name(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if "/" in value or "\\" in value or ".." in value:
        raise ManifestValidationError(f"{field} must not contain path traversal")
    if not _NAME_RE.fullmatch(value):
        raise ManifestValidationError(f"{field} contains invalid characters")
    return value


def _require_scope(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if "/" in value or "\\" in value or ".." in value:
        raise ManifestValidationError(f"{field} must not contain path traversal")
    if not _NAME_RE.fullmatch(value):
        raise ManifestValidationError(f"{field} contains invalid characters")
    if "." not in value:
        raise ManifestValidationError(f"{field} should use subsystem.permission form")
    return value


def _require_ttl(raw: Mapping[str, Any], field: str) -> int:
    value = raw[field]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ManifestValidationError(f"{field} must be an integer number of seconds")
    if value < _TTL_MIN_SECONDS or value > _TTL_MAX_SECONDS:
        raise ManifestValidationError(
            f"{field} must be between {_TTL_MIN_SECONDS} and {_TTL_MAX_SECONDS}"
        )
    return value


def _require_mode(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if value not in _MODE_VALUES:
        raise ManifestValidationError(
            f"{field} must be one of: " + ", ".join(sorted(_MODE_VALUES))
        )
    return value


def _optional_name(raw: Mapping[str, Any], field: str) -> str | None:
    if field not in raw or raw[field] is None:
        return None
    return _require_name(raw, field)


def _optional_transport(raw: Mapping[str, Any], field: str) -> str | None:
    if field not in raw or raw[field] is None:
        return None
    value = _require_name(raw, field)
    if value not in _TRANSPORT_VALUES:
        raise ManifestValidationError(
            f"{field} must be one of: " + ", ".join(sorted(_TRANSPORT_VALUES))
        )
    return value


def _optional_choice(raw: Mapping[str, Any], field: str, allowed: set[str]) -> str | None:
    if field not in raw or raw[field] is None:
        return None
    value = _require_name(raw, field)
    if value not in allowed:
        raise ManifestValidationError(
            f"{field} must be one of: " + ", ".join(sorted(allowed))
        )
    return value


def _optional_bounded_int(raw: Mapping[str, Any], field: str, minimum: int, maximum: int) -> int | None:
    if field not in raw or raw[field] is None:
        return None
    value = raw[field]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ManifestValidationError(f"{field} must be an integer")
    if value < minimum or value > maximum:
        raise ManifestValidationError(f"{field} must be between {minimum} and {maximum}")
    return value
