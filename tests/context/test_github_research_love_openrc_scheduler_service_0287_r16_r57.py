from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from context.github_research_love_openrc_scheduler_service_0287 import (
    GitHubResearchLoveOpenRcSchedulerService,
    GitHubResearchLoveOpenRcSchedulerServiceError,
    OpenRcSchedulerServiceSettings,
)


class Scheduler:
    def __init__(self) -> None:
        self._running = False
        self._finished = asyncio.Event()
        self.run_calls = 0
        self.shutdown_calls = 0

    @property
    def running(self) -> bool:
        return self._running

    async def run(self) -> None:
        self.run_calls += 1
        self._running = True
        await self._finished.wait()
        self._running = False

    async def shutdown(self) -> None:
        self.shutdown_calls += 1
        self._running = False
        self._finished.set()


@dataclass(frozen=True)
class TickReport:
    status: str


class Runtime:
    def __init__(self, stop: asyncio.Event) -> None:
        self.stop = stop
        self.calls = 0
        self.bounds: list[int] = []

    async def run_tick(self, *, actor_ref, cause_ref, bound):
        assert actor_ref == "actor:openrc-autodoc-scheduler"
        assert cause_ref == "cause:openrc-service-tick"
        self.calls += 1
        self.bounds.append(bound.max_task_steps)
        if self.calls == 2:
            self.stop.set()
            return TickReport("cycle-executed")
        return TickReport("idle")


@pytest.mark.asyncio
async def test_service_owns_one_scheduler_and_stops_cooperatively() -> None:
    stop = asyncio.Event()
    scheduler = Scheduler()
    runtime = Runtime(stop)
    times = iter(("2026-07-20T06:00:00Z", "2026-07-20T06:00:01Z"))
    service = GitHubResearchLoveOpenRcSchedulerService(
        scheduler=scheduler,
        runtime=runtime,
        settings=OpenRcSchedulerServiceSettings(
            poll_interval_seconds=0.05,
            max_task_steps=10,
        ),
        clock=lambda: next(times),
    )

    receipt = await service.run(stop)

    assert scheduler.run_calls == 1
    assert scheduler.shutdown_calls == 1
    assert scheduler.running is False
    assert runtime.calls == 2
    assert runtime.bounds == [10, 10]
    assert receipt.tick_count == 2
    assert receipt.idle_tick_count == 1
    assert receipt.executed_tick_count == 1
    assert receipt.scheduler_task_joined is True
    assert receipt.boundaries["new_scheduler_created"] is False
    assert receipt.boundaries["postgresql_remains_durable_authority"] is True


@pytest.mark.asyncio
async def test_service_refuses_scheduler_already_owned_elsewhere() -> None:
    stop = asyncio.Event()
    scheduler = Scheduler()
    scheduler._running = True
    service = GitHubResearchLoveOpenRcSchedulerService(
        scheduler=scheduler,
        runtime=Runtime(stop),
        settings=OpenRcSchedulerServiceSettings(),
    )

    with pytest.raises(
        GitHubResearchLoveOpenRcSchedulerServiceError,
        match="déjà actif",
    ):
        await service.run(stop)
