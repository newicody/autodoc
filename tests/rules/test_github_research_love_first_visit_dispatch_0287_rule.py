from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import context.github_research_love_first_visit_dispatch_0287 as module
from context.correlated_research_work_package_0287 import WORK_PACKAGE_SCHEMA
from context.github_research_love_first_visit_dispatch_0287 import (
    GitHubResearchLoveFirstVisitDispatchCommand,
    GitHubResearchLoveRuntimeResolver,
    build_first_love_visit_surface_from_github_research,
    dispatch_first_love_visit_from_github_research,
)
from context.github_research_scheduler_dispatch_0287 import (
    SCHEMA as DISPATCH_SCHEMA,
)
from context.github_research_scheduler_intake_0287 import (
    SCHEMA as INTAKE_SCHEMA,
)
from context.love_study_contracts_0287 import (
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_STUDIES_LABORATORY_REF,
)
from contracts.event import EventType


def _work_package() -> dict[str, object]:
    return {
        "schema": WORK_PACKAGE_SCHEMA,
        "work_package_ref": "research-work-package:test-15",
        "repository": "newicody/projects",
        "run_id": "29622831972",
        "source_issue": {
            "number": 15,
            "url": "https://github.com/newicody/projects/issues/15",
        },
        "source_candidate_ref": "source-candidate:test-15",
        "conversation_ref": "github-research-conversation:test",
        "return_route_ref": "github-issue-return:test",
        "context_generation": 0,
        "authoritative_request": {
            "title": "Étudier la notion d'amour",
            "body": "Analyser les concepts, affects et dynamiques décrits.",
        },
        "copilot_advisory": {
            "schema": "missipy.github.copilot_advisory.v2",
        },
        "advisory_present": True,
        "request_authoritative": True,
        "advisory_used_as_hint_only": True,
    }


def _intake() -> dict[str, object]:
    decision = "policy-decision:github-research-auto:test"
    return {
        "schema": INTAKE_SCHEMA,
        "valid": True,
        "authorized": True,
        "status": "scheduler-request-ready",
        "research_route_candidate": {
            "route_candidate_ref": "research-route-candidate:test",
            "work_package_ref": "research-work-package:test-15",
            "repository": "newicody/projects",
            "run_id": "29622831972",
            "issue_number": 15,
        },
        "scheduler_route_request": {
            "request_id": "request:test",
            "route_id": "route:test",
            "task_id": "task:test",
            "policy_decision_id": decision,
        },
        "scheduler_dispatch_started": False,
        "laboratory_execution_started": False,
    }


def _dispatch() -> dict[str, object]:
    return {
        "schema": DISPATCH_SCHEMA,
        "valid": True,
        "status": "route-ready",
        "request_id": "request:test",
        "event_id": "event:test",
        "policy_decision_id": "policy-decision:github-research-auto:test",
        "route_reply": {
            "request_id": "request:test",
            "route_id": "route:test",
            "task_id": "task:test",
            "status": "ready",
        },
        "laboratory_execution_started": False,
    }


def _ports(dispatcher: object | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        scheduler=SimpleNamespace(running=True),
        dispatcher=dispatcher or SimpleNamespace(handlers={}),
        base_revision_ref="context-revision:test",
    )


def test_first_surface_uses_authoritative_request_and_known_specialist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ports = _ports()
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    surface = build_first_love_visit_surface_from_github_research(
        runtime_ports=ports,  # type: ignore[arg-type]
        work_package=_work_package(),
        scheduler_intake=_intake(),
        scheduler_dispatch=_dispatch(),
    )

    assert surface.study.objective == "Étudier la notion d'amour"
    assert surface.study.subject_text.startswith("Analyser les concepts")
    assert surface.first_task.specialist_ref == LOVE_CONCEPT_AFFECT_SPECIALIST_REF
    assert surface.first_visit.laboratory_ref == LOVE_STUDIES_LABORATORY_REF
    assert surface.first_visit.objective_ref == surface.first_task.task_ref
    assert surface.first_visit.source_candidate_ref == surface.study.study_ref


