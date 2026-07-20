from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

import context.love_tool_bounded_scheduler_owner_0287 as owner
from context.love_tool_bounded_scheduler_owner_0287 import (
    ToolBoundedSchedulerOwnershipError,
    run_with_owned_tool_bounded_scheduler,
)


class FakeScheduler:
    def __init__(self, *, running: bool = False) -> None:
        self.running = running
        self.run_calls = 0
        self.shutdown_calls = 0
        self._stop: asyncio.Event | None = None

    async def run(self) -> None:
        self.run_calls += 1
        self.running = True
        self._stop = asyncio.Event()
        await self._stop.wait()
        self.running = False

    async def shutdown(self) -> None:
        self.shutdown_calls += 1
        if self._stop is None:
            raise AssertionError("shutdown called without an owned run")
        self._stop.set()


class NeverStartsScheduler(FakeScheduler):
    async def run(self) -> None:
        self.run_calls += 1
        await asyncio.sleep(10)


async def _value_operation(scheduler: FakeScheduler) -> str:
    assert scheduler.running is True
    return "ok"


def test_tool_bounded_starts_and_stops_the_same_injected_scheduler() -> None:
    scheduler = FakeScheduler()

    execution = asyncio.run(
        run_with_owned_tool_bounded_scheduler(
            scheduler=scheduler,
            scheduler_lifecycle="tool-bounded",
            operation=lambda: _value_operation(scheduler),
        )
    )

    assert execution.value == "ok"
    assert scheduler.run_calls == 1
    assert scheduler.shutdown_calls == 1
    assert scheduler.running is False
    assert execution.receipt.scheduler_started_by_owner is True
    assert execution.receipt.scheduler_shutdown_by_owner is True
    assert execution.receipt.run_task_joined is True


def test_tool_bounded_reuses_an_already_running_scheduler_without_owning_it() -> None:
    scheduler = FakeScheduler(running=True)

    execution = asyncio.run(
        run_with_owned_tool_bounded_scheduler(
            scheduler=scheduler,
            scheduler_lifecycle="tool-bounded",
            operation=lambda: _value_operation(scheduler),
        )
    )

    assert execution.value == "ok"
    assert scheduler.run_calls == 0
    assert scheduler.shutdown_calls == 0
    assert scheduler.running is True
    assert execution.receipt.scheduler_started_by_owner is False


def test_externally_managed_scheduler_is_reused_and_never_stopped() -> None:
    scheduler = FakeScheduler(running=True)

    execution = asyncio.run(
        run_with_owned_tool_bounded_scheduler(
            scheduler=scheduler,
            scheduler_lifecycle="externally-managed",
            operation=lambda: _value_operation(scheduler),
        )
    )

    assert execution.value == "ok"
    assert scheduler.run_calls == 0
    assert scheduler.shutdown_calls == 0
    assert scheduler.running is True


def test_externally_managed_scheduler_must_already_be_running() -> None:
    scheduler = FakeScheduler()

    with pytest.raises(
        ToolBoundedSchedulerOwnershipError,
        match="externally-managed Scheduler must already be running",
    ):
        asyncio.run(
            run_with_owned_tool_bounded_scheduler(
                scheduler=scheduler,
                scheduler_lifecycle="externally-managed",
                operation=lambda: _value_operation(scheduler),
            )
        )

    assert scheduler.run_calls == 0
    assert scheduler.shutdown_calls == 0


def test_operation_failure_still_stops_the_owned_scheduler() -> None:
    scheduler = FakeScheduler()

    async def failing_operation() -> str:
        assert scheduler.running is True
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        asyncio.run(
            run_with_owned_tool_bounded_scheduler(
                scheduler=scheduler,
                scheduler_lifecycle="tool-bounded",
                operation=failing_operation,
            )
        )

    assert scheduler.run_calls == 1
    assert scheduler.shutdown_calls == 1
    assert scheduler.running is False


def test_tool_bounded_fails_closed_when_scheduler_never_starts() -> None:
    scheduler = NeverStartsScheduler()

    with pytest.raises(
        ToolBoundedSchedulerOwnershipError,
        match="did not enter its running state",
    ):
        asyncio.run(
            run_with_owned_tool_bounded_scheduler(
                scheduler=scheduler,
                scheduler_lifecycle="tool-bounded",
                operation=lambda: _value_operation(scheduler),
            )
        )

    assert scheduler.run_calls == 1
    assert scheduler.shutdown_calls == 0


def test_prepare_adapter_preserves_result_and_adds_scheduler_receipt(monkeypatch) -> None:
    scheduler = FakeScheduler()
    prepared = SimpleNamespace(
        valid=True,
        status="publication-confirmation-required",
        issues=(),
        publication_plan=SimpleNamespace(plan_digest="digest:test"),
        to_mapping=lambda: {"schema": "prepared.v1", "valid": True},
    )

    async def fake_prepare(command):
        assert command.runtime_ports.scheduler.running is True
        return prepared

    monkeypatch.setattr(owner, "_prepare_without_scheduler_owner", fake_prepare)
    command = SimpleNamespace(
        runtime_ports=SimpleNamespace(
            scheduler=scheduler,
            scheduler_lifecycle="tool-bounded",
        )
    )

    result = asyncio.run(owner.prepare_github_research_love_closed_loop(command))
    mapping = result.to_mapping()

    assert result.valid is True
    assert result.publication_plan.plan_digest == "digest:test"
    assert mapping["schema"] == "prepared.v1"
    assert mapping["scheduler_cycle"]["scheduler_started_by_owner"] is True
    assert mapping["scheduler_cycle"]["running_after"] is False
