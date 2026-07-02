from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json
import os
import tempfile


_AUDIT_SCHEMA = "missipy.source_candidate.phase6_closure_audit.v1"
_HANDOFF_SCHEMA = "missipy.source_candidate.projection_handoff_dry_run.v1"
_PREVIEW_SCHEMA = "missipy.source_candidate.projection_preview.v1"
_GATE_REPORT_SCHEMA = "missipy.source_candidate.projection_gate_report.v1"


@dataclass(frozen=True)
class SourceCandidatePhase6ClosureAuditIssue:
    severity: str
    code: str
    message: str

    def to_json_dict(self) -> dict[str, object]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }


@dataclass(frozen=True)
class SourceCandidatePhase6ClosureAudit:
    handoff_path: Path
    output_path: Path | None
    passed: bool
    handoff_passed: bool
    item_count: int
    artifact_count: int
    byte_count: int
    issue_count: int
    issues: tuple[SourceCandidatePhase6ClosureAuditIssue, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _AUDIT_SCHEMA,
            "handoff_path": str(self.handoff_path),
            "output_path": str(self.output_path) if self.output_path is not None else None,
            "passed": self.passed,
            "handoff_passed": self.handoff_passed,
            "item_count": self.item_count,
            "artifact_count": self.artifact_count,
            "byte_count": self.byte_count,
            "issue_count": self.issue_count,
            "issues": [issue.to_json_dict() for issue in self.issues],
        }


def build_source_candidate_phase6_closure_audit(
    handoff_path: Path,
    *,
    output_path: Path | None = None,
) -> SourceCandidatePhase6ClosureAudit:
    """Build a local closure audit for the SourceCandidate Phase 6 chain."""

    issues: list[SourceCandidatePhase6ClosureAuditIssue] = []
    manifest_path = handoff_path / "handoff_manifest.json"
    preview_path = handoff_path / "projection_preview.json"
    gate_report_path = handoff_path / "projection_gate_report.json"

    manifest = _read_json_object(manifest_path, issues, "handoff_manifest")
    preview = _read_json_object(preview_path, issues, "projection_preview")
    gate_report = _read_json_object(gate_report_path, issues, "projection_gate_report")

    _expect_schema(manifest, _HANDOFF_SCHEMA, issues, "handoff_manifest")
    _expect_schema(preview, _PREVIEW_SCHEMA, issues, "projection_preview")
    _expect_schema(gate_report, _GATE_REPORT_SCHEMA, issues, "projection_gate_report")

    handoff_passed = bool(manifest.get("passed")) and bool(
        _mapping(gate_report.get("gate_result")).get("passed")
    )

    item_count = _non_negative_int(manifest.get("item_count"))
    preview_item_count = _non_negative_int(preview.get("item_count"))
    if item_count != preview_item_count:
        issues.append(
            _error(
                "item_count_mismatch",
                "handoff manifest item_count does not match projection preview item_count",
            )
        )

    raw_artifacts = manifest.get("artifacts")
    artifact_count = len(raw_artifacts) if isinstance(raw_artifacts, list) else 0
    if not isinstance(raw_artifacts, list):
        issues.append(_error("artifacts_missing", "handoff manifest artifacts must be a list"))

    byte_count = sum(_existing_size(path) for path in (manifest_path, preview_path, gate_report_path))

    passed = handoff_passed and not any(issue.severity == "error" for issue in issues)
    return SourceCandidatePhase6ClosureAudit(
        handoff_path=handoff_path,
        output_path=output_path,
        passed=passed,
        handoff_passed=handoff_passed,
        item_count=max(item_count, 0),
        artifact_count=artifact_count,
        byte_count=byte_count,
        issue_count=len(issues),
        issues=tuple(issues),
    )


def write_source_candidate_phase6_closure_audit(
    handoff_path: Path,
    output_path: Path,
) -> SourceCandidatePhase6ClosureAudit:
    """Write the local Phase 6 closure audit JSON atomically."""

    audit = build_source_candidate_phase6_closure_audit(
        handoff_path,
        output_path=output_path,
    )
    _atomic_write_json(output_path, audit.to_json_dict())
    return audit


def render_source_candidate_phase6_closure_audit(
    audit: SourceCandidatePhase6ClosureAudit,
) -> str:
    status = "PASS" if audit.passed else "FAIL"
    lines = [
        f"phase 6 closure audit: {status}",
        f"handoff: {audit.handoff_path}",
        f"items: {audit.item_count}",
        f"artifacts: {audit.artifact_count}",
        f"issues: {audit.issue_count}",
    ]
    for issue in audit.issues:
        lines.append(f"- {issue.severity}:{issue.code}: {issue.message}")
    return "\n".join(lines)


def _read_json_object(
    path: Path,
    issues: list[SourceCandidatePhase6ClosureAuditIssue],
    role: str,
) -> Mapping[str, Any]:
    if not path.exists():
        issues.append(_error(f"{role}_missing", f"{role} file is missing: {path}"))
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(_error(f"{role}_invalid_json", f"{role} file is invalid JSON: {exc}"))
        return {}
    if not isinstance(payload, Mapping):
        issues.append(_error(f"{role}_not_object", f"{role} payload must be an object"))
        return {}
    return payload


def _expect_schema(
    payload: Mapping[str, Any],
    expected: str,
    issues: list[SourceCandidatePhase6ClosureAuditIssue],
    role: str,
) -> None:
    if payload.get("schema") != expected:
        issues.append(_error(f"{role}_schema", f"{role} schema mismatch"))


def _mapping(raw: object) -> Mapping[str, Any]:
    return raw if isinstance(raw, Mapping) else {}


def _non_negative_int(raw: object) -> int:
    return raw if isinstance(raw, int) and raw >= 0 else -1


def _existing_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def _error(code: str, message: str) -> SourceCandidatePhase6ClosureAuditIssue:
    return SourceCandidatePhase6ClosureAuditIssue(
        severity="error",
        code=code,
        message=message,
    )


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
