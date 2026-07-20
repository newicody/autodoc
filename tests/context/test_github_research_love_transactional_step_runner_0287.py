from __future__ import annotations

import pytest

from context.github_research_love_transactional_step_runner_0287 import (
    GitHubResearchLoveTransactionalStepRunner,
    build_github_research_love_transactional_step_runner,
)


class ContinuationStore:
    def load_snapshot(self, **_kwargs):
        raise AssertionError("not called")


class LaunchTransaction:
    def commit_launch(self, **_kwargs):
        raise AssertionError("not called")


class CompletionTransaction:
    def commit_outcome(self, **_kwargs):
        raise AssertionError("not called")


class InputProvider:
    def load_ready_task_execution_input(self, **_kwargs):
        raise AssertionError("not called")


def test_factory_keeps_installed_transaction_identities() -> None:
    continuation = ContinuationStore()
    launch = LaunchTransaction()
    completion = CompletionTransaction()
    provider = InputProvider()
    runner = build_github_research_love_transactional_step_runner(
        scheduler_ref="scheduler:canonical",
        continuation_store=continuation,
        task_launch_transaction=launch,
        handler_execution_transaction=completion,
        ready_task_input_provider=provider,
    )
    assert isinstance(runner, GitHubResearchLoveTransactionalStepRunner)
    assert runner._continuation_store is continuation
    assert runner._task_launch_transaction is launch
    assert runner._handler_execution_transaction is completion
    assert runner._ready_task_input_provider is provider


def test_factory_fails_closed_without_ready_task_provider() -> None:
    with pytest.raises(TypeError):
        build_github_research_love_transactional_step_runner(
            scheduler_ref="scheduler:canonical",
            continuation_store=ContinuationStore(),
            task_launch_transaction=LaunchTransaction(),
            handler_execution_transaction=CompletionTransaction(),
        )
