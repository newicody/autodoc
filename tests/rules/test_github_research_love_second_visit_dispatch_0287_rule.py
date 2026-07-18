from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import context.github_research_love_second_visit_dispatch_0287 as module
from context.github_research_love_first_visit_dispatch_0287 import (
    GitHubResearchLoveFirstVisitDispatchResult,
    GitHubResearchLoveFirstVisitSurface,
    GitHubResearchLoveRuntimeResolver,
)
from context.github_research_love_second_visit_dispatch_0287 import (
    GitHubResearchLoveSecondVisitDispatchCommand,
    dispatch_second_love_visit_from_first_analysis,
)
from context.laboratory_framework_contract_0273 import (
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LABORATORY_VISIT_RESULT_SCHEMA,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
)
from context.love_study_contracts_0287 import (
    LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
    LOVE_STUDIES_LABORATORY_REF,
)
from context.native_love_laboratory_collaboration_scheduler_binding_0287 import (
    NativeLoveCollaborativeVisitRequestHandler,
)
from context.native_love_laboratory_second_specialist_0287 import (
    NATIVE_LOVE_COLLABORATION_PREPARATION_SCHEMA,
)
from contracts.event import EventType


def _first_visit() -> LaboratoryVisitRequest:
    return LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref="laboratory-visit:love-first-test",
        laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        objective_ref="specialist-task:love-first-test",
        source_candidate_ref="love-study:github-test",
        context_generation=0,
        input_contract_ref="contract:love.study_request.v1",
        expected_output_contract_ref=LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
        resource_budget=LaboratoryResourceBudget(),
        return_route_ref="route:github-research-test",
        context_refs=("ctx:github-research-test",),
        evidence_refs=("artifact:github-request-test",),
        conversation_ref="laboratory-conversation:github-research-test",
    )


def _first_result_mapping() -> dict[str, object]:
    visit = _first_visit()
    return {
        "schema": LABORATORY_VISIT_RESULT_SCHEMA,
        "visit_ref": visit.visit_ref,
        "laboratory_ref": visit.laboratory_ref,
        "specialist_ref": visit.specialist_ref,
        "status": "completed",
        "output_contract_ref": LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
        "machine_result": {
            "schema": "missipy.love.concept_affect_analysis.v1",
            "analysis_ref": "love-analysis:concept-test",
            "study_ref": visit.source_candidate_ref,
            "specialist_ref": visit.specialist_ref,
            "context_revision_ref": "ctx-result:revision-test",
            "findings": [],
            "concepts": ["attachement"],
            "affects": ["confiance"],
            "uncertainties": [],
            "contradictions": [],
            "limitations": ["Analyse limitée au texte fourni."],
            "recommendations": [],
            "evidence_refs": ["artifact:github-request-test"],
            "artifact_refs": [],
            "local_synthesis": "Première analyse locale.",
            "contribution_kind": "domain_analysis",
        },
        "human_representation": "Première analyse conceptuelle et affective.",
        "confidence": 0.75,
        "evidence_refs": ["artifact:github-request-test"],
        "assumptions": [],
        "requested_context_refs": [],
        "requested_specialist_refs": [],
        "requested_laboratory_refs": [],
        "followup_request_refs": [],
        "provenance_refs": ["ctx:github-research-test"],
        "conversation_ref": visit.conversation_ref,
        "parent_visit_ref": None,
    }


def _first_dispatch() -> GitHubResearchLoveFirstVisitDispatchResult:
    visit = _first_visit()
    surface = GitHubResearchLoveFirstVisitSurface(
        study=SimpleNamespace(to_mapping=lambda: {}),  # type: ignore[arg-type]
        first_task=SimpleNamespace(to_mapping=lambda: {}),  # type: ignore[arg-type]
        first_visit=visit,
    )
    return GitHubResearchLoveFirstVisitDispatchResult(
        valid=True,
        status="first-specialist-completed",
        issues=(),
        handler_action="registered",
        work_package_ref="research-work-package:test",
        route_request_id="request:test",
        route_event_id="event:test",
        surface=surface,
        scheduler_receipt={
            "execution": {
                "specialist_stage": "first_analysis",
                "result_valid": True,
                "validation_issues": [],
                "result": _first_result_mapping(),
            }
        },
    )


