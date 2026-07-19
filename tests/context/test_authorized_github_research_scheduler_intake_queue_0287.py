from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.authorized_route_request_queue import (
    AuthorizedRouteRequestQueueError,
    append_authorized_github_research_scheduler_intake,
    iter_authorized_route_request_queue,
)


def _intake_report(*, route_id: str = "route-github-research-laboratory-a681c735") -> dict[str, object]:
    policy_id = "policy-decision:github-research-auto:bc375aafe1206a60e39b1e9e"
    request = {
        "schema": "missipy.scheduler.route_adapter_request.v1",
        "request_id": "request-scheduler-candidate-github-research-a681c735",
        "route_id": route_id,
        "task_id": "task-github-research-a681c735",
        "policy_decision_id": policy_id,
        "holder": "scheduler",
        "scope": "route.write",
        "authorized": True,
        "activate": True,
        "ttl_seconds": 300,
        "requested_at": "2026-07-19T06:11:32Z",
    }
    return {
        "schema": "missipy.github.research_scheduler_intake_report.v1",
        "valid": True,
        "status": "scheduler-requests-ready",
        "results": [
            {
                "schema": "missipy.github.research_scheduler_intake.v1",
                "valid": True,
                "status": "scheduler-request-ready",
                "authorized": True,
                "scheduler_dispatch_started": False,
                "laboratory_execution_started": False,
                "research_route_candidate": {
                    "repository": "newicody/projects",
                    "run_id": "29673341210",
                },
                "policy_decision": {
                    "decision": "approve",
                    "automatic": True,
                    "policy_decision_id": policy_id,
                },
                "scheduler_route_request": request,
            }
        ],
    }


def _append(tmp_path: Path, report: dict[str, object]):
    return append_authorized_github_research_scheduler_intake(
        scheduler_intake_report=report,
        runtime_root=tmp_path,
        policy_decision_id=(
            "policy-decision:github-research-auto:bc375aafe1206a60e39b1e9e"
        ),
        repository="newicody/projects",
        run_id="29673341210",
    )


def test_queues_one_authorized_request_without_execution(tmp_path: Path) -> None:
    result = _append(tmp_path, _intake_report())

    assert result.valid is True
    assert result.status == "queued-for-canonical-scheduler"
    assert result.action == "queued"
    assert result.queued_count == 1
    assert result.replayed_count == 0
    assert result.scheduler_started is False
    assert result.dispatcher_used is False
    assert result.eventbus_used is False
    assert result.handler_called is False

    queued = list(iter_authorized_route_request_queue(result.queue_path))
    assert len(queued) == 1
    assert queued[0].request_id == result.request_id
    assert queued[0].policy_decision_id == result.policy_decision_id


def test_exact_replay_is_idempotent(tmp_path: Path) -> None:
    first = _append(tmp_path, _intake_report())
    second = _append(tmp_path, _intake_report())

    assert first.action == "queued"
    assert second.status == "already-queued"
    assert second.action == "replay"
    assert second.queued_count == 0
    assert second.replayed_count == 1
    assert Path(second.queue_path).read_text(encoding="utf-8").count("\n") == 1


def test_same_request_id_with_different_payload_is_rejected(tmp_path: Path) -> None:
    _append(tmp_path, _intake_report())

    with pytest.raises(
        AuthorizedRouteRequestQueueError,
        match="request_id collision",
    ):
        _append(tmp_path, _intake_report(route_id="route-github-research-other"))


def test_explicit_repository_run_and_policy_are_required(tmp_path: Path) -> None:
    report = _intake_report()

    with pytest.raises(AuthorizedRouteRequestQueueError, match="repository mismatch"):
        append_authorized_github_research_scheduler_intake(
            scheduler_intake_report=report,
            runtime_root=tmp_path,
            policy_decision_id=(
                "policy-decision:github-research-auto:bc375aafe1206a60e39b1e9e"
            ),
            repository="newicody/other",
            run_id="29673341210",
        )


def test_queue_line_is_canonical_json(tmp_path: Path) -> None:
    result = _append(tmp_path, _intake_report())
    line = Path(result.queue_path).read_text(encoding="utf-8").strip()

    assert json.dumps(json.loads(line), sort_keys=True, separators=(",", ":")) == line
