from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
import json
import os
import tempfile


_AUDIT_EVENT_SCHEMA = "missipy.source_candidate.external_probe_local_audit_event.v1"
_AUDIT_REPORT_SCHEMA = "missipy.source_candidate.external_probe_local_audit_report.v1"
_SUMMARY_SCHEMA = "missipy.source_candidate.external_probe_operator_summary.v1"


@dataclass(frozen=True)
class SourceCandidateExternalProbeLocalAuditEvent:
    event_id: str
    created_at: str
    event_kind: str
    summary_path: Path
    bundle_count: int
    ready_count: int
    check_count: int
    blocked_count: int
    total_artifact_count: int
    total_byte_count: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _AUDIT_EVENT_SCHEMA,
            "event_id": self.event_id,
            "created_at": self.created_at,
            "event_kind": self.event_kind,
            "summary_path": str(self.summary_path),
            "bundle_count": self.bundle_count,
            "ready_count": self.ready_count,
            "check_count": self.check_count,
            "blocked_count": self.blocked_count,
            "total_artifact_count": self.total_artifact_count,
            "total_byte_count": self.total_byte_count,
        }


@dataclass(frozen=True)
class SourceCandidateExternalProbeLocalAuditReport:
    audit_log_path: Path
    event_count: int
    ready_count: int
    check_count: int
    blocked_count: int
    latest_event_id: str | None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _AUDIT_REPORT_SCHEMA,
            "audit_log_path": str(self.audit_log_path),
            "event_count": self.event_count,
            "ready_count": self.ready_count,
            "check_count": self.check_count,
            "blocked_count": self.blocked_count,
            "latest_event_id": self.latest_event_id,
        }


def build_source_candidate_external_probe_local_audit_event(
    *,
    summary_path: Path,
    summary_payload: Mapping[str, Any],
    event_kind: str = "external_probe_operator_summary_recorded",
    created_at: str | None = None,
) -> SourceCandidateExternalProbeLocalAuditEvent:
    if summary_payload.get("schema") != _SUMMARY_SCHEMA:
        raise ValueError("external probe operator summary schema mismatch")

    timestamp = created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    event_id = _event_id(summary_path=summary_path, created_at=timestamp)

    return SourceCandidateExternalProbeLocalAuditEvent(
        event_id=event_id,
        created_at=timestamp,
        event_kind=event_kind,
        summary_path=summary_path,
        bundle_count=_int(summary_payload.get("bundle_count")),
        ready_count=_int(summary_payload.get("ready_count")),
        check_count=_int(summary_payload.get("check_count")),
        blocked_count=_int(summary_payload.get("blocked_count")),
        total_artifact_count=_int(summary_payload.get("total_artifact_count")),
        total_byte_count=_int(summary_payload.get("total_byte_count")),
    )


def append_source_candidate_external_probe_local_audit_event(
    *,
    audit_log_path: Path,
    event: SourceCandidateExternalProbeLocalAuditEvent,
) -> Path:
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.to_json_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    return audit_log_path


def record_source_candidate_external_probe_operator_summary(
    *,
    audit_log_path: Path,
    summary_path: Path,
    created_at: str | None = None,
) -> SourceCandidateExternalProbeLocalAuditEvent:
    event = build_source_candidate_external_probe_local_audit_event(
        summary_path=summary_path,
        summary_payload=_read_json_object(summary_path),
        created_at=created_at,
    )
    append_source_candidate_external_probe_local_audit_event(
        audit_log_path=audit_log_path,
        event=event,
    )
    return event


def build_source_candidate_external_probe_local_audit_report(
    audit_log_path: Path,
) -> SourceCandidateExternalProbeLocalAuditReport:
    events = read_source_candidate_external_probe_local_audit_events(audit_log_path)
    latest = events[-1].get("event_id") if events else None
    latest_event_id = latest if isinstance(latest, str) else None

    return SourceCandidateExternalProbeLocalAuditReport(
        audit_log_path=audit_log_path,
        event_count=len(events),
        ready_count=sum(_int(event.get("ready_count")) for event in events),
        check_count=sum(_int(event.get("check_count")) for event in events),
        blocked_count=sum(_int(event.get("blocked_count")) for event in events),
        latest_event_id=latest_event_id,
    )


def read_source_candidate_external_probe_local_audit_events(
    audit_log_path: Path,
) -> tuple[dict[str, Any], ...]:
    if not audit_log_path.exists():
        return ()

    events: list[dict[str, Any]] = []
    for line in audit_log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, Mapping):
            raise ValueError("audit event line must be a JSON object")
        if payload.get("schema") != _AUDIT_EVENT_SCHEMA:
            raise ValueError("audit event schema mismatch")
        events.append(dict(payload))
    return tuple(events)


def write_source_candidate_external_probe_local_audit_report(
    path: Path,
    report: SourceCandidateExternalProbeLocalAuditReport,
) -> Path:
    _atomic_write_json(path, report.to_json_dict())
    return path


def render_source_candidate_external_probe_local_audit_report(
    report: SourceCandidateExternalProbeLocalAuditReport,
) -> str:
    return "\n".join(
        [
            "external probe local audit trail",
            f"audit_log_path: {report.audit_log_path}",
            f"event_count: {report.event_count}",
            f"ready_count: {report.ready_count}",
            f"check_count: {report.check_count}",
            f"blocked_count: {report.blocked_count}",
            f"latest_event_id: {report.latest_event_id or '<none>'}",
        ]
    )


def _event_id(*, summary_path: Path, created_at: str) -> str:
    safe_path = str(summary_path).replace(os.sep, "_").replace(":", "_").strip("_")
    safe_time = created_at.replace(":", "").replace("+", "p")
    return f"{safe_time}__{safe_path}"


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _int(raw: object) -> int:
    if isinstance(raw, int):
        return raw
    return 0


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        tmp_name = handle.name
        handle.write(text)
    os.replace(tmp_name, path)
