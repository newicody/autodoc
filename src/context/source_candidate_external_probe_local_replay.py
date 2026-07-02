from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json
import os
import tempfile


_REPLAY_REPORT_SCHEMA = "missipy.source_candidate.external_probe_local_replay_report.v1"
_AUDIT_EVENT_SCHEMA = "missipy.source_candidate.external_probe_local_audit_event.v1"


@dataclass(frozen=True)
class SourceCandidateExternalProbeLocalReplayItem:
    event_id: str
    created_at: str
    summary_path: str
    status: str
    ready_count: int
    check_count: int
    blocked_count: int
    reason: str

    def to_json_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "created_at": self.created_at,
            "summary_path": self.summary_path,
            "status": self.status,
            "ready_count": self.ready_count,
            "check_count": self.check_count,
            "blocked_count": self.blocked_count,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SourceCandidateExternalProbeLocalReplayReport:
    audit_log_path: Path
    event_count: int
    replayed_count: int
    ready_event_count: int
    check_event_count: int
    blocked_event_count: int
    latest_event_id: str | None
    items: tuple[SourceCandidateExternalProbeLocalReplayItem, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _REPLAY_REPORT_SCHEMA,
            "audit_log_path": str(self.audit_log_path),
            "event_count": self.event_count,
            "replayed_count": self.replayed_count,
            "ready_event_count": self.ready_event_count,
            "check_event_count": self.check_event_count,
            "blocked_event_count": self.blocked_event_count,
            "latest_event_id": self.latest_event_id,
            "items": [item.to_json_dict() for item in self.items],
        }


def build_source_candidate_external_probe_local_replay_report(
    audit_log_path: Path,
    *,
    limit: int | None = None,
) -> SourceCandidateExternalProbeLocalReplayReport:
    events = read_source_candidate_external_probe_local_replay_events(audit_log_path)
    selected = events[-limit:] if limit is not None and limit >= 0 else events
    items = tuple(_item_from_event(event) for event in selected)
    latest_event_id = _string(events[-1].get("event_id"), default=None) if events else None

    return SourceCandidateExternalProbeLocalReplayReport(
        audit_log_path=audit_log_path,
        event_count=len(events),
        replayed_count=len(items),
        ready_event_count=sum(1 for item in items if item.status == "ready"),
        check_event_count=sum(1 for item in items if item.status == "check"),
        blocked_event_count=sum(1 for item in items if item.status == "blocked"),
        latest_event_id=latest_event_id,
        items=items,
    )


def read_source_candidate_external_probe_local_replay_events(
    audit_log_path: Path,
) -> tuple[dict[str, Any], ...]:
    if not audit_log_path.exists():
        return ()

    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(audit_log_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, Mapping):
            raise ValueError(f"audit replay line {line_number} must be a JSON object")
        if payload.get("schema") != _AUDIT_EVENT_SCHEMA:
            raise ValueError(f"audit replay line {line_number} schema mismatch")
        events.append(dict(payload))
    return tuple(events)


def write_source_candidate_external_probe_local_replay_report(
    path: Path,
    report: SourceCandidateExternalProbeLocalReplayReport,
) -> Path:
    _atomic_write_json(path, report.to_json_dict())
    return path


def read_source_candidate_external_probe_local_replay_report(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    if payload.get("schema") != _REPLAY_REPORT_SCHEMA:
        raise ValueError("external probe local replay report schema mismatch")
    return dict(payload)


def render_source_candidate_external_probe_local_replay_report(
    report: SourceCandidateExternalProbeLocalReplayReport,
) -> str:
    lines = [
        "external probe local replay",
        f"audit_log_path: {report.audit_log_path}",
        f"event_count: {report.event_count}",
        f"replayed_count: {report.replayed_count}",
        f"ready_event_count: {report.ready_event_count}",
        f"check_event_count: {report.check_event_count}",
        f"blocked_event_count: {report.blocked_event_count}",
        f"latest_event_id: {report.latest_event_id or '<none>'}",
    ]
    for item in report.items:
        lines.append(
            f"- {item.status}: {item.created_at} {item.event_id} "
            f"ready={item.ready_count} check={item.check_count} blocked={item.blocked_count} "
            f"reason={item.reason}"
        )
    return "\n".join(lines)


def _item_from_event(event: Mapping[str, Any]) -> SourceCandidateExternalProbeLocalReplayItem:
    ready_count = _int(event.get("ready_count"))
    check_count = _int(event.get("check_count"))
    blocked_count = _int(event.get("blocked_count"))
    status, reason = _status_and_reason(
        ready_count=ready_count,
        check_count=check_count,
        blocked_count=blocked_count,
    )

    return SourceCandidateExternalProbeLocalReplayItem(
        event_id=_string(event.get("event_id"), default="<unknown>") or "<unknown>",
        created_at=_string(event.get("created_at"), default="<unknown>") or "<unknown>",
        summary_path=_string(event.get("summary_path"), default="<unknown>") or "<unknown>",
        status=status,
        ready_count=ready_count,
        check_count=check_count,
        blocked_count=blocked_count,
        reason=reason,
    )


def _status_and_reason(
    *,
    ready_count: int,
    check_count: int,
    blocked_count: int,
) -> tuple[str, str]:
    if blocked_count > 0:
        return "blocked", "one or more bundles were blocked"
    if check_count > 0:
        return "check", "one or more bundles require operator review"
    if ready_count > 0:
        return "ready", "all replayed bundles are ready"
    return "check", "no ready bundle was recorded"


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _string(raw: object, *, default: str | None) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw
    return default


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
