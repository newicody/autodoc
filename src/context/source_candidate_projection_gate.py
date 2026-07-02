from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json


_BUNDLE_SCHEMA = "missipy.source_candidate.projection_bundle.v1"
_PREVIEW_SCHEMA = "missipy.source_candidate.projection_preview.v1"
_GATE_SCHEMA = "missipy.source_candidate.projection_gate.v1"


@dataclass(frozen=True)
class SourceCandidateProjectionGatePolicy:
    """Local validation policy for projection bundles."""

    require_items: bool = False
    require_audit_present: bool = False


@dataclass(frozen=True)
class SourceCandidateProjectionGateIssue:
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
class SourceCandidateProjectionGateResult:
    bundle_path: Path
    manifest_path: Path
    preview_path: Path | None
    passed: bool
    item_count: int
    issue_count: int
    issues: tuple[SourceCandidateProjectionGateIssue, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _GATE_SCHEMA,
            "bundle_path": str(self.bundle_path),
            "manifest_path": str(self.manifest_path),
            "preview_path": str(self.preview_path) if self.preview_path is not None else None,
            "passed": self.passed,
            "item_count": self.item_count,
            "issue_count": self.issue_count,
            "issues": [issue.to_json_dict() for issue in self.issues],
        }


def run_source_candidate_projection_gate(
    bundle_path: Path,
    policy: SourceCandidateProjectionGatePolicy | None = None,
) -> SourceCandidateProjectionGateResult:
    """Validate a local projection bundle before any external handoff."""

    active_policy = policy or SourceCandidateProjectionGatePolicy()
    manifest_path = bundle_path / "manifest.json"
    issues: list[SourceCandidateProjectionGateIssue] = []

    manifest = _read_json_object(manifest_path, issues, "manifest")
    preview_path = _preview_path_from_manifest(bundle_path, manifest, issues)

    preview: Mapping[str, Any] = {}
    if preview_path is not None:
        preview = _read_json_object(preview_path, issues, "preview")

    item_count = _validate_payloads(
        manifest=manifest,
        preview=preview,
        policy=active_policy,
        issues=issues,
    )

    return SourceCandidateProjectionGateResult(
        bundle_path=bundle_path,
        manifest_path=manifest_path,
        preview_path=preview_path,
        passed=not any(issue.severity == "error" for issue in issues),
        item_count=item_count,
        issue_count=len(issues),
        issues=tuple(issues),
    )


def render_source_candidate_projection_gate(result: SourceCandidateProjectionGateResult) -> str:
    status = "PASS" if result.passed else "FAIL"
    lines = [
        f"projection gate: {status}",
        f"bundle: {result.bundle_path}",
        f"items: {result.item_count}",
        f"issues: {result.issue_count}",
    ]
    for issue in result.issues:
        lines.append(f"- {issue.severity}:{issue.code}: {issue.message}")
    return "\n".join(lines)


def _read_json_object(
    path: Path,
    issues: list[SourceCandidateProjectionGateIssue],
    role: str,
) -> Mapping[str, Any]:
    if not path.exists():
        issues.append(_error(f"{role}_missing", f"{role} file is missing: {path}"))
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(_error(f"{role}_invalid_json", f"{role} file is invalid JSON: {exc}"))
        return {}
    if not isinstance(parsed, Mapping):
        issues.append(_error(f"{role}_not_object", f"{role} JSON payload must be an object"))
        return {}
    return parsed


def _preview_path_from_manifest(
    bundle_path: Path,
    manifest: Mapping[str, Any],
    issues: list[SourceCandidateProjectionGateIssue],
) -> Path | None:
    raw = manifest.get("preview_path")
    if not isinstance(raw, str) or not raw.strip():
        issues.append(_error("preview_path_missing", "manifest preview_path is missing"))
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = bundle_path / path
    return path


def _validate_payloads(
    *,
    manifest: Mapping[str, Any],
    preview: Mapping[str, Any],
    policy: SourceCandidateProjectionGatePolicy,
    issues: list[SourceCandidateProjectionGateIssue],
) -> int:
    if manifest.get("schema") != _BUNDLE_SCHEMA:
        issues.append(_error("manifest_schema", "manifest schema is not projection_bundle.v1"))
    if preview.get("schema") != _PREVIEW_SCHEMA:
        issues.append(_error("preview_schema", "preview schema is not projection_preview.v1"))

    manifest_count = _int_value(manifest.get("item_count"))
    preview_count = _int_value(preview.get("item_count"))
    raw_items = preview.get("items")
    actual_count = len(raw_items) if isinstance(raw_items, list) else 0

    if not isinstance(raw_items, list):
        issues.append(_error("preview_items", "preview items must be a list"))
    if preview_count != actual_count:
        issues.append(_error("preview_item_count", "preview item_count does not match items length"))
    if manifest_count != preview_count:
        issues.append(_error("manifest_item_count", "manifest item_count does not match preview item_count"))

    if policy.require_items and actual_count <= 0:
        issues.append(_error("items_required", "at least one projection item is required"))

    if policy.require_audit_present and isinstance(raw_items, list):
        missing = [
            item.get("candidate_id", "<unknown>")
            for item in raw_items
            if isinstance(item, Mapping) and not bool(item.get("audit_present"))
        ]
        if missing:
            issues.append(
                _error(
                    "audit_required",
                    "audit is required for all projection items: " + ", ".join(map(str, missing)),
                )
            )

    return actual_count


def _int_value(raw: object) -> int:
    return raw if isinstance(raw, int) and raw >= 0 else -1


def _error(code: str, message: str) -> SourceCandidateProjectionGateIssue:
    return SourceCandidateProjectionGateIssue(severity="error", code=code, message=message)
