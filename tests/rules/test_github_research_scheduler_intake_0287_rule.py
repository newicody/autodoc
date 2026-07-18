from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import context.github_research_scheduler_intake_0287 as module
from context.github_research_scheduler_intake_0287 import (
    GitHubResearchAutomaticSchedulerPolicy,
    GitHubResearchSchedulerIntakeCommand,
    build_authorized_scheduler_intake_for_admissible_research,
)
from context.github_research_work_package_admissibility_0287 import (
    ROUTE_CANDIDATE_SCHEMA,
)


def _candidate() -> dict[str, object]:
    return {
        "schema": ROUTE_CANDIDATE_SCHEMA,
        "route_candidate_ref": "research-route-candidate:abc",
        "work_package_ref": "research-work-package:abc",
        "repository": "newicody/projects",
        "run_id": "29622831972",
        "issue_number": 15,
        "requested_status": "Recherche",
        "request_mode": "initial",
        "parent_event_ref": "",
        "conversation_ref": "conversation:abc",
        "return_route_ref": "return:abc",
        "context_generation": 0,
        "context_refs": ["context:abc"],
        "evidence_refs": ["evidence:abc"],
        "admissibility_digest": "a" * 64,
        "scheduler_command_created": False,
        "scheduler_dispatch_started": False,
        "laboratory_execution_started": False,
    }


def test_admissible_research_reuses_existing_authorized_intake(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_builder(raw, *, policy_decision_id, authorized):
        captured["raw"] = dict(raw)
        captured["policy_decision_id"] = policy_decision_id
        captured["authorized"] = authorized
        return SimpleNamespace(
            to_mapping=lambda: {
                "authorized": True,
                "scheduler_route_request": {
                    "schema": "missipy.scheduler.route_request.v1",
                    "authorized": True,
                    "policy_decision_id": policy_decision_id,
                },
                "uses_existing_scheduler_route_adapter": True,
                "scheduler_modified": False,
            }
        )

    monkeypatch.setattr(
        module,
        "build_github_artifact_scheduler_intake_plan",
        fake_builder,
    )
    result = build_authorized_scheduler_intake_for_admissible_research(
        GitHubResearchSchedulerIntakeCommand(
            route_candidate=_candidate(),
            requested_at="2026-07-18T12:00:00Z",
        )
    )
    mapping = result.to_mapping()

    assert result.valid is True
    assert result.authorized is True
    assert result.status == "scheduler-request-ready"
    assert captured["authorized"] is True
    assert str(captured["policy_decision_id"]).startswith(
        "policy-decision:github-research-auto:"
    )
    assert captured["raw"]["status"] == "planned"
    assert mapping["existing_scheduler_intake_reused"] is True
    assert mapping["existing_scheduler_route_adapter_reused"] is True
    assert mapping["scheduler_command_created"] is True
    assert mapping["scheduler_dispatch_started"] is False
    assert mapping["laboratory_execution_started"] is False


def test_policy_decision_is_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decisions: list[str] = []

    def fake_builder(raw, *, policy_decision_id, authorized):
        decisions.append(policy_decision_id)
        return SimpleNamespace(
            to_mapping=lambda: {
                "authorized": True,
                "scheduler_route_request": {
                    "authorized": True,
                    "policy_decision_id": policy_decision_id,
                },
            }
        )

    monkeypatch.setattr(
        module,
        "build_github_artifact_scheduler_intake_plan",
        fake_builder,
    )
    command = GitHubResearchSchedulerIntakeCommand(
        route_candidate=_candidate(),
        requested_at="2026-07-18T12:00:00Z",
    )
    first = build_authorized_scheduler_intake_for_admissible_research(command)
    second = build_authorized_scheduler_intake_for_admissible_research(command)

    assert first.valid is True
    assert second.valid is True
    assert decisions[0] == decisions[1]


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("repository", "newicody/autodoc"),
        ("requested_status", "En cours"),
        ("scheduler_dispatch_started", True),
        ("laboratory_execution_started", True),
        ("admissibility_digest", "invalid"),
    ),
)
def test_invalid_or_already_started_candidate_is_rejected(
    field: str,
    value: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module,
        "build_github_artifact_scheduler_intake_plan",
        lambda *args, **kwargs: pytest.fail("existing intake must not be called"),
    )
    candidate = _candidate()
    candidate[field] = value

    result = build_authorized_scheduler_intake_for_admissible_research(
        GitHubResearchSchedulerIntakeCommand(
            route_candidate=candidate,
            requested_at="2026-07-18T12:00:00Z",
        )
    )

    assert result.valid is False
    assert result.authorized is False
    assert result.status == "rejected"


def test_disabled_policy_rejects_without_building_route_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module,
        "build_github_artifact_scheduler_intake_plan",
        lambda *args, **kwargs: pytest.fail("existing intake must not be called"),
    )
    result = build_authorized_scheduler_intake_for_admissible_research(
        GitHubResearchSchedulerIntakeCommand(
            route_candidate=_candidate(),
            requested_at="2026-07-18T12:00:00Z",
            policy=GitHubResearchAutomaticSchedulerPolicy(enabled=False),
        )
    )

    assert result.valid is False
    assert "disabled" in result.issues[0]


def test_r16_r8_does_not_dispatch_or_import_scheduler_runtime() -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "build_github_artifact_scheduler_intake_plan" in source
    assert "from kernel.scheduler" not in source
    assert "Scheduler(" not in source
    assert ".emit(" not in source
    assert "handle_scheduler_route_request(" not in source
    assert "laboratory_execution_started" in source
