from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import context.github_research_love_complete_closed_loop_0287 as module
from context.github_research_love_complete_closed_loop_0287 import (
    GitHubResearchLoveClosedLoopCompleteCommand,
    GitHubResearchLoveClosedLoopPrepareCommand,
    complete_github_research_love_closed_loop,
    prepare_github_research_love_closed_loop,
)


class Stage:
    def __init__(
        self,
        *,
        valid: bool = True,
        status: str = "ok",
        issues: tuple[str, ...] = (),
        **values,
    ) -> None:
        self.valid = valid
        self.status = status
        self.issues = issues
        for name, value in values.items():
            setattr(self, name, value)

    def to_mapping(self):
        mapping = {
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
        }
        for name, value in self.__dict__.items():
            if name not in {"valid", "status", "issues"}:
                mapping[name] = value
        return mapping


def _patch_command_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    names = (
        "GitHubReadyRunResearchAdmissibilityCommand",
        "GitHubResearchSchedulerIntakeCommand",
        "GitHubResearchSchedulerDispatchCommand",
        "GitHubResearchLoveFirstVisitDispatchCommand",
        "GitHubResearchLoveSecondVisitDispatchCommand",
        "GitHubResearchLoveTwoProjectionCommand",
        "GitHubResearchLoveTwoAnalysisRecallCommand",
        "GitHubResearchLoveLiaisonSynthesisCommand",
        "GitHubResearchLoveFinalDeliverableCommand",
        "GitHubResearchLoveFinalPublicationCommand",
        "GitHubResearchLoveFinalPublicationExecution",
        "GitHubResearchLovePublicationEvidenceCommand",
    )
    for name in names:
        monkeypatch.setattr(
            module,
            name,
            lambda **kwargs: SimpleNamespace(**kwargs),
        )


def _prepare_command():
    artifact = SimpleNamespace()
    return GitHubResearchLoveClosedLoopPrepareCommand(
        runtime_ports=SimpleNamespace(),  # type: ignore[arg-type]
        ready_run={"status": "ready"},
        artifact_contents=(artifact, artifact, artifact),  # type: ignore[arg-type]
        reference_point_reader=object(),
        requested_at="2026-07-18T10:00:00Z",
        analysis_created_at="2026-07-18T10:10:00Z",
        projected_at="2026-07-18T10:20:00Z",
        final_created_at="2026-07-18T10:30:00Z",
        recall_query_text="Relier les deux analyses.",
        project_item_id="PVTI_test",
        project_field_ref="PVTF_test",
    )


@pytest.mark.asyncio
async def test_prepare_composes_every_existing_stage_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_command_types(monkeypatch)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    calls: list[str] = []

    ready = Stage(
        valid=True,
        admissible=True,
        work_package_build={
            "work_package": {
                "repository": "newicody/projects",
                "work_package_ref": "research-work-package:test",
                "source_issue": {"number": 15},
            }
        },
        admissibility={
            "route_candidate": {
                "route_candidate_ref": "research-route-candidate:test",
            }
        },
    )
    intake = Stage(valid=True, authorized=True)
    scheduler = Stage(valid=True)
    first = Stage(valid=True)
    second = Stage(valid=True)
    sql = Stage(valid=True)
    projections = Stage(valid=True)
    recall = Stage(valid=True)
    liaison = Stage(valid=True)
    final = Stage(valid=True)
    publication_plan = SimpleNamespace(
        plan_digest="sha256:" + "1" * 64,
        to_mapping=lambda: {
            "plan_digest": "sha256:" + "1" * 64,
        },
    )

    def sync(name, value):
        def wrapped(*args, **kwargs):
            calls.append(name)
            return value
        return wrapped

    def async_(name, value):
        async def wrapped(*args, **kwargs):
            calls.append(name)
            return value
        return wrapped

    monkeypatch.setattr(
        module,
        "assemble_ready_run_and_evaluate_research_admissibility",
        sync("ready_run_admissibility", ready),
    )
    monkeypatch.setattr(
        module,
        "build_authorized_scheduler_intake_for_admissible_research",
        sync("scheduler_intake", intake),
    )
    monkeypatch.setattr(
        module,
        "dispatch_authorized_research_through_existing_scheduler",
        async_("scheduler_dispatch", scheduler),
    )
    monkeypatch.setattr(
        module,
        "dispatch_first_love_visit_from_github_research",
        async_("first_specialist", first),
    )
    monkeypatch.setattr(
        module,
        "dispatch_second_love_visit_from_first_analysis",
        async_("second_specialist", second),
    )
    monkeypatch.setattr(
        module,
        "persist_github_research_love_analyses",
        sync("analysis_sql", sql),
    )
    monkeypatch.setattr(
        module,
        "project_github_research_love_analyses",
        async_("analysis_qdrant", projections),
    )
    monkeypatch.setattr(
        module,
        "recall_github_research_love_analyses",
        async_("analysis_recall", recall),
    )
    monkeypatch.setattr(
        module,
        "build_github_research_love_liaison_synthesis",
        sync("liaison_synthesis", liaison),
    )
    monkeypatch.setattr(
        module,
        "persist_github_research_love_final_deliverable",
        sync("final_deliverable_sql", final),
    )
    monkeypatch.setattr(
        module,
        "build_github_research_love_final_publication_plan",
        sync("publication_plan", publication_plan),
    )

    result = await prepare_github_research_love_closed_loop(
        _prepare_command()
    )
    mapping = result.to_mapping()

    assert result.valid is True
    assert result.status == "publication-confirmation-required"
    assert calls == list(module._STAGE_ORDER)
    assert mapping["publication_plan_digest"] == (
        "sha256:" + "1" * 64
    )
    assert mapping["boundaries"]["remote_publication_performed"] is False
    assert mapping["boundaries"]["scheduler_remains_sole_orchestrator"] is True


