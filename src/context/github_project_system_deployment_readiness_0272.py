"""Pure contracts for GitHub ProjectV2 and Actions deployment readiness.

The CLI boundary performs filesystem and query-only GitHub reads.  This module
contains immutable configuration, workflow analysis and result closure only.
It never installs, deploys, dispatches or mutates anything.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Mapping, Sequence

READINESS_SCHEMA = "missipy.github.project_system_deployment_readiness.v1"
PROJECT_QUERY = """
query AutodocProjectReadiness($login: String!, $number: Int!) {
  user(login: $login) {
    projectV2(number: $number) { id number title url closed }
  }
}
""".strip()


@dataclass(frozen=True, slots=True)
class GitHubProjectSystemReadinessConfig:
    config_path: str
    token_env: str
    api_url: str
    graphql_url: str
    project_owner: str
    project_number: int
    project_id: str
    project_url: str
    workflow_repository: str
    workflow_name: str
    workflow_path: str
    workflow_template_path: str
    builder_path: str
    builder_template_path: str
    snapshot_tool_path: str
    change_detection_tool_path: str
    snapshot_dir: str
    report_dir: str
    require_actions_deployment: bool
    query_only: bool
    graphql_mutation_allowed: bool
    remote_mutation_allowed: bool


@dataclass(frozen=True, slots=True)
class GitHubProjectSystemReadinessCommand:
    execute: bool = False
    policy_decision_id: str = ""
    fixture_mode: bool = False


@dataclass(frozen=True, slots=True)
class WorkflowAnalysis:
    valid: bool
    issues: tuple[str, ...]
    sha256: str
    has_issue_trigger: bool
    has_workflow_dispatch: bool
    has_write_permission: bool
    uploads_artifact: bool
    calls_expected_builder: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "issues": list(self.issues),
            "sha256": self.sha256,
            "has_issue_trigger": self.has_issue_trigger,
            "has_workflow_dispatch": self.has_workflow_dispatch,
            "has_write_permission": self.has_write_permission,
            "uploads_artifact": self.uploads_artifact,
            "calls_expected_builder": self.calls_expected_builder,
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectSystemReadinessPlan:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    fixture_mode: bool
    config: GitHubProjectSystemReadinessConfig
    local_checks: Mapping[str, bool]
    local_workflow_analysis: WorkflowAnalysis
    token_present: bool
    boundaries: Mapping[str, bool]


@dataclass(frozen=True, slots=True)
class GitHubProjectSystemReadinessResult:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    local_ready: bool
    project_read_ready: bool
    actions_deployment_ready: bool
    system_ready: bool
    project_id: str
    workflow_repository: str
    workflow_name: str
    workflow_state: str
    workflow_path: str
    local_workflow_sha256: str
    remote_workflow_sha256: str
    workflow_matches_template: bool
    builder_matches_template: bool
    token_env: str
    token_present: bool
    external_call_performed: bool
    installation_performed: bool = False
    deployment_performed: bool = False
    workflow_dispatch_performed: bool = False
    remote_mutation_allowed: bool = False
    graphql_mutation_allowed: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": READINESS_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "local_ready": self.local_ready,
            "project_read_ready": self.project_read_ready,
            "actions_deployment_ready": self.actions_deployment_ready,
            "system_ready": self.system_ready,
            "project_id": self.project_id,
            "workflow_repository": self.workflow_repository,
            "workflow_name": self.workflow_name,
            "workflow_state": self.workflow_state,
            "workflow_path": self.workflow_path,
            "local_workflow_sha256": self.local_workflow_sha256,
            "remote_workflow_sha256": self.remote_workflow_sha256,
            "workflow_matches_template": self.workflow_matches_template,
            "builder_matches_template": self.builder_matches_template,
            "token_env": self.token_env,
            "token_present": self.token_present,
            "external_call_performed": self.external_call_performed,
            "installation_performed": self.installation_performed,
            "deployment_performed": self.deployment_performed,
            "workflow_dispatch_performed": self.workflow_dispatch_performed,
            "remote_mutation_allowed": self.remote_mutation_allowed,
            "graphql_mutation_allowed": self.graphql_mutation_allowed,
            "details": dict(self.details),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"github_project_system_deployment_readiness_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"execute={self.execute}",
                f"local_ready={self.local_ready}",
                f"project_read_ready={self.project_read_ready}",
                f"actions_deployment_ready={self.actions_deployment_ready}",
                f"system_ready={self.system_ready}",
                f"project_id={self.project_id or '-'}",
                f"workflow={self.workflow_repository}:{self.workflow_name}",
                f"external_call_performed={self.external_call_performed}",
                "installation_performed=False",
                "deployment_performed=False",
                "remote_mutation_allowed=False",
            )
        )


def validate_config(config: GitHubProjectSystemReadinessConfig) -> tuple[str, ...]:
    issues: list[str] = []
    required = {
        "token_env": config.token_env,
        "api_url": config.api_url,
        "graphql_url": config.graphql_url,
        "project_owner": config.project_owner,
        "project_id": config.project_id,
        "project_url": config.project_url,
        "workflow_repository": config.workflow_repository,
        "workflow_name": config.workflow_name,
        "workflow_path": config.workflow_path,
        "workflow_template_path": config.workflow_template_path,
        "builder_path": config.builder_path,
        "builder_template_path": config.builder_template_path,
        "snapshot_tool_path": config.snapshot_tool_path,
        "change_detection_tool_path": config.change_detection_tool_path,
    }
    for name, value in required.items():
        if not str(value).strip():
            issues.append(f"config:{name}:missing")
    if config.project_number <= 0:
        issues.append("config:project_number:invalid")
    if config.workflow_repository.count("/") != 1:
        issues.append("config:workflow_repository:owner_name_required")
    if not config.workflow_path.startswith(".github/workflows/"):
        issues.append("config:workflow_path:not_github_workflow")
    if not config.query_only:
        issues.append("config:query_only:must_be_true")
    if config.graphql_mutation_allowed:
        issues.append("config:graphql_mutation_allowed:must_be_false")
    if config.remote_mutation_allowed:
        issues.append("config:remote_mutation_allowed:must_be_false")
    return tuple(issues)


def analyze_workflow(text: str, *, expected_builder_path: str) -> WorkflowAnalysis:
    normalized = text.replace("\r\n", "\n")
    lowered = normalized.lower()
    issues: list[str] = []
    has_issue_trigger = "issues:" in lowered
    has_workflow_dispatch = "workflow_dispatch" in lowered
    has_write_permission = any(
        marker in lowered
        for marker in (
            "contents: write",
            "issues: write",
            "actions: write",
            "pull-requests: write",
            "packages: write",
            "id-token: write",
        )
    )
    uploads_artifact = "actions/upload-artifact@v4" in lowered
    calls_expected_builder = expected_builder_path.lower() in lowered
    if not has_issue_trigger:
        issues.append("workflow:issues_trigger:missing")
    if has_workflow_dispatch:
        issues.append("workflow:workflow_dispatch:forbidden")
    if has_write_permission:
        issues.append("workflow:write_permission:forbidden")
    if not uploads_artifact:
        issues.append("workflow:upload_artifact_v4:missing")
    if not calls_expected_builder:
        issues.append("workflow:expected_builder:missing")
    for marker in ("git push", "gh api --method post", "curl -x post", "curl --request post"):
        if marker in lowered:
            issues.append(f"workflow:mutation_command:forbidden:{marker}")
    return WorkflowAnalysis(
        valid=not issues,
        issues=tuple(issues),
        sha256=_sha256(normalized),
        has_issue_trigger=has_issue_trigger,
        has_workflow_dispatch=has_workflow_dispatch,
        has_write_permission=has_write_permission,
        uploads_artifact=uploads_artifact,
        calls_expected_builder=calls_expected_builder,
    )


def build_plan(
    config: GitHubProjectSystemReadinessConfig,
    command: GitHubProjectSystemReadinessCommand,
    *,
    local_checks: Mapping[str, bool],
    local_workflow_analysis: WorkflowAnalysis,
    token_present: bool,
) -> GitHubProjectSystemReadinessPlan:
    issues = list(validate_config(config))
    project_local_checks = {
        "config",
        "snapshot_tool",
        "change_detection_tool",
        "snapshot_dir_parent",
        "report_dir_parent",
    }
    actions_local_checks = {"workflow_template", "builder_template"}
    required_local_checks = set(project_local_checks)
    if config.require_actions_deployment:
        required_local_checks.update(actions_local_checks)
    issues.extend(
        f"local:{name}:missing"
        for name in sorted(required_local_checks)
        if not local_checks.get(name, False)
    )
    if config.require_actions_deployment:
        issues.extend(local_workflow_analysis.issues)
    if command.execute and not command.policy_decision_id.strip():
        issues.append("gate:policy_decision_id:required")
    if command.execute and not command.fixture_mode and not token_present:
        issues.append(f"gate:token_env:missing:{config.token_env}")
    boundaries = {
        "query_only": True,
        "graphql_mutation_allowed": False,
        "remote_mutation_allowed": False,
        "installation_allowed": False,
        "deployment_allowed": False,
        "workflow_dispatch_allowed": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
    }
    return GitHubProjectSystemReadinessPlan(
        valid=not issues,
        issues=tuple(issues),
        execute=command.execute,
        policy_decision_id=command.policy_decision_id,
        fixture_mode=command.fixture_mode,
        config=config,
        local_checks=dict(local_checks),
        local_workflow_analysis=local_workflow_analysis,
        token_present=token_present,
        boundaries=boundaries,
    )


def close_result(
    plan: GitHubProjectSystemReadinessPlan,
    *,
    project_payload: Mapping[str, Any] | None = None,
    workflow_payload: Mapping[str, Any] | None = None,
    remote_workflow_analysis: WorkflowAnalysis | None = None,
    local_builder_sha256: str = "",
    remote_builder_sha256: str = "",
    external_call_performed: bool = False,
    errors: Sequence[str] = (),
) -> GitHubProjectSystemReadinessResult:
    issues = list(plan.issues)
    issues.extend(str(error) for error in errors)
    project_local_checks = (
        "config",
        "snapshot_tool",
        "change_detection_tool",
        "snapshot_dir_parent",
        "report_dir_parent",
    )
    project_local_ready = all(plan.local_checks.get(name, False) for name in project_local_checks)
    actions_local_ready = (
        plan.local_checks.get("workflow_template", False)
        and plan.local_checks.get("builder_template", False)
        and plan.local_workflow_analysis.valid
    )
    local_ready = project_local_ready and (
        actions_local_ready or not plan.config.require_actions_deployment
    )
    project_read_ready = False
    workflow_state = ""
    workflow_path = ""
    workflow_matches = False
    builder_matches = False
    actions_ready = False
    if plan.execute and project_payload is not None:
        project_id = str(project_payload.get("id", ""))
        project_number = int(project_payload.get("number", 0) or 0)
        project_url = str(project_payload.get("url", ""))
        project_read_ready = (
            project_id == plan.config.project_id
            and project_number == plan.config.project_number
            and project_url.rstrip("/") == plan.config.project_url.rstrip("/")
        )
        if not project_read_ready:
            issues.append("remote:project_identity:mismatch")
    if plan.execute and workflow_payload is not None and remote_workflow_analysis is not None:
        workflow_state = str(workflow_payload.get("state", ""))
        workflow_path = str(workflow_payload.get("path", ""))
        workflow_matches = remote_workflow_analysis.sha256 == plan.local_workflow_analysis.sha256
        builder_matches = bool(local_builder_sha256) and local_builder_sha256 == remote_builder_sha256
        actions_ready = (
            workflow_state == "active"
            and workflow_path == plan.config.workflow_path
            and remote_workflow_analysis.valid
            and workflow_matches
            and builder_matches
        )
        if not actions_ready:
            issues.append("remote:actions_deployment:not_ready")
    system_ready = local_ready and project_read_ready and (
        actions_ready or not plan.config.require_actions_deployment
    )
    if plan.execute and not system_ready and not issues:
        issues.append("system:not_ready")
    return GitHubProjectSystemReadinessResult(
        valid=not issues,
        issues=tuple(dict.fromkeys(issues)),
        execute=plan.execute,
        policy_decision_id=plan.policy_decision_id,
        local_ready=local_ready,
        project_read_ready=project_read_ready,
        actions_deployment_ready=actions_ready,
        system_ready=system_ready,
        project_id=plan.config.project_id,
        workflow_repository=plan.config.workflow_repository,
        workflow_name=plan.config.workflow_name,
        workflow_state=workflow_state,
        workflow_path=workflow_path,
        local_workflow_sha256=plan.local_workflow_analysis.sha256,
        remote_workflow_sha256=(remote_workflow_analysis.sha256 if remote_workflow_analysis else ""),
        workflow_matches_template=workflow_matches,
        builder_matches_template=builder_matches,
        token_env=plan.config.token_env,
        token_present=plan.token_present,
        external_call_performed=external_call_performed,
        details={
            "local_checks": dict(plan.local_checks),
            "local_workflow": plan.local_workflow_analysis.to_json_dict(),
            "remote_workflow": remote_workflow_analysis.to_json_dict() if remote_workflow_analysis else None,
            "require_actions_deployment": plan.config.require_actions_deployment,
            "project_native_ready": project_local_ready and project_read_ready,
            "actions_bridge_optional": not plan.config.require_actions_deployment,
            "boundaries": dict(plan.boundaries),
        },
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
