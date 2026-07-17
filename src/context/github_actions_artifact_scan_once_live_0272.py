"""Pure contract for the 0272 GitHub Actions artifact scan-once live binding.

The actual GitHub GET/download transport remains the existing 0168 tool. This
module validates the alignment between the Project push-frame config and the
server artifact-fetch config, builds a bounded one-shot plan, and closes the
child report. It performs no IO and never carries a token value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import shlex
from typing import Any, Mapping

from context.human_readable_artifact_identity_0287 import (
    matches_actions_artifact_name,
)

SCAN_SCHEMA = "missipy.github_actions.artifact_scan_once_live.v1"
_FETCH_REPORT_SCHEMA = "missipy.github_actions.artifact_fetch_once_report.v1"
_DEFAULT_FETCH_TOOL = "tools/run_github_actions_artifact_fetch_once.py"
_DEFAULT_LIVE_TOOL = "tools/run_github_actions_artifact_scan_once_live_0272.py"
_LEGACY_SCAN_TOOL = "tools/run_github_artifact_scan_once.py"


_EXPECTED_CORRELATED_ARTIFACTS = (
    ("authoritative_request", "autodoc-authoritative-request"),
    ("copilot_advisory", "autodoc-copilot-advisory"),
    ("run_manifest", "autodoc-dual-artifact-manifest"),
)
_AVAILABLE_SKIP_REASONS = frozenset({"already_synced"})


@dataclass(frozen=True, slots=True)
class GitHubActionsArtifactScanSnapshot:
    project_config_path: str
    fetch_config_path: str
    repository: str
    fetch_repository: str
    development_repository: str
    fetch_development_repository: str
    project_url: str
    fetch_project_url: str
    workflow_name: str
    fetch_workflow_name: str
    artifact_name_prefix: str
    fetch_artifact_name_prefix: str
    token_env: str
    fetch_token_env: str
    api_url: str
    fetch_api_url: str
    allowed_repositories: tuple[str, ...]
    fetch_allowed_repositories: tuple[str, ...]
    scan_command: str
    history_mode: str
    dataset_root: str
    dataset_state_path: str
    read_only_scan: bool
    read_only_fetch: bool
    allow_workflow_dispatch: bool
    allow_remote_mutation: bool
    allow_sql_write: bool
    allow_qdrant_write: bool


@dataclass(frozen=True, slots=True)
class GitHubActionsArtifactScanCommand:
    execute: bool = False
    policy_decision_id: str = ""
    max_runs: int = 10
    max_artifacts: int = 20
    fixture_mode: bool = False
    force: bool = False

    def __post_init__(self) -> None:
        if self.max_runs <= 0:
            raise ValueError("max_runs must be > 0")
        if self.max_artifacts <= 0:
            raise ValueError("max_artifacts must be > 0")


@dataclass(frozen=True, slots=True)
class GitHubActionsArtifactScanPolicy:
    fetch_tool: str = _DEFAULT_FETCH_TOOL
    accepted_scan_commands: tuple[str, ...] = (
        _DEFAULT_LIVE_TOOL,
        _LEGACY_SCAN_TOOL,
    )
    require_policy_decision_for_execute: bool = True
    direct_issue_scan_allowed: bool = False
    direct_project_graphql_scan_allowed: bool = False
    workflow_dispatch_allowed: bool = False
    remote_mutation_allowed: bool = False


@dataclass(frozen=True, slots=True)
class GitHubActionsArtifactScanPlan:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    repository: str
    project_url: str
    workflow_name: str
    artifact_name_prefix: str
    token_env: str
    api_url: str
    dataset_root: str
    dataset_state_path: str
    fetch_tool: str
    max_runs: int
    max_artifacts: int
    fixture_mode: bool
    force: bool
    boundaries: Mapping[str, bool]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": SCAN_SCHEMA,
            "kind": "plan",
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "repository": self.repository,
            "project_url": self.project_url,
            "workflow_name": self.workflow_name,
            "artifact_name_prefix": self.artifact_name_prefix,
            "token_env": self.token_env,
            "api_url": self.api_url,
            "dataset_root": self.dataset_root,
            "dataset_state_path": self.dataset_state_path,
            "fetch_tool": self.fetch_tool,
            "max_runs": self.max_runs,
            "max_artifacts": self.max_artifacts,
            "fixture_mode": self.fixture_mode,
            "force": self.force,
            "boundaries": dict(self.boundaries),
        }


@dataclass(frozen=True, slots=True)
class GitHubActionsArtifactScanResult:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    repository: str
    project_url: str
    workflow_name: str
    artifact_name_prefix: str
    token_env: str
    token_present: bool
    fixture_mode: bool
    child_returncode: int | None
    child_status: str
    counts: Mapping[str, int]
    state_path: str
    staging_root: str
    downloaded_artifacts: tuple[Mapping[str, Any], ...] = ()
    skipped: tuple[Mapping[str, Any], ...] = ()
    errors: tuple[Mapping[str, Any], ...] = ()
    ready_runs: tuple[Mapping[str, Any], ...] = ()
    deferred_runs: tuple[Mapping[str, Any], ...] = ()
    external_call_performed: bool = False
    boundaries: Mapping[str, bool] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": SCAN_SCHEMA,
            "kind": "result",
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "repository": self.repository,
            "project_url": self.project_url,
            "workflow_name": self.workflow_name,
            "artifact_name_prefix": self.artifact_name_prefix,
            "token_env": self.token_env,
            "token_present": self.token_present,
            "fixture_mode": self.fixture_mode,
            "child_returncode": self.child_returncode,
            "child_status": self.child_status,
            "counts": dict(self.counts),
            "state_path": self.state_path,
            "staging_root": self.staging_root,
            "downloaded_artifacts": [dict(item) for item in self.downloaded_artifacts],
            "skipped": [dict(item) for item in self.skipped],
            "errors": [dict(item) for item in self.errors],
            "ready_runs": [dict(item) for item in self.ready_runs],
            "deferred_runs": [dict(item) for item in self.deferred_runs],
            "external_call_performed": self.external_call_performed,
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"github_actions_artifact_scan_once_live_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"execute={self.execute}",
                f"repository={self.repository or '-'}",
                f"workflow={self.workflow_name or '-'}",
                f"downloaded={self.counts.get('downloaded_count', 0)}",
                f"synced={self.counts.get('synced_count', 0)}",
                f"skipped={self.counts.get('skipped_count', 0)}",
                f"ready_runs={self.counts.get('ready_run_count', 0)}",
                f"deferred_runs={self.counts.get('deferred_run_count', 0)}",
                f"external_call_performed={self.external_call_performed}",
                "direct_issue_scan_required=False",
                "remote_mutation_allowed=False",
            )
        )


def build_github_actions_artifact_scan_plan(
    snapshot: GitHubActionsArtifactScanSnapshot,
    command: GitHubActionsArtifactScanCommand,
    policy: GitHubActionsArtifactScanPolicy | None = None,
) -> GitHubActionsArtifactScanPlan:
    policy = policy or GitHubActionsArtifactScanPolicy()
    issues = _validate_snapshot(snapshot, command, policy)
    return GitHubActionsArtifactScanPlan(
        valid=not issues,
        issues=tuple(issues),
        execute=command.execute,
        policy_decision_id=command.policy_decision_id,
        repository=snapshot.repository,
        project_url=snapshot.project_url,
        workflow_name=snapshot.workflow_name,
        artifact_name_prefix=snapshot.artifact_name_prefix,
        token_env=snapshot.token_env,
        api_url=snapshot.api_url,
        dataset_root=snapshot.dataset_root,
        dataset_state_path=snapshot.dataset_state_path,
        fetch_tool=policy.fetch_tool,
        max_runs=command.max_runs,
        max_artifacts=command.max_artifacts,
        fixture_mode=command.fixture_mode,
        force=command.force,
        boundaries=_boundaries(command.execute, command.fixture_mode),
    )


def close_github_actions_artifact_scan_result(
    plan: GitHubActionsArtifactScanPlan,
    *,
    child_returncode: int | None,
    child_report: Mapping[str, Any] | None,
    token_present: bool,
) -> GitHubActionsArtifactScanResult:
    report = dict(child_report or {})
    issues = list(plan.issues)
    status = str(report.get("status", "planned" if not plan.execute else "missing"))
    counts = _counts(report.get("counts"))
    downloaded_artifacts = _mapping_tuple(
        report.get("downloaded_artifacts")
    )
    skipped = _mapping_tuple(report.get("skipped"))
    ready_runs, deferred_runs = _correlate_fetched_runs(
        repository=plan.repository,
        downloaded_artifacts=downloaded_artifacts,
        skipped=skipped,
    )
    counts = dict(counts)
    counts["ready_run_count"] = len(ready_runs)
    counts["deferred_run_count"] = len(deferred_runs)
    external_call_performed = bool(report.get("external_call_performed", False))

    if plan.execute:
        if child_returncode is None:
            issues.append("fetch tool was not executed")
        elif child_returncode != 0:
            issues.append(f"fetch tool returned {child_returncode}")
        if status != "ok":
            issues.append(f"fetch report status must be ok, got {status}")
        if str(report.get("schema", "")) != _FETCH_REPORT_SCHEMA:
            issues.append("fetch report schema mismatch")
        if str(report.get("repository", "")) != plan.repository:
            issues.append("fetch report repository mismatch")
        if str(report.get("workflow_name", "")) != plan.workflow_name:
            issues.append("fetch report workflow mismatch")
        if str(report.get("artifact_name_prefix", "")) != plan.artifact_name_prefix:
            issues.append("fetch report artifact prefix mismatch")
        boundary_text = " ".join(str(item) for item in report.get("boundary", ()))
        for required_boundary in (
            "read-only GitHub Actions artifact fetch",
            "no remote mutation",
            "no SQL write",
            "no qdrant write",
        ):
            if required_boundary not in boundary_text:
                issues.append(f"fetch report boundary missing: {required_boundary}")
        if counts["error_count"] != 0:
            issues.append("fetch report contains errors")
        if plan.fixture_mode and external_call_performed:
            issues.append("fixture mode must not perform an external call")
        if not plan.fixture_mode and not external_call_performed:
            issues.append("live execution must report an external read call")
    elif child_report:
        issues.append("plan-only mode must not contain a child report")

    boundaries = dict(plan.boundaries)
    boundaries.update(
        {
            "github_actions_artifacts_only": True,
            "direct_issue_scan_required": False,
            "direct_project_graphql_scan_required": False,
            "workflow_dispatch_allowed": False,
            "remote_mutation_allowed": False,
            "token_value_serialized": False,
            "local_dataset_write_only": True,
            "correlated_three_artifact_runs": True,
            "ready_runs_are_local_handoffs": True,
            "laboratory_execution_started": False,
        }
    )

    return GitHubActionsArtifactScanResult(
        valid=not issues,
        issues=tuple(issues),
        execute=plan.execute,
        policy_decision_id=plan.policy_decision_id,
        repository=plan.repository,
        project_url=plan.project_url,
        workflow_name=plan.workflow_name,
        artifact_name_prefix=plan.artifact_name_prefix,
        token_env=plan.token_env,
        token_present=token_present,
        fixture_mode=plan.fixture_mode,
        child_returncode=child_returncode,
        child_status=status,
        counts=counts,
        state_path=str(report.get("state_path", plan.dataset_state_path)),
        staging_root=str(report.get("staging_root", "")),
        downloaded_artifacts=downloaded_artifacts,
        skipped=skipped,
        errors=_mapping_tuple(report.get("errors")),
        ready_runs=ready_runs,
        deferred_runs=deferred_runs,
        external_call_performed=external_call_performed,
        boundaries=boundaries,
    )


def _validate_snapshot(
    snapshot: GitHubActionsArtifactScanSnapshot,
    command: GitHubActionsArtifactScanCommand,
    policy: GitHubActionsArtifactScanPolicy,
) -> list[str]:
    issues: list[str] = []
    pairs = (
        ("repository", snapshot.repository, snapshot.fetch_repository),
        (
            "development_repository",
            snapshot.development_repository,
            snapshot.fetch_development_repository,
        ),
        ("project_url", snapshot.project_url, snapshot.fetch_project_url),
        ("workflow_name", snapshot.workflow_name, snapshot.fetch_workflow_name),
        (
            "artifact_name_prefix",
            snapshot.artifact_name_prefix,
            snapshot.fetch_artifact_name_prefix,
        ),
        ("token_env", snapshot.token_env, snapshot.fetch_token_env),
        ("api_url", snapshot.api_url.rstrip("/"), snapshot.fetch_api_url.rstrip("/")),
    )
    for name, project_value, fetch_value in pairs:
        if not project_value:
            issues.append(f"{name} missing from project config")
        if project_value != fetch_value:
            issues.append(f"{name} mismatch between project and fetch configs")

    if snapshot.repository == snapshot.development_repository:
        issues.append("development repository cannot be an artifact source")
    if snapshot.repository not in snapshot.allowed_repositories:
        issues.append("repository missing from project allow-list")
    if snapshot.repository not in snapshot.fetch_allowed_repositories:
        issues.append("repository missing from fetch allow-list")
    issues.extend(_validate_scan_command(snapshot.scan_command, policy))
    if snapshot.history_mode != "append_only":
        issues.append("history_mode must be append_only")
    if not snapshot.read_only_scan or not snapshot.read_only_fetch:
        issues.append("both configs must keep read-only scan/fetch enabled")
    if snapshot.allow_workflow_dispatch or policy.workflow_dispatch_allowed:
        issues.append("workflow_dispatch must remain disabled")
    if snapshot.allow_remote_mutation or policy.remote_mutation_allowed:
        issues.append("remote mutation must remain disabled")
    if snapshot.allow_sql_write:
        issues.append("GitHub scan must not write SQL")
    if snapshot.allow_qdrant_write:
        issues.append("GitHub scan must not write Qdrant")
    if command.execute and policy.require_policy_decision_for_execute:
        if not command.policy_decision_id.strip():
            issues.append("policy_decision_id is required for execute mode")
    return issues



def _validate_scan_command(
    value: str,
    policy: GitHubActionsArtifactScanPolicy,
) -> list[str]:
    issues: list[str] = []
    try:
        tokens = shlex.split(value)
    except ValueError as exc:
        return [f"project scan_command cannot be parsed: {exc}"]
    if not tokens or tokens[0] not in policy.accepted_scan_commands:
        return ["project scan_command is not an accepted scan-once surface"]
    arguments = tokens[1:]
    if not arguments:
        return issues
    if tokens[0] != _DEFAULT_LIVE_TOOL:
        return ["legacy scan_command cannot carry live execution arguments"]

    execute_seen = False
    decision_id = ""
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--execute" and not execute_seen:
            execute_seen = True
            index += 1
            continue
        if argument == "--policy-decision-id" and not decision_id:
            if index + 1 >= len(arguments):
                issues.append("configured policy_decision_id is missing")
                break
            decision_id = arguments[index + 1].strip()
            index += 2
            continue
        issues.append(f"project scan_command argument is not allowed: {argument}")
        index += 1
    if execute_seen != bool(decision_id):
        issues.append(
            "configured scan_command must pair --execute with --policy-decision-id"
        )
    return issues


def _correlate_fetched_runs(
    *,
    repository: str,
    downloaded_artifacts: tuple[Mapping[str, Any], ...],
    skipped: tuple[Mapping[str, Any], ...],
) -> tuple[
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
]:
    """Group locally available artifacts into strict three-member run handoffs."""

    records_by_run: dict[str, list[dict[str, Any]]] = {}
    for item in downloaded_artifacts:
        record = _availability_record(item, availability="downloaded")
        if record is not None:
            records_by_run.setdefault(record["run_id"], []).append(record)
    for item in skipped:
        reason = str(item.get("reason", "")).strip()
        availability = (
            "already_synced"
            if reason in _AVAILABLE_SKIP_REASONS
            else f"unavailable:{reason or 'skipped'}"
        )
        record = _availability_record(item, availability=availability)
        if record is not None:
            records_by_run.setdefault(record["run_id"], []).append(record)

    ready: list[Mapping[str, Any]] = []
    deferred: list[Mapping[str, Any]] = []
    for run_id in sorted(records_by_run, key=_run_sort_key, reverse=True):
        records = tuple(records_by_run[run_id])
        role_matches: dict[str, list[dict[str, Any]]] = {
            role: [] for role, _legacy_name in _EXPECTED_CORRELATED_ARTIFACTS
        }
        unavailable: list[dict[str, Any]] = []
        for record in records:
            if str(record["availability"]).startswith("unavailable:"):
                unavailable.append(record)
                continue
            for role, legacy_name in _EXPECTED_CORRELATED_ARTIFACTS:
                if matches_actions_artifact_name(
                    str(record["artifact_name"]),
                    legacy_name,
                ):
                    role_matches[role].append(record)

        missing_roles = tuple(
            role for role, matches in role_matches.items() if not matches
        )
        duplicate_roles = tuple(
            role for role, matches in role_matches.items() if len(matches) > 1
        )
        handoff_ref = _run_handoff_ref(repository, run_id)
        if not missing_roles and not duplicate_roles:
            ready.append(
                {
                    "repository": repository,
                    "run_id": run_id,
                    "handoff_ref": handoff_ref,
                    "status": "ready",
                    "artifact_count": len(_EXPECTED_CORRELATED_ARTIFACTS),
                    "artifacts": {
                        role: dict(matches[0])
                        for role, matches in role_matches.items()
                    },
                    "local_execution_started": False,
                    "remote_mutation_performed": False,
                }
            )
            continue

        reasons: list[str] = []
        if missing_roles:
            reasons.append("missing_roles")
        if duplicate_roles:
            reasons.append("duplicate_roles")
        if unavailable:
            reasons.append("unavailable_artifacts")
        deferred.append(
            {
                "repository": repository,
                "run_id": run_id,
                "handoff_ref": handoff_ref,
                "status": "deferred",
                "reasons": reasons,
                "missing_roles": list(missing_roles),
                "duplicate_roles": list(duplicate_roles),
                "available_role_counts": {
                    role: len(matches)
                    for role, matches in role_matches.items()
                },
                "unavailable_artifacts": [
                    dict(record) for record in unavailable
                ],
                "local_execution_started": False,
                "remote_mutation_performed": False,
            }
        )
    return tuple(ready), tuple(deferred)


def _availability_record(
    item: Mapping[str, Any],
    *,
    availability: str,
) -> dict[str, Any] | None:
    run_id = str(item.get("run_id", "")).strip()
    artifact_id = str(item.get("artifact_id", "")).strip()
    artifact_name = str(item.get("artifact_name", "")).strip()
    if not run_id or not artifact_id or not artifact_name:
        return None
    record: dict[str, Any] = {
        "run_id": run_id,
        "artifact_id": artifact_id,
        "artifact_name": artifact_name,
        "availability": availability,
    }
    staging_dir = str(item.get("staging_dir", "")).strip()
    if staging_dir:
        record["staging_dir"] = staging_dir
    sync_status = str(item.get("sync_status", "")).strip()
    if sync_status:
        record["sync_status"] = sync_status
    return record


def _run_sort_key(run_id: str) -> tuple[int, str]:
    try:
        return int(run_id), run_id
    except ValueError:
        return -1, run_id


def _run_handoff_ref(repository: str, run_id: str) -> str:
    repository_slug = repository.replace("/", "-")
    return f"github-actions-ready-run:{repository_slug}:{run_id}"

def _counts(value: object) -> dict[str, int]:
    source = value if isinstance(value, Mapping) else {}
    names = (
        "workflow_run_count",
        "artifact_seen_count",
        "downloaded_count",
        "synced_count",
        "skipped_count",
        "error_count",
    )
    return {name: int(source.get(name, 0)) for name in names}


def _mapping_tuple(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(dict(item) for item in value if isinstance(item, Mapping))


def _boundaries(execute: bool, fixture_mode: bool) -> dict[str, bool]:
    return {
        "scan_once": True,
        "plan_only": not execute,
        "fixture_mode": fixture_mode,
        "github_actions_artifacts_only": True,
        "direct_issue_scan_required": False,
        "direct_project_graphql_scan_required": False,
        "workflow_dispatch_allowed": False,
        "remote_mutation_allowed": False,
        "scheduler_modified": False,
        "polling_loop_added": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
    }