@pytest.mark.asyncio
async def test_prepare_stops_immediately_on_inadmissible_research(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_command_types(monkeypatch)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    ready = Stage(
        valid=True,
        admissible=False,
        issues=("research is inadmissible",),
        work_package_build={},
        admissibility={},
    )
    monkeypatch.setattr(
        module,
        "assemble_ready_run_and_evaluate_research_admissibility",
        lambda command: ready,
    )
    monkeypatch.setattr(
        module,
        "build_authorized_scheduler_intake_for_admissible_research",
        lambda command: pytest.fail("Scheduler intake must not start"),
    )

    result = await prepare_github_research_love_closed_loop(
        _prepare_command()
    )

    assert result.valid is False
    assert result.failed_stage == "ready_run_admissibility"
    assert tuple(result.stage_results) == ("ready_run_admissibility",)


def _prepared():
    plan = SimpleNamespace(
        plan_digest="sha256:" + "7" * 64,
        to_mapping=lambda: {
            "plan_digest": "sha256:" + "7" * 64,
        },
    )
    stages = {
        name: Stage(valid=True)
        for name in module._STAGE_ORDER[:-1]
    }
    stages["publication_plan"] = plan
    return module.GitHubResearchLoveClosedLoopPrepared(
        schema=module.PREPARED_SCHEMA,
        valid=True,
        status="publication-confirmation-required",
        issues=(),
        repository="newicody/projects",
        issue_number=15,
        work_package_ref="research-work-package:test",
        stage_results=stages,
    )


def test_completion_publishes_once_then_closes_sql(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_command_types(monkeypatch)
    prepared = _prepared()
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    calls: list[str] = []
    remote = Stage(
        valid=True,
        status="published",
        remote_result=SimpleNamespace(issues=()),
    )
    closure = Stage(
        valid=True,
        status="closed",
        cycle_closed=True,
    )
    monkeypatch.setattr(
        module,
        "execute_github_research_love_final_publication",
        lambda *args, **kwargs: (
            calls.append("remote_publication") or remote
        ),
    )
    monkeypatch.setattr(
        module,
        "close_github_research_love_cycle",
        lambda command: calls.append("closure") or closure,
    )

    result = complete_github_research_love_closed_loop(
        GitHubResearchLoveClosedLoopCompleteCommand(
            runtime_ports=SimpleNamespace(),  # type: ignore[arg-type]
            prepared=prepared,
            confirm_plan_digest=prepared.publication_plan.plan_digest,
            closed_at="2026-07-18T11:00:00Z",
            remote_mutation_allowed=True,
            issue_publication_allowed=True,
            project_projection_allowed=True,
        ),
        issue_port=SimpleNamespace(),  # type: ignore[arg-type]
        project_port=SimpleNamespace(),  # type: ignore[arg-type]
    )
    mapping = result.to_mapping()

    assert result.valid is True
    assert result.status == "closed"
    assert calls == ["remote_publication", "closure"]
    assert mapping["cycle_closed"] is True
    assert mapping["boundaries"][
        "remote_publication_reexecuted_by_closure"
    ] is False


def test_module_is_composition_not_parallel_orchestrator() -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")

    required = (
        "assemble_ready_run_and_evaluate_research_admissibility(",
        "build_authorized_scheduler_intake_for_admissible_research(",
        "dispatch_authorized_research_through_existing_scheduler(",
        "dispatch_first_love_visit_from_github_research(",
        "dispatch_second_love_visit_from_first_analysis(",
        "persist_github_research_love_analyses(",
        "project_github_research_love_analyses(",
        "recall_github_research_love_analyses(",
        "build_github_research_love_liaison_synthesis(",
        "persist_github_research_love_final_deliverable(",
        "build_github_research_love_final_publication_plan(",
        "execute_github_research_love_final_publication(",
        "close_github_research_love_cycle(",
    )
    for marker in required:
        assert marker in source

    forbidden = (
        "Scheduler(",
        "Dispatcher(",
        "EventBus(",
        "QdrantClient(",
        "GitHubCliFinalDeliverablePublicationAdapter(",
        "import openvino",
        "import psycopg",
        "CREATE TABLE",
        "subprocess.",
        "requests.",
    )
    for marker in forbidden:
        assert marker not in source
