from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import os
import tempfile


_GATE_SCHEMA = "missipy.source_candidate.remote_mutation_gate.v1"
_GITHUB_PAYLOAD_SCHEMA = "missipy.source_candidate.github_projection_payload.v1"


@dataclass(frozen=True)
class SourceCandidateRemoteMutationGatePolicy:
    """Local policy for remote write eligibility.

    The default is intentionally closed. A future adapter must pass this gate
    before any remote write can be considered.
    """

    remote_mutation_enabled: bool = False
    operator_confirmed: bool = False
    allowed_repositories: tuple[str, ...] = ()
    require_projection_allowed: bool = True
    require_dry_run_payload: bool = True
    require_no_payload_remote_mutation: bool = True
    require_no_safety_flags: bool = False
    require_operations: bool = False


@dataclass(frozen=True)
class SourceCandidateRemoteMutationGateIssue:
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
class SourceCandidateRemoteMutationGateResult:
    target_kind: str
    repository: str | None
    mutation_allowed: bool
    operation_count: int
    issue_count: int
    issues: tuple[SourceCandidateRemoteMutationGateIssue, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _GATE_SCHEMA,
            "target_kind": self.target_kind,
            "repository": self.repository,
            "mutation_allowed": self.mutation_allowed,
            "operation_count": self.operation_count,
            "issue_count": self.issue_count,
            "issues": [issue.to_json_dict() for issue in self.issues],
        }


def run_source_candidate_remote_mutation_gate(
    payload: Mapping[str, Any],
    policy: SourceCandidateRemoteMutationGatePolicy | None = None,
) -> SourceCandidateRemoteMutationGateResult:
    """Validate local eligibility for a future remote write.

    This function does not call an external service. It only returns a local
    PASS/FAIL-style result for operator review.
    """

    active_policy = policy or SourceCandidateRemoteMutationGatePolicy()
    issues: list[SourceCandidateRemoteMutationGateIssue] = []

    if payload.get("schema") != _GITHUB_PAYLOAD_SCHEMA:
        issues.append(_error("payload_schema", "payload schema is not github_projection_payload.v1"))

    repository = _optional_string(payload.get("repository"))
    if repository is None:
        issues.append(_error("repository_missing", "payload repository is missing"))
    elif active_policy.allowed_repositories and repository not in active_policy.allowed_repositories:
        issues.append(_error("repository_not_allowed", f"repository is not allowed: {repository}"))
    elif not active_policy.allowed_repositories:
        issues.append(_error("repository_allowlist_missing", "repository allowlist is empty"))

    if not active_policy.remote_mutation_enabled:
        issues.append(_error("remote_mutation_disabled", "remote mutation is disabled by policy"))

    if not active_policy.operator_confirmed:
        issues.append(_error("operator_not_confirmed", "operator confirmation is required"))

    if active_policy.require_projection_allowed and not bool(payload.get("projection_allowed")):
        issues.append(_error("projection_blocked", "payload projection_allowed is false"))

    if active_policy.require_dry_run_payload and not bool(payload.get("dry_run")):
        issues.append(_error("dry_run_required", "payload dry_run must be true before apply review"))

    if active_policy.require_no_payload_remote_mutation and bool(payload.get("remote_mutation")):
        issues.append(_error("payload_remote_mutation_true", "payload remote_mutation must be false"))

    operations = _operations(payload, issues)
    if active_policy.require_operations and not operations:
        issues.append(_error("operations_required", "at least one operation is required"))

    safety_flags = _operation_safety_flags(operations)
    if active_policy.require_no_safety_flags and safety_flags:
        issues.append(
            _error(
                "safety_flags_present",
                "safety flags are present: " + ", ".join(sorted(safety_flags)),
            )
        )

    return SourceCandidateRemoteMutationGateResult(
        target_kind="github_projection_payload",
        repository=repository,
        mutation_allowed=not any(issue.severity == "error" for issue in issues),
        operation_count=len(operations),
        issue_count=len(issues),
        issues=tuple(issues),
    )


def run_source_candidate_remote_mutation_gate_from_file(
    payload_path: Path,
    policy: SourceCandidateRemoteMutationGatePolicy | None = None,
) -> SourceCandidateRemoteMutationGateResult:
    return run_source_candidate_remote_mutation_gate(_read_json_object(payload_path), policy)


def write_source_candidate_remote_mutation_gate_result(
    path: Path,
    result: SourceCandidateRemoteMutationGateResult,
) -> Path:
    _atomic_write_json(path, result.to_json_dict())
    return path


def render_source_candidate_remote_mutation_gate(
    result: SourceCandidateRemoteMutationGateResult,
) -> str:
    status = "PASS" if result.mutation_allowed else "FAIL"
    lines = [
        f"remote mutation gate: {status}",
        f"target: {result.target_kind}",
        f"repository: {result.repository or '<none>'}",
        f"operations: {result.operation_count}",
        f"issues: {result.issue_count}",
    ]
    for issue in result.issues:
        lines.append(f"- {issue.severity}:{issue.code}: {issue.message}")
    return "\n".join(lines)


def _operations(
    payload: Mapping[str, Any],
    issues: list[SourceCandidateRemoteMutationGateIssue],
) -> tuple[Mapping[str, Any], ...]:
    raw = payload.get("operations")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        issues.append(_error("operations_invalid", "payload operations must be a list"))
        return ()
    operations: list[Mapping[str, Any]] = []
    for operation in raw:
        if not isinstance(operation, Mapping):
            issues.append(_error("operation_invalid", "payload operation must be an object"))
            continue
        operations.append(operation)
    return tuple(operations)


def _operation_safety_flags(operations: tuple[Mapping[str, Any], ...]) -> set[str]:
    flags: set[str] = set()
    for operation in operations:
        raw = operation.get("safety_flags")
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
            for item in raw:
                if isinstance(item, str) and item.strip():
                    flags.add(item)
    return flags


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _optional_string(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw
    return None


def _error(code: str, message: str) -> SourceCandidateRemoteMutationGateIssue:
    return SourceCandidateRemoteMutationGateIssue(
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
