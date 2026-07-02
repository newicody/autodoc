from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import os
import tempfile


_PREVIEW_SCHEMA = "missipy.source_candidate.projection_preview.v1"


@dataclass(frozen=True)
class SourceCandidateProjectionPreviewPolicy:
    """Local policy for building an operator projection preview.

    The preview is only a local artifact. It does not contact any external
    tracker and it does not mutate the SourceCandidate store.
    """

    target_name: str = "operator_project_surface"
    max_items: int = 50
    include_terminal: bool = False


@dataclass(frozen=True)
class SourceCandidateProjectionPreviewItem:
    candidate_id: str
    title: str
    status: str
    decision_action: str | None
    decision_reason: str | None
    target_context_id: str | None
    audit_present: bool
    recommended_action: str
    labels: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "title": self.title,
            "status": self.status,
            "decision_action": self.decision_action,
            "decision_reason": self.decision_reason,
            "target_context_id": self.target_context_id,
            "audit_present": self.audit_present,
            "recommended_action": self.recommended_action,
            "labels": list(self.labels),
        }


@dataclass(frozen=True)
class SourceCandidateProjectionPreview:
    target_name: str
    source_report_schema: str
    item_count: int
    items: tuple[SourceCandidateProjectionPreviewItem, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _PREVIEW_SCHEMA,
            "target_name": self.target_name,
            "source_report_schema": self.source_report_schema,
            "item_count": self.item_count,
            "items": [item.to_json_dict() for item in self.items],
        }


def build_source_candidate_projection_preview(
    report_payload: Mapping[str, Any],
    policy: SourceCandidateProjectionPreviewPolicy | None = None,
) -> SourceCandidateProjectionPreview:
    """Build a stable local projection preview from an operator report payload."""

    active_policy = policy or SourceCandidateProjectionPreviewPolicy()
    if active_policy.max_items <= 0:
        raise ValueError("max_items must be greater than zero")
    if not active_policy.target_name.strip():
        raise ValueError("target_name must not be empty")

    raw_items = _coerce_items(report_payload.get("items", ()))
    preview_items: list[SourceCandidateProjectionPreviewItem] = []

    for raw in raw_items:
        item = _build_item(raw)
        if not active_policy.include_terminal and _is_terminal_status(item.status):
            continue
        preview_items.append(item)
        if len(preview_items) >= active_policy.max_items:
            break

    return SourceCandidateProjectionPreview(
        target_name=active_policy.target_name,
        source_report_schema=str(report_payload.get("schema", "unknown")),
        item_count=len(preview_items),
        items=tuple(preview_items),
    )


def write_source_candidate_projection_preview(
    path: Path,
    preview: SourceCandidateProjectionPreview,
) -> Path:
    """Write a projection preview JSON artifact atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(preview.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        tmp_name = handle.name
        handle.write(payload)

    os.replace(tmp_name, path)
    return path


def read_operator_report(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("operator report must be a JSON object")
    return payload


def _coerce_items(raw: object) -> tuple[Mapping[str, Any], ...]:
    if raw is None:
        return ()
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise ValueError("operator report items must be a list")
    items: list[Mapping[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError("operator report item must be an object")
        items.append(item)
    return tuple(items)


def _build_item(raw: Mapping[str, Any]) -> SourceCandidateProjectionPreviewItem:
    decision = _mapping(raw.get("decision_summary"))
    audit = _mapping(raw.get("audit_summary"))

    candidate_id = _string_value(raw, "candidate_id", "id")
    title = _string_value(raw, "title", default=candidate_id)
    status = _string_value(raw, "status", default="unknown")

    decision_action = _optional_string(decision.get("action") or raw.get("decision_action"))
    decision_reason = _optional_string(decision.get("reason") or raw.get("decision_reason"))
    target_context_id = _optional_string(
        decision.get("target_context_id") or raw.get("target_context_id")
    )
    audit_present = bool(raw.get("audit_present") or audit.get("present"))

    recommended_action = _recommended_action(
        status=status,
        decision_action=decision_action,
        audit_present=audit_present,
    )

    return SourceCandidateProjectionPreviewItem(
        candidate_id=candidate_id,
        title=title,
        status=status,
        decision_action=decision_action,
        decision_reason=decision_reason,
        target_context_id=target_context_id,
        audit_present=audit_present,
        recommended_action=recommended_action,
        labels=_labels(status, decision_action, audit_present),
    )


def _mapping(raw: object) -> Mapping[str, Any]:
    return raw if isinstance(raw, Mapping) else {}


def _string_value(raw: Mapping[str, Any], *keys: str, default: str | None = None) -> str:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value
    if default is not None:
        return default
    raise ValueError(f"missing string field: {'/'.join(keys)}")


def _optional_string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _is_terminal_status(status: str) -> bool:
    return status in {"archived", "merged", "promoted", "rejected"}


def _recommended_action(status: str, decision_action: str | None, audit_present: bool) -> str:
    if _is_terminal_status(status):
        return "none"
    if decision_action == "relaunch":
        return "relaunch"
    if decision_action in {"promote", "merge"} and not audit_present:
        return "write-audit"
    if status in {"new", "analyzed"}:
        return "inspect"
    return "review"


def _labels(status: str, decision_action: str | None, audit_present: bool) -> tuple[str, ...]:
    labels = [f"status:{status}"]
    if decision_action:
        labels.append(f"decision:{decision_action}")
    labels.append("audit:present" if audit_present else "audit:missing")
    return tuple(labels)
