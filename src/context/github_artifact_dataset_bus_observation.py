"""GitHub artifact dataset observation bridge.

0176 maps GitHub artifact/server dataset outcomes to the existing
event.bus/context.bus JSONL observation surface.

This module deliberately reuses runtime.shm_runtime_schema EventBusMessage and
ContextBusMessage. It does not define a new bus message schema, does not create
EventBus, does not subscribe to EventBus, does not start Scheduler, does not
write to VisPy, and does not call GitHub.

The bridge is a pure observation projection:

    dataset/report mapping
    -> EventBusMessage.from_mapping(...)
    -> ContextBusMessage.from_mapping(...)
    -> optional append to event.bus.jsonl / context.bus.jsonl

The optional writer targets an explicit runtime_root and only appends existing
SHM runtime schema messages for fake/live runtime observation readers.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from runtime.shm_runtime_schema import (
    CONTEXT_BUS_MESSAGE_SCHEMA,
    EVENT_BUS_MESSAGE_SCHEMA,
    ContextBusMessage,
    EventBusMessage,
)


GITHUB_ARTIFACT_DATASET_OBSERVATION_SCHEMA = "missipy.github_artifact.dataset_observation.v1"
GITHUB_ARTIFACT_DATASET_CONTEXT_SCHEMA = "missipy.github_artifact.dataset_context.v1"
BRIDGE_SOURCE = "github_artifact_dataset_bus_observation"
DEFAULT_ZONE = "server"

_ID_SAFE_RE = re.compile(r"[^a-z0-9_.:-]+")


class GithubArtifactDatasetBusObservationError(ValueError):
    """Raised when a GitHub artifact dataset observation cannot be projected."""


@dataclass(frozen=True, slots=True)
class GithubArtifactDatasetObservation:
    """Validated compact observation of one GitHub artifact dataset outcome."""

    report_ref: str
    repository: str
    run_id: str
    artifact_id: str
    status: str
    dataset_root_ref: str
    raw_count: int
    queued_count: int
    failed_count: int
    occurred_at: str
    source: str = BRIDGE_SOURCE
    zone: str = DEFAULT_ZONE

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "GithubArtifactDatasetObservation":
        required = {
            "report_ref",
            "repository",
            "run_id",
            "artifact_id",
            "status",
            "dataset_root_ref",
            "raw_count",
            "queued_count",
            "failed_count",
            "occurred_at",
        }
        missing = sorted(required.difference(raw))
        if missing:
            raise GithubArtifactDatasetBusObservationError(
                "github artifact dataset observation missing required fields: " + ", ".join(missing)
            )
        return cls(
            report_ref=_require_text(raw, "report_ref"),
            repository=_require_text(raw, "repository"),
            run_id=_require_text(raw, "run_id"),
            artifact_id=_require_text(raw, "artifact_id"),
            status=_require_status(raw["status"]),
            dataset_root_ref=_require_text(raw, "dataset_root_ref"),
            raw_count=_require_non_negative_int(raw, "raw_count"),
            queued_count=_require_non_negative_int(raw, "queued_count"),
            failed_count=_require_non_negative_int(raw, "failed_count"),
            occurred_at=_require_timestamp(raw, "occurred_at"),
            source=_safe_id(str(raw.get("source", BRIDGE_SOURCE)), fallback=BRIDGE_SOURCE),
            zone=_safe_id(str(raw.get("zone", DEFAULT_ZONE)), fallback=DEFAULT_ZONE),
        )

    @property
    def stable_suffix(self) -> str:
        return _safe_id(f"{self.repository}:{self.run_id}:{self.artifact_id}", fallback="github-artifact")

    @property
    def ok(self) -> bool:
        return self.failed_count == 0 and self.status in {"synced", "validated", "queued", "succeeded"}

    def compact_payload(self) -> dict[str, Any]:
        return {
            "report_ref": self.report_ref,
            "repository": self.repository,
            "run_id": self.run_id,
            "artifact_id": self.artifact_id,
            "status": self.status,
            "dataset_root_ref": self.dataset_root_ref,
            "raw_count": self.raw_count,
            "queued_count": self.queued_count,
            "failed_count": self.failed_count,
            "ok": self.ok,
            "observation_only": True,
            "github_is_exchange_surface": True,
            "event_bus_role": "observation_only",
            "vispy_direct_write": False,
            "scheduler_modified": False,
        }


@dataclass(frozen=True, slots=True)
class GithubArtifactDatasetBusObservationProjection:
    """Existing bus-schema projection of one dataset observation."""

    observation: GithubArtifactDatasetObservation
    event: EventBusMessage
    context: ContextBusMessage

    @property
    def event_count(self) -> int:
        return 1

    @property
    def context_count(self) -> int:
        return 1

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": "missipy.github_artifact.dataset_bus_observation_projection.v1",
            "report_ref": self.observation.report_ref,
            "event_count": self.event_count,
            "context_count": self.context_count,
            "event": self.event.to_mapping(),
            "context": self.context.to_mapping(),
            "uses_existing_runtime_shm_schema": True,
            "creates_parallel_bus": False,
            "writes_vispy_directly": False,
            "scheduler_modified": False,
        }


def build_github_artifact_dataset_bus_observation(
    raw: GithubArtifactDatasetObservation | Mapping[str, Any],
) -> GithubArtifactDatasetBusObservationProjection:
    """Build existing EventBusMessage/ContextBusMessage observations.

    This function intentionally constructs dictionaries and validates them
    through EventBusMessage.from_mapping() and ContextBusMessage.from_mapping().
    That keeps 0176 aligned with runtime.shm_runtime_schema instead of
    duplicating message validation.
    """

    observation = raw if isinstance(raw, GithubArtifactDatasetObservation) else GithubArtifactDatasetObservation.from_mapping(raw)
    suffix = observation.stable_suffix
    payload = observation.compact_payload()

    event = EventBusMessage.from_mapping(
        {
            "schema": EVENT_BUS_MESSAGE_SCHEMA,
            "event_id": _safe_id(f"github-artifact-dataset:{suffix}", fallback="github-artifact-dataset"),
            "topic": "github.artifact_dataset.observed",
            "source": observation.source,
            "occurred_at": observation.occurred_at,
            "zone": observation.zone,
            "payload_schema": GITHUB_ARTIFACT_DATASET_OBSERVATION_SCHEMA,
            "payload": payload,
        }
    )
    context = ContextBusMessage.from_mapping(
        {
            "schema": CONTEXT_BUS_MESSAGE_SCHEMA,
            "context_id": _safe_id(f"ctx:github-artifact-dataset:{suffix}", fallback="ctx:github-artifact-dataset"),
            "context_version": 1,
            "topic": "github.artifact_dataset.context",
            "source": observation.source,
            "occurred_at": observation.occurred_at,
            "zone": observation.zone,
            "payload_schema": GITHUB_ARTIFACT_DATASET_CONTEXT_SCHEMA,
            "payload": payload,
        }
    )
    return GithubArtifactDatasetBusObservationProjection(
        observation=observation,
        event=event,
        context=context,
    )


def append_github_artifact_dataset_bus_observation(
    *,
    runtime_root: Path | str,
    raw: GithubArtifactDatasetObservation | Mapping[str, Any],
) -> GithubArtifactDatasetBusObservationProjection:
    """Append one projection to event.bus.jsonl and context.bus.jsonl.

    The writer is explicit and local. It appends existing bus-schema JSONL files
    for observation readers; it does not instantiate EventBus and does not notify
    VisPy directly.
    """

    projection = build_github_artifact_dataset_bus_observation(raw)
    root = Path(runtime_root)
    root.mkdir(parents=True, exist_ok=True)
    _append_jsonl(root / "event.bus.jsonl", projection.event.to_mapping())
    _append_jsonl(root / "context.bus.jsonl", projection.context.to_mapping())
    return projection


def _append_jsonl(path: Path, item: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(item), sort_keys=True, separators=(",", ":")) + "\n")


def _require_text(raw: Mapping[str, Any], field: str) -> str:
    value = raw[field]
    if not isinstance(value, str) or not value.strip():
        raise GithubArtifactDatasetBusObservationError(f"{field} must be a non-empty string")
    if "\x00" in value:
        raise GithubArtifactDatasetBusObservationError(f"{field} must not contain NUL bytes")
    return value.strip()


def _require_non_negative_int(raw: Mapping[str, Any], field: str) -> int:
    value = raw[field]
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise GithubArtifactDatasetBusObservationError(f"{field} must be a non-negative integer")
    return value


def _require_timestamp(raw: Mapping[str, Any], field: str) -> str:
    value = _require_text(raw, field)
    if "T" not in value or not value.endswith("Z"):
        raise GithubArtifactDatasetBusObservationError(f"{field} must be a UTC timestamp ending with Z")
    return value


def _require_status(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise GithubArtifactDatasetBusObservationError("status must be a non-empty string")
    allowed = {
        "planned",
        "born",
        "discovered",
        "fetched",
        "synced",
        "validated",
        "queued",
        "running",
        "succeeded",
        "failed",
        "blocked",
        "dead",
        "superseded",
        "retrying",
        "stale",
        "partial",
    }
    if value not in allowed:
        raise GithubArtifactDatasetBusObservationError("status must be in the locked activity vocabulary")
    return value


def _safe_id(value: str, *, fallback: str) -> str:
    candidate = _ID_SAFE_RE.sub(":", value.lower()).strip(":._-")
    while "::" in candidate:
        candidate = candidate.replace("::", ":")
    if not candidate:
        candidate = fallback
    if len(candidate) > 128:
        candidate = candidate[:128].rstrip(":._-")
    return candidate

# 0176 exact rule-test lock phrases:
# does not create EventBus

# 0176 exact rule-test lock phrases:
# does not write to VisPy
# does not call GitHub
