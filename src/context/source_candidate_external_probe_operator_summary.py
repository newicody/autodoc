from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import os
import tempfile


_SUMMARY_SCHEMA = "missipy.source_candidate.external_probe_operator_summary.v1"
_INDEX_SCHEMA = "missipy.source_candidate.external_probe_artifact_index.v1"


@dataclass(frozen=True)
class SourceCandidateExternalProbeOperatorSummaryItem:
    repository: str
    bundle_path: str
    status: str
    read_only: bool
    external_call_performed: bool
    probe_allowed: bool
    artifact_count: int
    byte_count: int
    reason: str

    def to_json_dict(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "bundle_path": self.bundle_path,
            "status": self.status,
            "read_only": self.read_only,
            "external_call_performed": self.external_call_performed,
            "probe_allowed": self.probe_allowed,
            "artifact_count": self.artifact_count,
            "byte_count": self.byte_count,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SourceCandidateExternalProbeOperatorSummary:
    index_path: Path | None
    bundle_count: int
    ready_count: int
    check_count: int
    blocked_count: int
    total_artifact_count: int
    total_byte_count: int
    items: tuple[SourceCandidateExternalProbeOperatorSummaryItem, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _SUMMARY_SCHEMA,
            "index_path": str(self.index_path) if self.index_path is not None else None,
            "bundle_count": self.bundle_count,
            "ready_count": self.ready_count,
            "check_count": self.check_count,
            "blocked_count": self.blocked_count,
            "total_artifact_count": self.total_artifact_count,
            "total_byte_count": self.total_byte_count,
            "items": [item.to_json_dict() for item in self.items],
        }


def build_source_candidate_external_probe_operator_summary_from_index_payload(
    payload: Mapping[str, Any],
    *,
    index_path: Path | None = None,
) -> SourceCandidateExternalProbeOperatorSummary:
    if payload.get("schema") != _INDEX_SCHEMA:
        raise ValueError("external probe artifact index schema mismatch")

    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, Sequence) or isinstance(raw_entries, (str, bytes, bytearray)):
        raise ValueError("external probe artifact index entries must be a list")

    items = tuple(_item_from_index_entry(entry) for entry in raw_entries if isinstance(entry, Mapping))

    return SourceCandidateExternalProbeOperatorSummary(
        index_path=index_path,
        bundle_count=len(items),
        ready_count=sum(1 for item in items if item.status == "ready"),
        check_count=sum(1 for item in items if item.status == "check"),
        blocked_count=sum(1 for item in items if item.status == "blocked"),
        total_artifact_count=sum(item.artifact_count for item in items),
        total_byte_count=sum(item.byte_count for item in items),
        items=items,
    )


def build_source_candidate_external_probe_operator_summary_from_index_file(
    index_path: Path,
) -> SourceCandidateExternalProbeOperatorSummary:
    return build_source_candidate_external_probe_operator_summary_from_index_payload(
        _read_json_object(index_path),
        index_path=index_path,
    )


def write_source_candidate_external_probe_operator_summary(
    path: Path,
    summary: SourceCandidateExternalProbeOperatorSummary,
) -> Path:
    _atomic_write_json(path, summary.to_json_dict())
    return path


def read_source_candidate_external_probe_operator_summary(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    if payload.get("schema") != _SUMMARY_SCHEMA:
        raise ValueError("external probe operator summary schema mismatch")
    return dict(payload)


def render_source_candidate_external_probe_operator_summary(
    summary: SourceCandidateExternalProbeOperatorSummary,
) -> str:
    lines = [
        "external probe operator summary",
        f"index_path: {summary.index_path or '<memory>'}",
        f"bundle_count: {summary.bundle_count}",
        f"ready_count: {summary.ready_count}",
        f"check_count: {summary.check_count}",
        f"blocked_count: {summary.blocked_count}",
        f"total_artifact_count: {summary.total_artifact_count}",
        f"total_byte_count: {summary.total_byte_count}",
    ]
    for item in summary.items:
        lines.append(
            f"- {item.status}: {item.repository} "
            f"{item.bundle_path} artifacts={item.artifact_count} bytes={item.byte_count} "
            f"reason={item.reason}"
        )
    return "\n".join(lines)


def _item_from_index_entry(entry: Mapping[str, Any]) -> SourceCandidateExternalProbeOperatorSummaryItem:
    read_only = bool(entry.get("read_only"))
    external_call_performed = bool(entry.get("external_call_performed"))
    probe_allowed = bool(entry.get("probe_allowed"))
    status, reason = _status_and_reason(
        read_only=read_only,
        external_call_performed=external_call_performed,
        probe_allowed=probe_allowed,
    )

    return SourceCandidateExternalProbeOperatorSummaryItem(
        repository=_string(entry.get("repository"), default="<unknown>"),
        bundle_path=_string(entry.get("bundle_path"), default="<unknown>"),
        status=status,
        read_only=read_only,
        external_call_performed=external_call_performed,
        probe_allowed=probe_allowed,
        artifact_count=_int(entry.get("artifact_count")),
        byte_count=_int(entry.get("byte_count")),
        reason=reason,
    )


def _status_and_reason(
    *,
    read_only: bool,
    external_call_performed: bool,
    probe_allowed: bool,
) -> tuple[str, str]:
    if external_call_performed:
        return "blocked", "external call was already performed"
    if not read_only:
        return "blocked", "bundle is not marked read-only"
    if not probe_allowed:
        return "check", "probe was not allowed"
    return "ready", "read-only probe bundle is ready for operator review"


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _string(raw: object, *, default: str) -> str:
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
