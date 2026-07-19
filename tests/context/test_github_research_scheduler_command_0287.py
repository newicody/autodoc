from __future__ import annotations

from context.github_research_scheduler_command_0287 import (
    AuthorizedSchedulerCommand,
    GitHubResearchSchedulerCommand,
    ResearchExecutionBudget,
    SchedulerCommand,
    build_typed_github_research_scheduler_command,
)


def _report() -> dict[str, object]:
    digest = "a" * 64
    policy_digest = "b" * 64
    policy_id = "policy-decision:github-research-auto:bbbbbbbbbbbbbbbbbbbbbbbb"
    requested_at = "2026-07-19T06:11:32Z"
    route_id = "route-github-research-laboratory-aaaaaaaa"
    task_id = "task-github-research-aaaaaaaa"
    work_package_ref = "research-work-package:b30f73efd0284f04a27882f9"
    route_candidate_ref = "research-route-candidate:a681c7356d4ea43e433a7cb5"
    route = {
        "schema": "missipy.scheduler.route_adapter_request.v1",
        "request_id": "request-scheduler-candidate-github-research-aaaaaaaa",
        "route_id": route_id,
        "task_id": task_id,
        "policy_decision_id": policy_id,
        "holder": "scheduler",
        "scope": "route.write",
        "authorized": True,
        "activate": True,
        "ttl_seconds": 300,
        "requested_at": requested_at,
    }
    candidate = {
        "schema": "missipy.github.research_laboratory_route_candidate.v1",
        "repository": "newicody/projects",
        "issue_number": 54,
        "run_id": "29673341210",
        "requested_status": "Recherche",
        "request_mode": "initial",
        "parent_event_ref": "",
        "work_package_ref": work_package_ref,
        "route_candidate_ref": route_candidate_ref,
        "conversation_ref": (
            "github-research-conversation:newicody-projects:54:29673341210"
        ),
        "return_route_ref": "github-issue-return:newicody-projects:54",
        "context_generation": 0,
        "context_refs": [
            "github-actions-ready-run:newicody-projects:29673341210"
        ],
        "evidence_refs": [
            "github-actions-artifact:newicody-projects:29673341210:8438033314",
            "github-actions-artifact:newicody-projects:29673341210:8438033380",
            "github-actions-artifact:newicody-projects:29673341210:8438033437",
        ],
        "admissibility_digest": digest,
    }
    policy = {
        "schema": "missipy.github.research_automatic_scheduler_policy_decision.v1",
        "policy_decision_id": policy_id,
        "policy_ref": "policy:github-research:auto-scheduler:r16-r8",
        "decision": "approve",
        "automatic": True,
        "decision_digest": policy_digest,
    }
    intake_plan = {
        "schema": "missipy.github_artifact.scheduler_intake_plan.v1",
        "authorized": True,
        "calls_handle_scheduler_route_request": False,
        "candidate": {
            "schema": "missipy.github_artifact.scheduler_intake_candidate.v1",
            "artifact_id": "research-i54-aaaaaaaaaaaaaaaa",
            "authorized": True,
            "candidate_ref": "scheduler-candidate-github-research-aaaaaaaa",
            "dataset_root_ref": work_package_ref,
            "observation_only_source": True,
            "observation_ref": route_candidate_ref,
            "policy_decision_id": policy_id,
            "priority": 60,
            "repository": "newicody/projects",
            "requested_at": requested_at,
            "route_id": route_id,
            "run_id": "29673341210",
            "scheduler_modified": False,
            "scheduler_route_request_ready": True,
            "status": "planned",
            "task_id": task_id,
        },
    }
    result = {
        "schema": "missipy.github.research_scheduler_intake.v1",
        "valid": True,
        "authorized": True,
        "status": "scheduler-request-ready",
        "scheduler_dispatch_started": False,
        "laboratory_execution_started": False,
        "research_route_candidate": candidate,
        "policy_decision": policy,
        "scheduler_route_request": route,
        "scheduler_intake_plan": intake_plan,
    }
    return {
        "schema": "missipy.github.research_scheduler_intake_report.v1",
        "valid": True,
        "status": "scheduler-requests-ready",
        "results": [result],
    }


