from __future__ import annotations

from context.github_research_love_end_to_end_acceptance_0287 import (
    EndToEndAcceptanceCommand,
    EXPECTED_STAGE_ORDER,
    validate_github_research_love_end_to_end,
)


def _fetch() -> dict[str, object]:
    return {
        "schema": "missipy.github_actions.artifact_fetch_cycle_once.v1",
        "valid": True,
        "mode": "execute",
        "status": "artifacts-fetched",
        "ready_runs": [
            {
                "repository": "newicody/projects",
                "issue_number": 77,
                "run_id": "30000000001",
                "artifacts": [
                    {
                        "repository": "newicody/projects",
                        "run_id": "30000000001",
                        "role": "authoritative_request",
                    },
                    {
                        "repository": "newicody/projects",
                        "run_id": "30000000001",
                        "role": "copilot_advisory",
                    },
                    {
                        "repository": "newicody/projects",
                        "run_id": "30000000001",
                        "role": "run_manifest",
                    },
                ],
            }
        ],
    }


def _prepared() -> dict[str, object]:
    return {
        "schema": "missipy.github.research_love_operational_closed_loop.v1",
        "valid": True,
        "mode": "prepare",
        "status": "publication-confirmation-required",
        "input": {
            "repository": "newicody/projects",
            "run_id": "30000000001",
        },
        "publication_plan_digest": "sha256:abc123",
        "prepared": {
            "schema": "missipy.github.research_love_closed_loop_prepared.v1",
            "valid": True,
            "issue_number": 77,
            "work_package_ref": "research-work-package:test",
            "stage_order": list(EXPECTED_STAGE_ORDER),
        },
    }


def _completed() -> dict[str, object]:
    return {
        "schema": "missipy.github.research_love_operational_closed_loop.v1",
        "valid": True,
        "mode": "complete",
        "status": "closed",
        "input": {
            "repository": "newicody/projects",
            "run_id": "30000000001",
            "publication_plan_digest": "sha256:abc123",
        },
        "remote_publication": {"status": "published"},
        "closure": {"valid": True, "cycle_closed": True},
        "boundaries": {
            "publication_evidence_persisted": True,
            "cycle_closed": True,
        },
    }


def _observations() -> tuple[dict[str, str], ...]:
    values: list[dict[str, str]] = []
    for index in range(10):
        for phase in ("CREATED", "STARTED", "SUCCEEDED", "CLOSED"):
            values.append(
                {
                    "observation_ref": f"scheduler-observation:{index}-{phase}",
                    "scheduler_ref": "scheduler:canonical",
                    "command_ref": "scheduler-command:test",
                    "task_ref": f"scheduler-task:{index}",
                    "handler_ref": f"handler:test-{index}",
                    "capability_ref": f"capability:test-{index}.v1",
                    "phase": phase,
                    "occurred_at": "2026-07-20T00:00:00Z",
                    "result_ref": f"handler-result:{index}",
                    "attempt": "1",
                }
            )
    return tuple(values)


def test_accepts_one_fully_correlated_closed_cycle() -> None:
    report = validate_github_research_love_end_to_end(
        EndToEndAcceptanceCommand(
            repository="newicody/projects",
            issue_number=77,
            run_id="30000000001",
            fetch_cycle=_fetch(),
            prepared_report=_prepared(),
            completed_report=_completed(),
            temporal_observations=_observations(),
        )
    )

    assert report.valid is True
    assert report.status == "accepted"
    assert all(report.checks.values())
    assert report.evidence["observed_handler_count"] == 10
    assert report.to_mapping()["boundaries"]["vispy_remains_observation_only"] is True


def test_rejects_a_cross_run_digest_mismatch() -> None:
    completed = _completed()
    completed["input"] = {
        "repository": "newicody/projects",
        "run_id": "30000000001",
        "publication_plan_digest": "sha256:different",
    }

    report = validate_github_research_love_end_to_end(
        EndToEndAcceptanceCommand(
            repository="newicody/projects",
            issue_number=77,
            run_id="30000000001",
            fetch_cycle=_fetch(),
            prepared_report=_prepared(),
            completed_report=completed,
            temporal_observations=_observations(),
        )
    )

    assert report.valid is False
    assert report.status == "rejected"
    assert any("digest" in issue for issue in report.issues)
