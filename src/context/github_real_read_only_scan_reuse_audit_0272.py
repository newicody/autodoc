"""Pure reuse audit for a future real read-only GitHub issue scan.

0272-r1 performs source inspection only.  It never imports or calls a GitHub
client, reads no token value, performs no network request and cannot mutate a
remote repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

AUDIT_SCHEMA = "missipy.github.real_read_only_scan_reuse_audit.v1"


@dataclass(frozen=True, slots=True)
class GitHubReadOnlyScanAuditCommand:
    repo_root: Path
    max_files: int = 500

    def __post_init__(self) -> None:
        if self.max_files <= 0:
            raise ValueError("max_files must be > 0")


@dataclass(frozen=True, slots=True)
class GitHubReadOnlyScanAuditPolicy:
    required_surfaces: tuple[str, ...] = (
        "tools/run_github_actions_artifact_fetch_once.py",
        "src/context/github_artifact_server_fetch_config.py",
        "src/context/github_scan_once_handoff_0267.py",
        "src/context/source_candidate_github_adapter.py",
        "src/context/source_candidate_remote_mutation_gate.py",
    )
    forbidden_mutation_signatures: tuple[str, ...] = (
        "create_" + "issue(",
        "update_" + "issue(",
        "create_" + "pull(",
        "merge(",
        "git push",
    )


@dataclass(frozen=True, slots=True)
class GitHubReuseFinding:
    surface: str
    present: bool
    role: str
    evidence: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "present": self.present,
            "role": self.role,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class GitHubReadOnlyScanReuseAuditResult:
    valid: bool
    issues: tuple[str, ...]
    scanned_files: int
    findings: tuple[GitHubReuseFinding, ...]
    actions_read_only_client_found: bool
    issue_read_only_client_found: bool
    token_env_policy_found: bool
    repository_allowlist_found: bool
    local_handoff_found: bool
    remote_mutation_gate_found: bool
    network_used: bool = False
    remote_mutation_performed: bool = False
    implementation_needed: bool = True
    new_shared_read_only_io_module_justified: bool = True
    next_patch: str = "0272-r2-github_read_only_issue_scan_client"
    boundaries: Mapping[str, bool] = field(
        default_factory=lambda: {
            "local_authority": True,
            "github_review_surface_only": True,
            "remote_mutation_allowed": False,
            "scheduler_modified": False,
            "polling_loop_added": False,
        }
    )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": AUDIT_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "scanned_files": self.scanned_files,
            "findings": [finding.to_json_dict() for finding in self.findings],
            "actions_read_only_client_found": self.actions_read_only_client_found,
            "issue_read_only_client_found": self.issue_read_only_client_found,
            "token_env_policy_found": self.token_env_policy_found,
            "repository_allowlist_found": self.repository_allowlist_found,
            "local_handoff_found": self.local_handoff_found,
            "remote_mutation_gate_found": self.remote_mutation_gate_found,
            "network_used": self.network_used,
            "remote_mutation_performed": self.remote_mutation_performed,
            "implementation_needed": self.implementation_needed,
            "new_shared_read_only_io_module_justified": self.new_shared_read_only_io_module_justified,
            "next": self.next_patch,
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"github_real_read_only_scan_reuse_audit_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"scanned_files={self.scanned_files}",
                f"actions_read_only_client_found={self.actions_read_only_client_found}",
                f"issue_read_only_client_found={self.issue_read_only_client_found}",
                f"implementation_needed={self.implementation_needed}",
                "remote_mutation_allowed=False",
                f"next={self.next_patch}",
            )
        )


def audit_github_real_read_only_scan_reuse(
    command: GitHubReadOnlyScanAuditCommand,
    policy: GitHubReadOnlyScanAuditPolicy | None = None,
) -> GitHubReadOnlyScanReuseAuditResult:
    policy = policy or GitHubReadOnlyScanAuditPolicy()
    root = command.repo_root.resolve()
    issues: list[str] = []
    findings: list[GitHubReuseFinding] = []

    texts: dict[str, str] = {}
    scanned_files = 0
    for relative in policy.required_surfaces:
        path = root / relative
        present = path.is_file()
        text = path.read_text(encoding="utf-8") if present else ""
        texts[relative] = text
        scanned_files += int(present)
        if not present:
            issues.append(f"required surface missing: {relative}")
        findings.append(
            GitHubReuseFinding(
                surface=relative,
                present=present,
                role=_role_for(relative),
                evidence=_evidence_for(relative, text),
            )
        )

    if scanned_files > command.max_files:
        issues.append("scan exceeded max_files")

    actions_text = texts.get("tools/run_github_actions_artifact_fetch_once.py", "")
    config_text = texts.get("src/context/github_artifact_server_fetch_config.py", "")
    handoff_text = texts.get("src/context/github_scan_once_handoff_0267.py", "")
    adapter_text = texts.get("src/context/source_candidate_github_adapter.py", "")
    gate_text = texts.get("src/context/source_candidate_remote_mutation_gate.py", "")
    combined = "\n".join(texts.values())

    actions_read_only_client_found = all(
        marker in actions_text
        for marker in (
            "class GitHubActionsClient",
            "def _get_json",
            "def _get_bytes",
            "no remote mutation",
        )
    )
    issue_read_only_client_found = any(
        marker in combined
        for marker in (
            "class GitHubIssuesReadOnlyClient",
            "def list_repository_issues",
            "def list_issues_read_only",
        )
    )
    token_env_policy_found = all(
        marker in config_text for marker in ("token_env", "_looks_like_secret_value")
    )
    repository_allowlist_found = "allowed_repositories" in config_text
    local_handoff_found = all(
        marker in handoff_text
        for marker in ("HANDOFF_SCHEMA", "remote_mutation_allowed", "scan_once")
    )
    remote_mutation_gate_found = (
        "SourceCandidateRemoteMutationGatePolicy" in adapter_text
        and "run_source_candidate_remote_mutation_gate" in adapter_text
        and bool(gate_text)
    )

    if not actions_read_only_client_found:
        issues.append("existing GitHub Actions read-only client not detected")
    if not token_env_policy_found:
        issues.append("token_env safety policy not detected")
    if not repository_allowlist_found:
        issues.append("repository allow-list not detected")
    if not local_handoff_found:
        issues.append("0267 local handoff not detected")
    if not remote_mutation_gate_found:
        issues.append("remote mutation gate not detected")

    mutation_signatures = tuple(
        signature
        for signature in policy.forbidden_mutation_signatures
        if signature in actions_text
    )
    if mutation_signatures:
        issues.append(
            "read-only Actions client contains mutation signatures: "
            + ",".join(mutation_signatures)
        )

    return GitHubReadOnlyScanReuseAuditResult(
        valid=not issues,
        issues=tuple(issues),
        scanned_files=scanned_files,
        findings=tuple(findings),
        actions_read_only_client_found=actions_read_only_client_found,
        issue_read_only_client_found=issue_read_only_client_found,
        token_env_policy_found=token_env_policy_found,
        repository_allowlist_found=repository_allowlist_found,
        local_handoff_found=local_handoff_found,
        remote_mutation_gate_found=remote_mutation_gate_found,
        implementation_needed=not issue_read_only_client_found,
        new_shared_read_only_io_module_justified=not issue_read_only_client_found,
    )


def _role_for(relative: str) -> str:
    roles = {
        "tools/run_github_actions_artifact_fetch_once.py": "existing read-only GitHub Actions HTTP transport",
        "src/context/github_artifact_server_fetch_config.py": "token-env and repository allow-list policy",
        "src/context/github_scan_once_handoff_0267.py": "local scan-once handoff contract",
        "src/context/source_candidate_github_adapter.py": "fake-only mutation-facing adapter contract",
        "src/context/source_candidate_remote_mutation_gate.py": "explicit remote mutation gate",
    }
    return roles[relative]


def _evidence_for(relative: str, text: str) -> tuple[str, ...]:
    candidates = {
        "tools/run_github_actions_artifact_fetch_once.py": (
            "class GitHubActionsClient",
            "def _get_json",
            "no remote mutation",
        ),
        "src/context/github_artifact_server_fetch_config.py": (
            "token_env",
            "allowed_repositories",
            "allow_remote_mutation",
        ),
        "src/context/github_scan_once_handoff_0267.py": (
            "HANDOFF_SCHEMA",
            "scan_once",
            "remote_mutation_allowed",
        ),
        "src/context/source_candidate_github_adapter.py": (
            "FakeSourceCandidateGithubProjectionAdapter",
            "SourceCandidateRemoteMutationGatePolicy",
        ),
        "src/context/source_candidate_remote_mutation_gate.py": (
            "SourceCandidateRemoteMutationGatePolicy",
            "mutation_allowed",
        ),
    }
    return tuple(marker for marker in candidates[relative] if marker in text)
