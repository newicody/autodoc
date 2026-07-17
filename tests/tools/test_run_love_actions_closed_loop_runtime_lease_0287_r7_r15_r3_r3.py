from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest


def _load_tool(name: str) -> ModuleType:
    path = (
        Path(__file__).resolve().parents[2]
        / "tools"
        / "run_love_actions_closed_loop_0287.py"
    )
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


class _Lease:
    def __init__(self) -> None:
        self.close_count = 0

    def close(self, *, current_process_id: int) -> None:
        self.close_count += 1


def _runtime(scheduler, lifecycle: str = "tool-bounded") -> SimpleNamespace:
    return SimpleNamespace(
        scheduler=scheduler,
        dispatcher=object(),
        authority_store=object(),
        projection_port=object(),
        collection=object(),
        embedder=object(),
        executor=object(),
        scheduler_lifecycle=lifecycle,
    )


def test_tool_bounded_runtime_lease_closes_after_scheduler_shutdown(
    monkeypatch,
) -> None:
    tool = _load_tool("run_love_actions_closed_loop_runtime_lease")
    events: list[str] = []

    class Scheduler:
        def __init__(self) -> None:
            self.running = False
            self.stopped = asyncio.Event()

        async def run(self) -> None:
            self.running = True
            await self.stopped.wait()
            self.running = False
            events.append("scheduler-stopped")

        async def shutdown(self) -> None:
            events.append("scheduler-shutdown")
            self.stopped.set()

    class Lease(_Lease):
        def close(self, *, current_process_id: int) -> None:
            events.append("lease-close")
            super().close(
                current_process_id=current_process_id,
            )

    scheduler = Scheduler()
    lease = Lease()

    async def fake_r14(command, **ports):
        assert scheduler.running is True
        events.append("r14-complete")
        return "r14-result"

    monkeypatch.setattr(
        tool,
        "run_love_full_deterministic_local_smoke",
        fake_r14,
    )
    result = asyncio.run(
        tool._run_r14_on_existing_scheduler(
            SimpleNamespace(run_id="123"),
            _runtime(scheduler),
            runtime_lease=lease,
        )
    )

    assert result == "r14-result"
    assert lease.close_count == 1
    assert events.index("scheduler-stopped") < events.index("lease-close")


def test_scheduler_failure_still_closes_tool_bounded_lease(monkeypatch) -> None:
    tool = _load_tool("run_love_actions_closed_loop_runtime_lease_failure")

    class Scheduler:
        async def run(self) -> None:
            raise RuntimeError("scheduler failed")

        async def shutdown(self) -> None:
            return None

    lease = _Lease()

    async def hanging_r14(command, **ports):
        await asyncio.Event().wait()

    monkeypatch.setattr(
        tool,
        "run_love_full_deterministic_local_smoke",
        hanging_r14,
    )
    with pytest.raises(
        tool.LoveActionsClosedLoopPreviewError,
        match="Scheduler failed",
    ):
        asyncio.run(
            tool._run_r14_on_existing_scheduler(
                SimpleNamespace(run_id="123"),
                _runtime(Scheduler()),
                runtime_lease=lease,
            )
        )

    assert lease.close_count == 1


def test_externally_managed_runtime_does_not_close_injected_lease(
    monkeypatch,
) -> None:
    tool = _load_tool("run_love_actions_closed_loop_runtime_lease_external")

    class Scheduler:
        async def run(self) -> None:
            raise AssertionError("must not start")

        async def shutdown(self) -> None:
            raise AssertionError("must not stop")

    lease = _Lease()

    async def fake_r14(command, **ports):
        return "external-result"

    monkeypatch.setattr(
        tool,
        "run_love_full_deterministic_local_smoke",
        fake_r14,
    )
    result = asyncio.run(
        tool._run_r14_on_existing_scheduler(
            SimpleNamespace(run_id="123"),
            _runtime(Scheduler(), "externally-managed"),
            runtime_lease=lease,
        )
    )

    assert result == "external-result"
    assert lease.close_count == 0


def test_scheduler_failure_at_r14_completion_is_not_silenced(
    monkeypatch,
) -> None:
    tool = _load_tool("run_love_actions_closed_loop_runtime_lease_race")
    release_scheduler = asyncio.Event()

    class Scheduler:
        async def run(self) -> None:
            await release_scheduler.wait()
            raise RuntimeError("late scheduler failure")

        async def shutdown(self) -> None:
            release_scheduler.set()

    lease = _Lease()

    async def fake_r14(command, **ports):
        release_scheduler.set()
        await asyncio.sleep(0)
        return "r14-result"

    monkeypatch.setattr(
        tool,
        "run_love_full_deterministic_local_smoke",
        fake_r14,
    )
    with pytest.raises(
        tool.LoveActionsClosedLoopPreviewError,
        match="Scheduler failed",
    ):
        asyncio.run(
            tool._run_r14_on_existing_scheduler(
                SimpleNamespace(run_id="123"),
                _runtime(Scheduler()),
                runtime_lease=lease,
            )
        )

    assert lease.close_count == 1
