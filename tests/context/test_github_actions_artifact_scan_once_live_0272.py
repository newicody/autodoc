from context.github_actions_artifact_scan_once_live_0272 import (
    GitHubActionsArtifactScanCommand,
    GitHubActionsArtifactScanSnapshot,
    build_github_actions_artifact_scan_plan,
    close_github_actions_artifact_scan_result,
)


def _snapshot(**overrides):
    values = {
        "project_config_path": "config/project.ini",
        "fetch_config_path": "config/fetch.ini",
        "repository": "newicody/autodoc-ideas",
        "fetch_repository": "newicody/autodoc-ideas",
        "development_repository": "newicody/autodoc",
        "fetch_development_repository": "newicody/autodoc",
        "project_url": "https://github.com/users/newicody/projects/2",
        "fetch_project_url": "https://github.com/users/newicody/projects/2",
        "workflow_name": "autodoc-ticket-artifact.yml",
        "fetch_workflow_name": "autodoc-ticket-artifact.yml",
        "artifact_name_prefix": "autodoc-ticket-artifact-",
        "fetch_artifact_name_prefix": "autodoc-ticket-artifact-",
        "token_env": "GITHUB_TOKEN",
        "fetch_token_env": "GITHUB_TOKEN",
        "api_url": "https://api.github.com",
        "fetch_api_url": "https://api.github.com",
        "allowed_repositories": ("newicody/autodoc-ideas",),
        "fetch_allowed_repositories": ("newicody/autodoc-ideas",),
        "scan_command": (
            "tools/run_github_actions_artifact_scan_once_live_0272.py "
            "--execute --policy-decision-id "
            "policy:0272:fcron-actions-artifacts-read-only"
        ),
        "history_mode": "append_only",
        "dataset_root": ".var/server_datasets/github_artifacts",
        "dataset_state_path": ".var/server_datasets/github_artifacts/index/fetch_state.json",
        "read_only_scan": True,
        "read_only_fetch": True,
        "allow_workflow_dispatch": False,
        "allow_remote_mutation": False,
        "allow_sql_write": False,
        "allow_qdrant_write": False,
    }
    values.update(overrides)
    return GitHubActionsArtifactScanSnapshot(**values)


def test_0272_r2_builds_bounded_plan_without_direct_issue_scan() -> None:
    plan = build_github_actions_artifact_scan_plan(
        _snapshot(),
        GitHubActionsArtifactScanCommand(),
    )
    assert plan.valid is True
    assert plan.execute is False
    assert plan.fetch_tool == "tools/run_github_actions_artifact_fetch_once.py"
    assert plan.boundaries["github_actions_artifacts_only"] is True
    assert plan.boundaries["direct_issue_scan_required"] is False
    assert plan.boundaries["remote_mutation_allowed"] is False


def test_0272_r2_requires_decision_for_live_execute() -> None:
    plan = build_github_actions_artifact_scan_plan(
        _snapshot(),
        GitHubActionsArtifactScanCommand(execute=True),
    )
    assert plan.valid is False
    assert "policy_decision_id is required" in " ".join(plan.issues)


def test_0272_r2_rejects_config_mismatch_and_mutation() -> None:
    plan = build_github_actions_artifact_scan_plan(
        _snapshot(
            fetch_repository="other/repo",
            allow_remote_mutation=True,
            allow_workflow_dispatch=True,
        ),
        GitHubActionsArtifactScanCommand(),
    )
    assert plan.valid is False
    combined = " ".join(plan.issues)
    assert "repository mismatch" in combined
    assert "workflow_dispatch" in combined
    assert "remote mutation" in combined


def test_0272_r2_closes_live_child_report() -> None:
    plan = build_github_actions_artifact_scan_plan(
        _snapshot(),
        GitHubActionsArtifactScanCommand(
            execute=True,
            policy_decision_id="policy:0272:read-only-artifacts",
        ),
    )
    result = close_github_actions_artifact_scan_result(
        plan,
        child_returncode=0,
        token_present=True,
        child_report={
            "schema": "missipy.github_actions.artifact_fetch_once_report.v1",
            "repository": "newicody/autodoc-ideas",
            "workflow_name": "autodoc-ticket-artifact.yml",
            "artifact_name_prefix": "autodoc-ticket-artifact-",
            "boundary": [
                "read-only GitHub Actions artifact fetch",
                "no remote mutation",
                "no SQL write",
                "no qdrant write",
            ],
            "status": "ok",
            "external_call_performed": True,
            "counts": {
                "workflow_run_count": 2,
                "artifact_seen_count": 3,
                "downloaded_count": 1,
                "synced_count": 1,
                "skipped_count": 2,
                "error_count": 0,
            },
            "downloaded_artifacts": [{"artifact_id": "10"}],
            "skipped": [{"artifact_id": "9", "reason": "already_synced"}],
            "errors": [],
            "state_path": ".var/state.json",
            "staging_root": ".var/staging",
        },
    )
    assert result.valid is True
    assert result.counts["synced_count"] == 1
    assert result.external_call_performed is True
    assert result.boundaries["direct_issue_scan_required"] is False
    assert result.boundaries["token_value_serialized"] is False


def test_0272_r2_fixture_mode_must_remain_offline() -> None:
    plan = build_github_actions_artifact_scan_plan(
        _snapshot(),
        GitHubActionsArtifactScanCommand(
            execute=True,
            policy_decision_id="policy:fixture",
            fixture_mode=True,
        ),
    )
    result = close_github_actions_artifact_scan_result(
        plan,
        child_returncode=0,
        token_present=False,
        child_report={
            "schema": "missipy.github_actions.artifact_fetch_once_report.v1",
            "repository": "newicody/autodoc-ideas",
            "workflow_name": "autodoc-ticket-artifact.yml",
            "artifact_name_prefix": "autodoc-ticket-artifact-",
            "boundary": [
                "read-only GitHub Actions artifact fetch",
                "no remote mutation",
                "no SQL write",
                "no qdrant write",
            ],
            "status": "ok",
            "external_call_performed": False,
            "counts": {"error_count": 0},
        },
    )
    assert result.valid is True
    assert result.fixture_mode is True
    assert result.external_call_performed is False


def test_0272_r2_rejects_misaligned_child_report() -> None:
    plan = build_github_actions_artifact_scan_plan(
        _snapshot(),
        GitHubActionsArtifactScanCommand(
            execute=True,
            policy_decision_id="policy:0272:misaligned",
        ),
    )
    result = close_github_actions_artifact_scan_result(
        plan,
        child_returncode=0,
        token_present=True,
        child_report={
            "schema": "wrong",
            "status": "ok",
            "repository": "other/repository",
            "workflow_name": "other.yml",
            "artifact_name_prefix": "other-",
            "external_call_performed": True,
            "counts": {"error_count": 0},
            "boundary": [],
        },
    )
    assert result.valid is False
    combined = " ".join(result.issues)
    assert "schema mismatch" in combined
    assert "repository mismatch" in combined
    assert "boundary missing" in combined


def test_0272_r2_rejects_uncontrolled_configured_command_arguments() -> None:
    plan = build_github_actions_artifact_scan_plan(
        _snapshot(
            scan_command=(
                "tools/run_github_actions_artifact_scan_once_live_0272.py "
                "--execute --shell-command dangerous"
            )
        ),
        GitHubActionsArtifactScanCommand(),
    )
    assert plan.valid is False
    assert "argument is not allowed" in " ".join(plan.issues)