@pytest.mark.asyncio
async def test_second_visit_registers_first_artifact_and_uses_scheduler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolver = SimpleNamespace(
        register_concept_analysis=lambda analysis, artifact: None,
        register_task=lambda task: None,
    )
    handler = SimpleNamespace(
        provider=SimpleNamespace(resolver=resolver)
    )
    dispatcher = SimpleNamespace(
        handlers={EventType.LABORATORY_VISIT_REQUEST: handler}
    )
    ports = SimpleNamespace(
        scheduler=SimpleNamespace(running=True),
        dispatcher=dispatcher,
    )
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    monkeypatch.setattr(
        module,
        "_existing_runtime_resolver",
        lambda value: resolver,
    )

    preparation = SimpleNamespace(
        first_analysis=object(),
        first_artifact=object(),
        second_task=object(),
        second_visit=SimpleNamespace(
            visit_ref="laboratory-visit:love-second-test",
            parent_visit_ref="laboratory-visit:love-first-test",
        ),
        to_mapping=lambda: {
            "schema": NATIVE_LOVE_COLLABORATION_PREPARATION_SCHEMA,
            "second_visit_executed": False,
        },
    )
    monkeypatch.setattr(
        module,
        "_prepare_second_visit",
        lambda **kwargs: preparation,
    )

    captured: dict[str, object] = {}

    async def fake_submit(scheduler, request, **kwargs):
        captured["scheduler"] = scheduler
        captured["request"] = request
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            to_mapping=lambda: {
                "visit_ref": request.visit_ref,
                "execution": {
                    "specialist_stage": "second_analysis",
                    "result_valid": True,
                    "validation_issues": [],
                    "result": {
                        "specialist_ref": LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
                    },
                },
            }
        )

    monkeypatch.setattr(
        module,
        "submit_native_love_collaboration_visit",
        fake_submit,
    )

    result = await dispatch_second_love_visit_from_first_analysis(
        GitHubResearchLoveSecondVisitDispatchCommand(
            runtime_ports=ports,  # type: ignore[arg-type]
            first_dispatch=_first_dispatch(),
        )
    )
    mapping = result.to_mapping()

    assert result.valid is True
    assert result.status == "second-specialist-completed"
    assert captured["scheduler"] is ports.scheduler
    assert captured["request"] is preparation.second_visit
    assert mapping["first_analysis_artifact_registered"] is True
    assert mapping["second_task_registered"] is True
    assert mapping["direct_specialist_invocation"] is False
    assert mapping["second_specialist_execution_completed"] is True
    assert mapping["global_synthesis_created"] is False


@pytest.mark.asyncio
async def test_stopped_scheduler_is_not_started(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ports = SimpleNamespace(
        scheduler=SimpleNamespace(running=False),
        dispatcher=SimpleNamespace(handlers={}),
    )
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    preparation = SimpleNamespace(
        second_visit=SimpleNamespace(
            visit_ref="laboratory-visit:love-second-test",
            parent_visit_ref="laboratory-visit:love-first-test",
        ),
        to_mapping=lambda: {},
    )
    monkeypatch.setattr(
        module,
        "_prepare_second_visit",
        lambda **kwargs: preparation,
    )

    result = await dispatch_second_love_visit_from_first_analysis(
        GitHubResearchLoveSecondVisitDispatchCommand(
            runtime_ports=ports,  # type: ignore[arg-type]
            first_dispatch=_first_dispatch(),
        )
    )

    assert result.valid is False
    assert result.status == "scheduler-not-running"
    assert result.to_mapping()["scheduler_started"] is False


@pytest.mark.asyncio
async def test_invalid_first_analysis_is_rejected_before_second_submission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _first_dispatch()
    broken_receipt = dict(first.scheduler_receipt)
    broken_receipt["execution"] = {
        "specialist_stage": "first_analysis",
        "result_valid": False,
        "result": _first_result_mapping(),
    }
    first = GitHubResearchLoveFirstVisitDispatchResult(
        valid=first.valid,
        status=first.status,
        issues=first.issues,
        handler_action=first.handler_action,
        work_package_ref=first.work_package_ref,
        route_request_id=first.route_request_id,
        route_event_id=first.route_event_id,
        surface=first.surface,
        scheduler_receipt=broken_receipt,
    )
    ports = SimpleNamespace(
        scheduler=SimpleNamespace(running=True),
        dispatcher=SimpleNamespace(handlers={}),
    )
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    monkeypatch.setattr(
        module,
        "submit_native_love_collaboration_visit",
        lambda *args, **kwargs: pytest.fail(
            "second visit must not be submitted"
        ),
    )

    result = await dispatch_second_love_visit_from_first_analysis(
        GitHubResearchLoveSecondVisitDispatchCommand(
            runtime_ports=ports,  # type: ignore[arg-type]
            first_dispatch=first,
        )
    )

    assert result.valid is False
    assert result.status == "rejected"


def test_module_reuses_existing_collaboration_and_keeps_synthesis_separate() -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "prepare_second_specialist_collaboration(" in source
    assert "register_concept_analysis(" in source
    assert "register_task(" in source
    assert "submit_native_love_collaboration_visit(" in source
    assert "Scheduler(" not in source
    assert "Dispatcher(" not in source
    assert "EventBus(" not in source
    assert "scheduler.run(" not in source
    assert "execute_native_love_collaborative_visit(" not in source
    assert "global_synthesis_created" in source
