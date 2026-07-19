from __future__ import annotations

from types import SimpleNamespace

import context.github_research_love_grouped_specialist_pipeline_0287 as module
from context.github_research_scheduler_command_0287 import (
    GitHubResearchSchedulerCommand,
)


def _command(*, max_steps: int = 20, max_visits: int = 2):
    command = object.__new__(GitHubResearchSchedulerCommand)
    object.__setattr__(
        command,
        "command_ref",
        "scheduler-command:github-research:" + "b" * 24,
    )
    object.__setattr__(command, "priority", 80)
    object.__setattr__(
        command,
        "correlation",
        SimpleNamespace(
            conversation_ref="conversation:github-research-54",
            return_route_ref="route:github-research-54",
        ),
    )
    object.__setattr__(
        command,
        "research",
        SimpleNamespace(
            work_package_ref="research-work-package:github-research-54",
            route_candidate_ref="route-candidate:github-research-54",
            context_refs=("context:github-research-54",),
            evidence_refs=("artifact:authoritative-request-54",),
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


class _Provider:
    def load_first_dispatch_command(self, **_kwargs):
        raise AssertionError("non appelé pendant le bootstrap")

    def load_second_dispatch_command(self, **_kwargs):
        raise AssertionError("non appelé pendant le bootstrap")

    def load_pair_stage_input(self, **_kwargs):
        raise AssertionError("non appelé pendant le bootstrap")


class _FirstVisitProvider:
    def load(self, **_kwargs):
        raise AssertionError("non appelé pendant le bootstrap")


def test_grouped_graph_keeps_two_specialists_and_pair_effect_separate() -> None:
    built = module.build_github_research_love_grouped_task_graph(
        _command(),
        created_at="2026-07-19T21:00:00Z",
    )
    assert len(built.graph.tasks) == 10
    assert tuple(built.stage_task_refs) == tuple(
        spec.stage for spec in module.GROUPED_STAGE_SPECS
    )
    capabilities = tuple(task.capability_ref for task in built.graph.tasks)
    assert module.EXECUTE_FIRST_CAPABILITY_REF in capabilities
    assert module.EXECUTE_SECOND_CAPABILITY_REF in capabilities
    assert module.PERSIST_PROJECT_PAIR_CAPABILITY_REF in capabilities
    assert capabilities.index(module.EXECUTE_FIRST_CAPABILITY_REF) < capabilities.index(
        module.EXECUTE_SECOND_CAPABILITY_REF
    )
    assert capabilities.index(module.EXECUTE_SECOND_CAPABILITY_REF) < capabilities.index(
        module.PERSIST_PROJECT_PAIR_CAPABILITY_REF
    )
    for previous, current in zip(built.graph.tasks, built.graph.tasks[1:]):
        assert current.dependencies[0].task_ref == previous.task_ref


def test_grouped_graph_rejects_insufficient_budget() -> None:
    try:
        module.build_github_research_love_grouped_task_graph(
            _command(max_steps=9),
            created_at="2026-07-19T21:00:00Z",
        )
    except module.GitHubResearchLoveGroupedPipelineError as exc:
        assert "max_scheduler_steps" in str(exc)
    else:
        raise AssertionError("budget insuffisant accepté")


def test_grouped_bootstrap_catalogues_only_available_capabilities() -> None:
    bootstrap = module.build_github_research_love_grouped_scheduler_bootstrap(
        _FirstVisitProvider(),
        _Provider(),
    )
    assert bootstrap.handler_refs == (
        module.GITHUB_RESEARCH_LOVE_PREPARE_FIRST_VISIT_HANDLER_REF,
        module.EXECUTE_FIRST_HANDLER_REF,
        module.EXECUTE_SECOND_HANDLER_REF,
        module.PERSIST_PROJECT_PAIR_HANDLER_REF,
    )
    assert len(bootstrap.catalog.snapshot()) == 4


def test_pair_result_refuses_merged_analysis_objects() -> None:
    try:
        module.GitHubResearchLovePersistedProjectedPair(
            schema=module.PAIR_RESULT_SCHEMA,
            command_ref="scheduler-command:test",
            scheduler_task_ref="scheduler-task:test",
            work_package_ref="research-work-package:test",
            sql_plan_digest="sha256:" + "1" * 64,
            revision_ref="context-revision:test",
            first_object_ref="context-object:same",
            second_object_ref="context-object:same",
            first_artifact_ref="artifact:first",
            second_artifact_ref="artifact:second",
            qdrant_pair_plan_digest="sha256:" + "2" * 64,
            first_projection={"object_ref": "context-object:first"},
            second_projection={"object_ref": "context-object:second"},
            completed_at="2026-07-19T21:00:00Z",
        )
    except module.GitHubResearchLoveGroupedPipelineError as exc:
        assert "objets SQL distincts" in str(exc)
    else:
        raise AssertionError("fusion des analyses acceptée")
