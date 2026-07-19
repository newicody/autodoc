from __future__ import annotations

import asyncio
from types import SimpleNamespace

import context.github_research_love_scheduler_bootstrap_0287 as module
from context.github_research_scheduler_command_0287 import GitHubResearchSchedulerCommand
from kernel.scheduler_handler_instance_lifecycle import SchedulerHandlerExecutionContext
from kernel.scheduler_task_model import SchedulerTaskState


def _command(*, max_steps: int = 20, max_visits: int = 2):
    command = object.__new__(GitHubResearchSchedulerCommand)
    object.__setattr__(command, "command_ref", "scheduler-command:github-research:" + "a" * 24)
    object.__setattr__(command, "priority", 80)
    object.__setattr__(
        command,
        "correlation",
        SimpleNamespace(
            repository="newicody/projects",
            issue_number=54,
            run_id="29673341210",
            conversation_ref="conversation:github-research-54",
            return_route_ref="route:github-research-54",
        ),
    )
    object.__setattr__(
        command,
        "research",
        SimpleNamespace(
            work_package_ref="work-package:github-research-54",
            route_candidate_ref="route-candidate:github-research-54",
            context_generation=0,
            context_refs=("context:github-research-54",),
            evidence_refs=(
                "artifact:authoritative-request-54",
                "artifact:copilot-advisory-54",
                "artifact:run-manifest-54",
            ),
        ),
    )
    object.__setattr__(
        command,
        "execution_budget",
        SimpleNamespace(
            max_scheduler_steps=max_steps,
            max_specialist_visits=max_visits,
        ),
    )
    return command


def test_builds_full_correlated_graph_with_only_first_stage_ready() -> None:
    command = _command()
    built = module.build_github_research_love_task_graph(
        command,
        created_at="2026-07-19T20:00:00Z",
    )

    assert len(built.graph.tasks) == 14
    assert tuple(built.stage_task_refs) == tuple(
        spec.stage for spec in module.GITHUB_RESEARCH_LOVE_STAGE_SPECS
    )
    assert built.graph.tasks[0].capability_ref == (
        module.GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_CAPABILITY_REF
    )
    assert built.graph.tasks[-1].capability_ref.endswith("close-cycle.v1")
    assert all(task.command_ref == command.command_ref for task in built.graph.tasks)
    assert all(task.evidence_refs == command.research.evidence_refs for task in built.graph.tasks)
    for previous, current in zip(built.graph.tasks, built.graph.tasks[1:]):
        assert current.parent_task_ref == previous.task_ref
        assert current.dependencies[0].task_ref == previous.task_ref

    plan = built.graph.readiness_plan()
    assert plan.ready_task_refs == (built.first_task_ref,)
    assert built.graph.task(built.first_task_ref).state is SchedulerTaskState.PLANNED


def test_rejects_budget_too_small_for_full_graph() -> None:
    try:
        module.build_github_research_love_task_graph(
            _command(max_steps=13),
            created_at="2026-07-19T20:00:00Z",
        )
    except module.GitHubResearchLoveSchedulerBootstrapError as exc:
        assert "max_scheduler_steps" in str(exc)
    else:
        raise AssertionError("budget insuffisant accepté")


def test_bootstrap_catalogues_only_real_first_visit_preparation_handler() -> None:
    class Provider:
        def load(self, **_kwargs):
            raise AssertionError("non appelé pendant le bootstrap")

    bootstrap = module.build_github_research_love_scheduler_bootstrap(Provider())

    assert bootstrap.handler_refs == (
        module.GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_HANDLER_REF,
    )
    assert bootstrap.capability_refs == (
        module.GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_CAPABILITY_REF,
    )
    binding = bootstrap.catalog.resolve_for(
        _command(),
        capability_ref=module.GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_CAPABILITY_REF,
        contract_version=1,
    )
    assert binding.handler_type is module.GitHubResearchLovePrepareFirstVisitHandler
    try:
        bootstrap.catalog.resolve_for(
            _command(),
            capability_ref="capability:github-research.love.execute-first-specialist.v1",
            contract_version=1,
        )
    except LookupError:
        pass
    else:
        raise AssertionError("capacité future cataloguée prématurément")


def test_handler_reuses_existing_surface_builder_without_dispatch(monkeypatch) -> None:
    command = _command()
    built = module.build_github_research_love_task_graph(
        command,
        created_at="2026-07-19T20:00:00Z",
    )
    calls = []
    surface = SimpleNamespace(
        study=SimpleNamespace(study_ref="love-study:github-54-test"),
        first_task=SimpleNamespace(task_ref="specialist-task:love-first-test"),
        first_visit=SimpleNamespace(visit_ref="laboratory-visit:love-first-test"),
    )

    def existing_builder(**kwargs):
        calls.append(kwargs)
        return surface

    monkeypatch.setattr(
        module,
        "build_first_love_visit_surface_from_github_research",
        existing_builder,
    )

    class Provider:
        def load(self, *, command, execution_context):
            assert execution_context.task_ref == built.first_task_ref
            return module.GitHubResearchLoveFirstVisitInput(
                runtime_ports=object(),
                work_package={
                    "repository": command.correlation.repository,
                    "run_id": command.correlation.run_id,
                    "work_package_ref": command.research.work_package_ref,
                    "context_generation": command.research.context_generation,
                    "source_issue": {"number": command.correlation.issue_number},
                },
                scheduler_intake={"schema": "test"},
                scheduler_dispatch={"schema": "test"},
            )

    context = SchedulerHandlerExecutionContext(
        scheduler_ref="scheduler:canonical",
        command_ref=command.command_ref,
        task_ref=built.first_task_ref,
        attempt_ref="scheduler-attempt:test",
        reservation_ref="scheduler-reservation:test",
        launch_ticket_ref="scheduler-handler-launch:test",
        handler_instance_ref="handler-instance:test",
        deadline_at="2026-07-19T20:05:00Z",
        started_at="2026-07-19T20:00:01Z",
    )
    handler = module.GitHubResearchLovePrepareFirstVisitHandler(Provider())
    result = asyncio.run(handler.execute(command, context))

    assert result.surface is surface
    assert result.visit_ref == "laboratory-visit:love-first-test"
    assert result.result_digest.startswith("sha256:")
    assert len(calls) == 1
