from __future__ import annotations

import sqlite3
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.github_research_scheduler_command_0287 import (  # noqa: E402
    ResearchExecutionBudget,
    build_typed_github_research_scheduler_command,
)
from context.github_research_scheduler_command_sql_authority_0287 import (  # noqa: E402
    DbApiGitHubResearchSchedulerCommandStore,
    GitHubResearchSchedulerCommandSqlAuthorityError,
)


def _intake() -> dict[str, object]:
    repository = "newicody/projects"
    run_id = "29673341210"
    issue_number = 54
    repository_key = "newicody-projects"
    policy_decision_id = (
        "policy-decision:github-research-auto:bc375aafe1206a60e39b1e9e"
    )
    route_id = (
        "route-github-research-laboratory-a681c7356d4ea43e433a7cb5"
    )
    task_id = "task-github-research-a681c7356d4ea43e433a7cb5"
    requested_at = "2026-07-19T06:11:32Z"
    candidate = {
        "schema": "missipy.github.research_laboratory_route_candidate.v1",
        "admissibility_digest": (
            "a681c7356d4ea43e433a7cb50ffa581532091cd29a628d8e18492b7cc4dfd1de"
        ),
        "context_generation": 0,
        "context_refs": [
            f"github-actions-ready-run:{repository_key}:{run_id}"
        ],
        "conversation_ref": (
            f"github-research-conversation:{repository_key}:"
            f"{issue_number}:{run_id}"
        ),
        "evidence_refs": [
            f"github-actions-artifact:{repository_key}:{run_id}:8438033314",
            f"github-actions-artifact:{repository_key}:{run_id}:8438033380",
            f"github-actions-artifact:{repository_key}:{run_id}:8438033437",
        ],
        "issue_number": issue_number,
        "parent_event_ref": "",
        "repository": repository,
        "request_mode": "initial",
        "requested_status": "Recherche",
        "return_route_ref": (
            f"github-issue-return:{repository_key}:{issue_number}"
        ),
        "route_candidate_ref": (
            "research-route-candidate:a681c7356d4ea43e433a7cb5"
        ),
        "run_id": run_id,
        "work_package_ref": "research-work-package:b30f73efd0284f04a27882f9",
    }
    route_request = {
        "schema": "missipy.scheduler.route_adapter_request.v1",
        "request_id": (
            "request-scheduler-candidate-github-research-"
            "a681c7356d4ea43e433a7cb5"
        ),
        "route_id": route_id,
        "task_id": task_id,
        "holder": "scheduler",
        "scope": "route.write",
        "authorized": True,
        "policy_decision_id": policy_decision_id,
        "ttl_seconds": 300,
        "activate": True,
        "requested_at": requested_at,
    }
    intake_candidate = {
        "schema": "missipy.github_artifact.scheduler_intake_candidate.v1",
        "repository": repository,
        "run_id": run_id,
        "policy_decision_id": policy_decision_id,
        "dataset_root_ref": candidate["work_package_ref"],
        "observation_ref": candidate["route_candidate_ref"],
        "route_id": route_id,
        "task_id": task_id,
        "requested_at": requested_at,
        "authorized": True,
        "scheduler_route_request_ready": True,
        "status": "planned",
        "priority": 60,
    }
    return {
        "schema": "missipy.github.research_scheduler_intake_report.v1",
        "valid": True,
        "status": "scheduler-requests-ready",
        "results": [
            {
                "schema": "missipy.github.research_scheduler_intake.v1",
                "valid": True,
                "authorized": True,
                "status": "scheduler-request-ready",
                "scheduler_dispatch_started": False,
                "laboratory_execution_started": False,
                "research_route_candidate": candidate,
                "policy_decision": {
                    "schema": (
                        "missipy.github."
                        "research_automatic_scheduler_policy_decision.v1"
                    ),
                    "policy_decision_id": policy_decision_id,
                    "policy_ref": "policy:github-research:auto-scheduler:r16-r8",
                    "decision_digest": (
                        "bc375aafe1206a60e39b1e9e4053d8dc"
                        "1de63b570788e7c6f47cbf8f0c1e981f"
                    ),
                    "decision": "approve",
                    "automatic": True,
                },
                "scheduler_route_request": route_request,
                "scheduler_intake_plan": {
                    "schema": "missipy.github_artifact.scheduler_intake_plan.v1",
                    "authorized": True,
                    "calls_handle_scheduler_route_request": False,
                    "candidate": intake_candidate,
                },
            }
        ],
    }


def _command(*, max_steps: int = 16):
    result = build_typed_github_research_scheduler_command(
        scheduler_intake_report=_intake(),
        execution_budget=ResearchExecutionBudget(
            max_scheduler_steps=max_steps,
            max_specialist_visits=2,
            max_wall_time_s=1800,
        ),
    )
    assert result.valid is True
    assert result.command is not None
    return result.command


def _store():
    connection = sqlite3.connect(":memory:")
    store = DbApiGitHubResearchSchedulerCommandStore(connection)
    store.initialize_schema()
    return connection, store


def test_round_trip_reconstructs_same_typed_command() -> None:
    _connection, store = _store()
    command = _command()
    result = store.put_command(command)
    assert result.inserted is True
    assert result.idempotent_replay is False
    assert store.get_command(command.command_ref) == command
    state = store.get_state(command.command_ref)
    assert state is not None
    assert state.state == "pending"
    assert state.state_version == 1
    assert store.list_pending_command_refs() == (command.command_ref,)


def test_exact_replay_is_idempotent() -> None:
    _connection, store = _store()
    command = _command()
    store.put_command(command)
    replay = store.put_command(command)
    assert replay.inserted is False
    assert replay.idempotent_replay is True


def test_second_command_for_same_github_run_rolls_back() -> None:
    connection, store = _store()
    first = _command(max_steps=16)
    second = _command(max_steps=17)
    store.put_command(first)
    with pytest.raises(
        GitHubResearchSchedulerCommandSqlAuthorityError,
        match="SQL insertion failed",
    ):
        store.put_command(second)
    assert store.get_command(second.command_ref) is None
    count = connection.execute("SELECT COUNT(*) FROM scheduler_commands").fetchone()
    assert count == (1,)


def test_schema_contains_no_json_authority_column() -> None:
    connection, _store_instance = _store()
    rows = connection.execute(
        "SELECT name, sql FROM sqlite_master "
        "WHERE type = 'table' AND name LIKE 'scheduler_command%'"
    ).fetchall()
    assert rows
    ddl = "\n".join(str(row[1]).lower() for row in rows)
    assert "json" not in ddl
    assert "payload_json" not in ddl
    assert "metadata_json" not in ddl


def test_pending_order_uses_priority_then_issued_time() -> None:
    _connection, store = _store()
    command = _command()
    store.put_command(command)
    assert store.list_pending_command_refs(limit=1) == (command.command_ref,)