def _budget() -> ResearchExecutionBudget:
    return ResearchExecutionBudget(
        max_scheduler_steps=16,
        max_specialist_visits=2,
        max_wall_time_s=1800.0,
    )


def test_builds_typed_inheritance_and_composition_without_io() -> None:
    result = build_typed_github_research_scheduler_command(
        scheduler_intake_report=_report(),
        execution_budget=_budget(),
    )

    assert result.valid is True
    assert result.status == "typed-command-ready-for-sql"
    assert isinstance(result.command, GitHubResearchSchedulerCommand)
    assert isinstance(result.command, AuthorizedSchedulerCommand)
    assert isinstance(result.command, SchedulerCommand)
    assert result.command.correlation.repository == "newicody/projects"
    assert result.command.correlation.issue_number == 54
    assert result.command.research.work_package_ref.startswith(
        "research-work-package:"
    )
    assert len(result.command.research.evidence_refs) == 3
    assert result.command.execution_budget.max_specialist_visits == 2
    assert result.command.route_request.authorized is True
    assert result.command.issued_at == result.command.route_request.requested_at
    assert result.command.command_ref.endswith(
        result.command.command_digest.removeprefix("sha256:")[:24]
    )

    boundaries = result.to_mapping()["boundaries"]
    assert boundaries["legacy_filesystem_handoff_is_canonical"] is False
    assert boundaries["filesystem_write_performed"] is False
    assert boundaries["sql_write_performed"] is False
    assert boundaries["dispatcher_called"] is False


def test_command_digest_is_deterministic_and_correlation_sensitive() -> None:
    first = build_typed_github_research_scheduler_command(
        scheduler_intake_report=_report(),
        execution_budget=_budget(),
    )
    replay = build_typed_github_research_scheduler_command(
        scheduler_intake_report=_report(),
        execution_budget=_budget(),
    )
    changed_report = _report()
    changed_candidate = changed_report["results"][0]["research_route_candidate"]
    changed_candidate["run_id"] = "29673341211"
    changed_candidate["conversation_ref"] = (
        "github-research-conversation:newicody-projects:54:29673341211"
    )
    changed_candidate["context_refs"] = [
        "github-actions-ready-run:newicody-projects:29673341211"
    ]
    changed_candidate["evidence_refs"] = [
        "github-actions-artifact:newicody-projects:29673341211:8438033314",
        "github-actions-artifact:newicody-projects:29673341211:8438033380",
        "github-actions-artifact:newicody-projects:29673341211:8438033437",
    ]
    changed_report["results"][0]["scheduler_intake_plan"]["candidate"][
        "run_id"
    ] = "29673341211"
    changed = build_typed_github_research_scheduler_command(
        scheduler_intake_report=changed_report,
        execution_budget=_budget(),
    )

    assert first.command is not None
    assert replay.command is not None
    assert changed.command is not None
    assert first.command.command_digest == replay.command.command_digest
    assert first.command.command_digest != changed.command.command_digest


def test_budget_changes_command_identity() -> None:
    first = build_typed_github_research_scheduler_command(
        scheduler_intake_report=_report(),
        execution_budget=_budget(),
    )
    second = build_typed_github_research_scheduler_command(
        scheduler_intake_report=_report(),
        execution_budget=ResearchExecutionBudget(
            max_scheduler_steps=12,
            max_specialist_visits=2,
            max_wall_time_s=1800.0,
        ),
    )

    assert first.command is not None
    assert second.command is not None
    assert first.command.command_digest != second.command.command_digest


def test_rejects_duplicate_evidence_refs() -> None:
    report = _report()
    candidate = report["results"][0]["research_route_candidate"]
    candidate["evidence_refs"] = [candidate["evidence_refs"][0]] * 2

    result = build_typed_github_research_scheduler_command(
        scheduler_intake_report=report,
        execution_budget=_budget(),
    )

    assert result.valid is False
    assert "must not contain duplicates" in result.issues[0]


def test_rejects_inconsistent_intake_plan() -> None:
    report = _report()
    report["results"][0]["scheduler_intake_plan"]["candidate"][
        "dataset_root_ref"
    ] = "research-work-package:different"

    result = build_typed_github_research_scheduler_command(
        scheduler_intake_report=report,
        execution_budget=_budget(),
    )

    assert result.valid is False
    assert "dataset_root_ref mismatch" in result.issues[0]
