from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence
import json
import os
import tempfile


_PROBE_REQUEST_SCHEMA = "missipy.source_candidate.read_only_external_probe_request.v1"
_PROBE_RESULT_SCHEMA = "missipy.source_candidate.read_only_external_probe_result.v1"
_OPERATOR_REVIEW_SCHEMA = "missipy.source_candidate.operator_external_review_report.v1"


@dataclass(frozen=True)
class SourceCandidateReadOnlyExternalProbeRequest:
    target_kind: str
    repository: str
    dry_run: bool
    requested_checks: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _PROBE_REQUEST_SCHEMA,
            "target_kind": self.target_kind,
            "repository": self.repository,
            "dry_run": self.dry_run,
            "requested_checks": list(self.requested_checks),
        }


@dataclass(frozen=True)
class SourceCandidateReadOnlyExternalProbeFinding:
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
class SourceCandidateReadOnlyExternalProbeResult:
    target_kind: str
    repository: str
    read_only: bool
    external_call_performed: bool
    probe_allowed: bool
    check_count: int
    finding_count: int
    findings: tuple[SourceCandidateReadOnlyExternalProbeFinding, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _PROBE_RESULT_SCHEMA,
            "target_kind": self.target_kind,
            "repository": self.repository,
            "read_only": self.read_only,
            "external_call_performed": self.external_call_performed,
            "probe_allowed": self.probe_allowed,
            "check_count": self.check_count,
            "finding_count": self.finding_count,
            "findings": [finding.to_json_dict() for finding in self.findings],
        }


class SourceCandidateReadOnlyExternalProbeAdapter(Protocol):
    """Interface for read-only external probing.

    Phase 7.9 only provides a fake local implementation. A future real adapter
    must preserve read-only behavior and must never perform mutation.
    """

    def probe(
        self,
        request: SourceCandidateReadOnlyExternalProbeRequest,
    ) -> SourceCandidateReadOnlyExternalProbeResult:
        ...


@dataclass(frozen=True)
class FakeSourceCandidateReadOnlyExternalProbeAdapter:
    """Fake external probe adapter for local tests and operator review."""

    available_repositories: tuple[str, ...] = ()
    supported_checks: tuple[str, ...] = (
        "repository_visible",
        "project_surface_visible",
        "write_access_not_required",
    )

    def probe(
        self,
        request: SourceCandidateReadOnlyExternalProbeRequest,
    ) -> SourceCandidateReadOnlyExternalProbeResult:
        findings: list[SourceCandidateReadOnlyExternalProbeFinding] = []

        if not request.dry_run:
            findings.append(_error("not_dry_run", "probe request must remain dry-run"))

        if request.repository not in self.available_repositories:
            findings.append(
                _warning("repository_not_confirmed", f"repository not confirmed locally: {request.repository}")
            )

        for check in request.requested_checks:
            if check not in self.supported_checks:
                findings.append(_warning("unsupported_check", f"unsupported read-only check: {check}"))

        return SourceCandidateReadOnlyExternalProbeResult(
            target_kind=request.target_kind,
            repository=request.repository,
            read_only=True,
            external_call_performed=False,
            probe_allowed=not any(finding.severity == "error" for finding in findings),
            check_count=len(request.requested_checks),
            finding_count=len(findings),
            findings=tuple(findings),
        )


def build_source_candidate_read_only_external_probe_request_from_operator_report(
    report_payload: Mapping[str, Any],
    *,
    requested_checks: Sequence[str] | None = None,
) -> SourceCandidateReadOnlyExternalProbeRequest:
    """Build a read-only probe request from an operator external review report."""

    if report_payload.get("schema") != _OPERATOR_REVIEW_SCHEMA:
        raise ValueError("operator external review report schema mismatch")

    repository = _string(report_payload.get("repository"))
    dry_run = bool(report_payload.get("dry_run"))
    recommended_action = _string(report_payload.get("recommended_action"), default="fix_errors")

    checks = tuple(requested_checks) if requested_checks is not None else (
        "repository_visible",
        "project_surface_visible",
        "write_access_not_required",
    )

    if recommended_action not in {"operator_review", "review_gate_blockers"}:
        raise ValueError("operator review report is not ready for read-only probe")

    return SourceCandidateReadOnlyExternalProbeRequest(
        target_kind="github_project_surface",
        repository=repository,
        dry_run=dry_run,
        requested_checks=tuple(_string(check) for check in checks),
    )


def build_source_candidate_read_only_external_probe_request_from_file(
    report_path: Path,
    *,
    requested_checks: Sequence[str] | None = None,
) -> SourceCandidateReadOnlyExternalProbeRequest:
    return build_source_candidate_read_only_external_probe_request_from_operator_report(
        _read_json_object(report_path),
        requested_checks=requested_checks,
    )


def write_source_candidate_read_only_external_probe_request(
    path: Path,
    request: SourceCandidateReadOnlyExternalProbeRequest,
) -> Path:
    _atomic_write_json(path, request.to_json_dict())
    return path


def write_source_candidate_read_only_external_probe_result(
    path: Path,
    result: SourceCandidateReadOnlyExternalProbeResult,
) -> Path:
    _atomic_write_json(path, result.to_json_dict())
    return path


def read_source_candidate_read_only_external_probe_result(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    if payload.get("schema") != _PROBE_RESULT_SCHEMA:
        raise ValueError("read-only external probe result schema mismatch")
    return dict(payload)


def render_source_candidate_read_only_external_probe_result(
    result: SourceCandidateReadOnlyExternalProbeResult,
) -> str:
    status = "PASS" if result.probe_allowed else "FAIL"
    lines = [
        f"read-only external probe: {status}",
        f"target: {result.target_kind}",
        f"repository: {result.repository}",
        f"read_only: {result.read_only}",
        f"external_call_performed: {result.external_call_performed}",
        f"checks: {result.check_count}",
        f"findings: {result.finding_count}",
    ]
    for finding in result.findings:
        lines.append(f"- {finding.severity}:{finding.code}: {finding.message}")
    return "\n".join(lines)


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _string(raw: object, *, default: str | None = None) -> str:
    if isinstance(raw, str) and raw.strip():
        return raw
    if default is not None:
        return default
    raise ValueError("expected non-empty string")


def _error(code: str, message: str) -> SourceCandidateReadOnlyExternalProbeFinding:
    return SourceCandidateReadOnlyExternalProbeFinding(
        severity="error",
        code=code,
        message=message,
    )


def _warning(code: str, message: str) -> SourceCandidateReadOnlyExternalProbeFinding:
    return SourceCandidateReadOnlyExternalProbeFinding(
        severity="warning",
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
