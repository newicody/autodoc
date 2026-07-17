from __future__ import annotations

from context.github_actions_artifact_scan_once_live_0272 import (
    GitHubActionsArtifactScanPlan,
    close_github_actions_artifact_scan_result,
)


def _plan() -> GitHubActionsArtifactScanPlan:
    return GitHubActionsArtifactScanPlan(
        valid=True,
        issues=(),
        execute=True,
        policy_decision_id="policy:test-fetch",
        repository="newicody/projects",
        project_url="https://github.com/users/newicody/projects/3",
        workflow_name="autodoc-controlled-research.yml",
        artifact_name_prefix="autodoc-",
        token_env="AUTODOC_PROJECT_TOKEN",
        api_url="https://api.github.com",
        dataset_root="/srv/autodoc/github-artifacts",
        dataset_state_path="/srv/autodoc/github-artifacts/state.json",
        fetch_tool="tools/run_github_actions_artifact_fetch_once.py",
        max_runs=10,
        max_artifacts=30,
        fixture_mode=True,
        force=False,
        boundaries={},
    )


def _report(downloaded=(), skipped=()):
    return {
        "schema": "missipy.github_actions.artifact_fetch_once_report.v1",
        "status": "ok",
        "repository": "newicody/projects",
        "workflow_name": "autodoc-controlled-research.yml",
        "artifact_name_prefix": "autodoc-",
        "external_call_performed": False,
        "counts": {
            "workflow_run_count": 1,
            "artifact_seen_count": len(downloaded) + len(skipped),
            "downloaded_count": len(downloaded),
            "synced_count": len(downloaded),
            "skipped_count": len(skipped),
            "error_count": 0,
        },
        "downloaded_artifacts": list(downloaded),
        "skipped": list(skipped),
        "errors": [],
        "state_path": "/srv/autodoc/github-artifacts/state.json",
        "staging_root": "/srv/autodoc/github-artifacts/staging",
        "boundary": [
            "read-only GitHub Actions artifact fetch",
            "no remote mutation",
            "no SQL write",
            "no qdrant write",
        ],
    }


def _artifact(run_id: str, artifact_id: int, name: str):
    return {
        "run_id": run_id,
        "artifact_id": artifact_id,
        "artifact_name": name,
        "staging_dir": f"/staging/{run_id}/{artifact_id}",
        "sync_status": "ok",
    }


def test_three_downloaded_legacy_artifacts_produce_one_ready_run() -> None:
    result = close_github_actions_artifact_scan_result(
        _plan(),
        child_returncode=0,
        child_report=_report(
            downloaded=(
                _artifact("29255262261", 1, "autodoc-authoritative-request"),
                _artifact("29255262261", 2, "autodoc-copilot-advisory"),
                _artifact("29255262261", 3, "autodoc-dual-artifact-manifest"),
            )
        ),
        token_present=False,
    )

    assert result.valid
    assert result.counts["ready_run_count"] == 1
    assert result.counts["deferred_run_count"] == 0
    assert len(result.ready_runs) == 1
    ready = result.ready_runs[0]
    assert ready["run_id"] == "29255262261"
    assert ready["status"] == "ready"
    assert set(ready["artifacts"]) == {
        "authoritative_request",
        "copilot_advisory",
        "run_manifest",
    }
    assert ready["local_execution_started"] is False
    assert ready["remote_mutation_performed"] is False


def test_downloaded_and_already_synced_members_form_ready_run() -> None:
    result = close_github_actions_artifact_scan_result(
        _plan(),
        child_returncode=0,
        child_report=_report(
            downloaded=(
                _artifact(
                    "29255262261",
                    2,
                    "autodoc-copilot-advisory",
                ),
            ),
            skipped=(
                {
                    **_artifact(
                        "29255262261",
                        1,
                        "autodoc-authoritative-request",
                    ),
                    "reason": "already_synced",
                },
                {
                    **_artifact(
                        "29255262261",
                        3,
                        "autodoc-dual-artifact-manifest",
                    ),
                    "reason": "already_synced",
                },
            ),
        ),
        token_present=False,
    )

    assert len(result.ready_runs) == 1
    artifacts = result.ready_runs[0]["artifacts"]
    assert artifacts["copilot_advisory"]["availability"] == "downloaded"
    assert artifacts["authoritative_request"]["availability"] == (
        "already_synced"
    )


def test_readable_canonical_names_are_accepted() -> None:
    result = close_github_actions_artifact_scan_result(
        _plan(),
        child_returncode=0,
        child_report=_report(
            downloaded=(
                _artifact(
                    "44",
                    1,
                    "autodoc-i42-amour--authoritative-request-v1",
                ),
                _artifact(
                    "44",
                    2,
                    "autodoc-i42-amour--copilot-advisory-v2",
                ),
                _artifact(
                    "44",
                    3,
                    "autodoc-i42-amour--run-manifest-v1",
                ),
            )
        ),
        token_present=False,
    )

    assert [item["run_id"] for item in result.ready_runs] == ["44"]
    assert result.deferred_runs == ()


def test_missing_or_expired_member_is_deferred_not_executed() -> None:
    result = close_github_actions_artifact_scan_result(
        _plan(),
        child_returncode=0,
        child_report=_report(
            downloaded=(
                _artifact("9", 1, "autodoc-authoritative-request"),
                _artifact("9", 3, "autodoc-dual-artifact-manifest"),
            ),
            skipped=(
                {
                    **_artifact("9", 2, "autodoc-copilot-advisory"),
                    "reason": "expired",
                },
            ),
        ),
        token_present=False,
    )

    assert result.valid
    assert result.ready_runs == ()
    assert len(result.deferred_runs) == 1
    deferred = result.deferred_runs[0]
    assert deferred["missing_roles"] == ["copilot_advisory"]
    assert deferred["reasons"] == [
        "missing_roles",
        "unavailable_artifacts",
    ]
    assert deferred["local_execution_started"] is False


def test_duplicate_role_is_deferred_as_ambiguous() -> None:
    result = close_github_actions_artifact_scan_result(
        _plan(),
        child_returncode=0,
        child_report=_report(
            downloaded=(
                _artifact("7", 1, "autodoc-authoritative-request"),
                _artifact(
                    "7",
                    2,
                    "autodoc-i7-title--authoritative-request-v1",
                ),
                _artifact("7", 3, "autodoc-copilot-advisory"),
                _artifact("7", 4, "autodoc-dual-artifact-manifest"),
            )
        ),
        token_present=False,
    )

    assert result.ready_runs == ()
    assert result.deferred_runs[0]["duplicate_roles"] == [
        "authoritative_request"
    ]
    assert result.counts["deferred_run_count"] == 1