@pytest.mark.asyncio
async def test_first_visit_is_submitted_through_existing_scheduler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Dispatcher:
        def __init__(self) -> None:
            self.handlers: dict[object, object] = {}

        def register(self, event_type: object, handler: object) -> None:
            self.handlers[event_type] = handler

    dispatcher = Dispatcher()
    ports = _ports(dispatcher)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    captured: dict[str, object] = {}

    async def fake_submit(scheduler, request, **kwargs):
        captured["scheduler"] = scheduler
        captured["request"] = request
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            to_mapping=lambda: {
                "schema": "missipy.love.collaboration_scheduler_receipt.v1",
                "visit_ref": request.visit_ref,
                "execution": {
                    "specialist_stage": "first_analysis",
                    "result_valid": True,
                    "validation_issues": [],
                    "result": {
                        "schema": "missipy.laboratory.visit_result.v1",
                        "visit_ref": request.visit_ref,
                    },
                },
            }
        )

    monkeypatch.setattr(
        module,
        "submit_native_love_collaboration_visit",
        fake_submit,
    )

    result = await dispatch_first_love_visit_from_github_research(
        GitHubResearchLoveFirstVisitDispatchCommand(
            runtime_ports=ports,  # type: ignore[arg-type]
            work_package=_work_package(),
            scheduler_intake=_intake(),
            scheduler_dispatch=_dispatch(),
        )
    )
    mapping = result.to_mapping()

    assert result.valid is True
    assert result.status == "first-specialist-completed"
    assert result.handler_action == "registered"
    assert EventType.LABORATORY_VISIT_REQUEST in dispatcher.handlers
    assert captured["scheduler"] is ports.scheduler
    assert mapping["direct_specialist_invocation"] is False
    assert mapping["laboratory_execution_completed"] is True
    assert mapping["first_specialist_execution_completed"] is True
    assert mapping["second_specialist_execution_started"] is False


@pytest.mark.asyncio
async def test_second_issue_reuses_handler_and_appends_study(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Dispatcher:
        def __init__(self) -> None:
            self.handlers: dict[object, object] = {}

        def register(self, event_type: object, handler: object) -> None:
            self.handlers[event_type] = handler

    dispatcher = Dispatcher()
    ports = _ports(dispatcher)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    async def fake_submit(scheduler, request, **kwargs):
        return SimpleNamespace(
            to_mapping=lambda: {
                "execution": {
                    "specialist_stage": "first_analysis",
                    "result_valid": True,
                    "validation_issues": [],
                    "result": {"visit_ref": request.visit_ref},
                }
            }
        )

    monkeypatch.setattr(
        module,
        "submit_native_love_collaboration_visit",
        fake_submit,
    )

    first = await dispatch_first_love_visit_from_github_research(
        GitHubResearchLoveFirstVisitDispatchCommand(
            runtime_ports=ports,  # type: ignore[arg-type]
            work_package=_work_package(),
            scheduler_intake=_intake(),
            scheduler_dispatch=_dispatch(),
        )
    )
    second_package = _work_package()
    second_package["work_package_ref"] = "research-work-package:test-16"
    second_package["run_id"] = "run-16"
    second_package["source_issue"] = {
        "number": 16,
        "url": "https://github.com/newicody/projects/issues/16",
    }
    second_package["source_candidate_ref"] = "source-candidate:test-16"
    second_intake = _intake()
    second_intake["research_route_candidate"] = {
        "route_candidate_ref": "research-route-candidate:test-16",
        "work_package_ref": "research-work-package:test-16",
        "repository": "newicody/projects",
        "run_id": "run-16",
        "issue_number": 16,
    }

    second = await dispatch_first_love_visit_from_github_research(
        GitHubResearchLoveFirstVisitDispatchCommand(
            runtime_ports=ports,  # type: ignore[arg-type]
            work_package=second_package,
            scheduler_intake=second_intake,
            scheduler_dispatch=_dispatch(),
        )
    )

    assert first.handler_action == "registered"
    assert second.handler_action == "replay"
    handler = dispatcher.handlers[EventType.LABORATORY_VISIT_REQUEST]
    assert isinstance(
        handler.provider.resolver,
        GitHubResearchLoveRuntimeResolver,
    )
    assert len(handler.provider.resolver._studies) == 2
    assert len(handler.provider.resolver._tasks) == 2


@pytest.mark.asyncio
async def test_stopped_scheduler_is_not_started(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ports = _ports()
    ports.scheduler.running = False
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    result = await dispatch_first_love_visit_from_github_research(
        GitHubResearchLoveFirstVisitDispatchCommand(
            runtime_ports=ports,  # type: ignore[arg-type]
            work_package=_work_package(),
            scheduler_intake=_intake(),
            scheduler_dispatch=_dispatch(),
        )
    )

    assert result.valid is False
    assert result.status == "scheduler-not-running"
    assert result.to_mapping()["scheduler_started"] is False


def test_module_keeps_scheduler_as_only_orchestrator() -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "submit_native_love_collaboration_visit(" in source
    assert "register_native_love_collaboration_visit_handler(" in source
    assert "execute_native_love_collaborative_visit(" not in source
    assert ".execute(" not in source
    assert "Scheduler(" not in source
    assert "Dispatcher(" not in source
    assert "EventBus(" not in source
    assert "scheduler.run(" not in source
    assert "prepare_second_specialist_collaboration(" not in source
    assert "global_synthesis_created" in source
