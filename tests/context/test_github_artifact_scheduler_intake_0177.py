import pytest

from context.github_artifact_scheduler_intake import (
    GITHUB_ARTIFACT_SCHEDULER_INTAKE_CANDIDATE_SCHEMA,
    GithubArtifactSchedulerIntakeError,
    build_github_artifact_scheduler_intake_candidate,
    build_github_artifact_scheduler_intake_plan,
)
from runtime.scheduler_route_adapter import SCHEDULER_ROUTE_REQUEST_SCHEMA, SchedulerRouteRequest


def _raw() -> dict[str, object]:
    return {
        "observation_ref": "event:github-artifact-dataset:newicody:run0177",
        "repository": "newicody/autodoc-ideas",
        "run_id": "run0177",
        "artifact_id": "artifact0177",
        "dataset_root_ref": "server-dataset:github-artifacts",
        "status": "queued",
        "priority": 55,
        "requested_at": "2026-07-07T00:00:00Z",
    }


def test_0177_builds_unauthorized_scheduler_intake_candidate() -> None:
    candidate = build_github_artifact_scheduler_intake_candidate(_raw())

    assert candidate.schema == GITHUB_ARTIFACT_SCHEDULER_INTAKE_CANDIDATE_SCHEMA
    assert candidate.authorized is False
    assert candidate.policy_decision_id is None
    assert candidate.scheduler_route_request_ready is False
    assert candidate.scheduler_modified is False
    assert candidate.route_id.startswith("route-")


def test_0177_plan_without_policy_does_not_emit_scheduler_route_request() -> None:
    plan = build_github_artifact_scheduler_intake_plan(_raw())

    mapping = plan.to_mapping()
    assert mapping["authorized"] is False
    assert mapping["scheduler_route_request"] is None
    assert mapping["uses_existing_scheduler_route_adapter"] is True
    assert mapping["calls_handle_scheduler_route_request"] is False


def test_0177_authorized_plan_uses_existing_scheduler_route_request_mapping() -> None:
    plan = build_github_artifact_scheduler_intake_plan(
        _raw(),
        policy_decision_id="policy:allow:github-artifact:0177",
        authorized=True,
    )

    assert plan.authorized is True
    assert plan.scheduler_route_request is not None
    assert plan.scheduler_route_request["schema"] == SCHEDULER_ROUTE_REQUEST_SCHEMA
    parsed = SchedulerRouteRequest.from_mapping(plan.scheduler_route_request)
    assert parsed.authorized is True
    assert parsed.policy_decision_id == "policy:allow:github-artifact:0177"


def test_0177_rejects_authorized_candidate_without_policy() -> None:
    with pytest.raises(GithubArtifactSchedulerIntakeError, match="policy_decision_id"):
        build_github_artifact_scheduler_intake_plan(_raw(), authorized=True)
