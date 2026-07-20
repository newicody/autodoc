"""Own one injected Scheduler cycle for a tool-bounded runtime.

The helper starts and stops only the exact Scheduler object supplied by the
installed runtime. It creates no Scheduler, Dispatcher, EventBus, queue,
thread, process, daemon or durable side channel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

from context.github_research_love_complete_closed_loop_0287 import (
    GitHubResearchLoveClosedLoopPrepareCommand,
    prepare_github_research_love_closed_loop as _prepare_without_scheduler_owner,
)


SCHEDULER_OWNERSHIP_RECEIPT_SCHEMA = (
    "missipy.love.tool_bounded_scheduler_ownership_receipt.v1"
)

T = TypeVar("T")


class ToolBoundedSchedulerOwnershipError(RuntimeError):
    """Raised when the injected Scheduler lifecycle cannot be preserved."""


class RuntimeSchedulerPort(Protocol):
    """Minimal canonical Scheduler surface needed by the runtime owner."""

    @property
    def running(self) -> bool: ...

    async def run(self) -> None: ...

    async def shutdown(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ToolBoundedSchedulerOwnershipReceipt:
    """Serializable evidence for one Scheduler ownership decision."""

    schema: str
    scheduler_lifecycle: str
    running_before: bool
    scheduler_started_by_owner: bool
    running_during_operation: bool
    scheduler_shutdown_by_owner: bool
    run_task_joined: bool
    running_after: bool

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_OWNERSHIP_RECEIPT_SCHEMA:
            raise ToolBoundedSchedulerOwnershipError(
                "unsupported Scheduler ownership receipt schema"
            )
        if self.scheduler_lifecycle not in {
            "tool-bounded",
            "externally-managed",
        }:
            raise ToolBoundedSchedulerOwnershipError(
                "scheduler_lifecycle must be tool-bounded or externally-managed"
            )
        if self.scheduler_started_by_owner and self.running_before:
            raise ToolBoundedSchedulerOwnershipError(
                "an already-running Scheduler cannot be started by this owner"
            )
        if self.scheduler_shutdown_by_owner != self.scheduler_started_by_owner:
            raise ToolBoundedSchedulerOwnershipError(
                "the owner must stop exactly the Scheduler cycle it started"
            )
        if self.run_task_joined != self.scheduler_started_by_owner:
            raise ToolBoundedSchedulerOwnershipError(
                "the owner must join exactly the Scheduler task it started"
            )
        if self.scheduler_started_by_owner and self.running_after:
            raise ToolBoundedSchedulerOwnershipError(
                "an owned tool-bounded Scheduler must be stopped before return"
            )
        if not self.scheduler_started_by_owner and not self.running_after:
            raise ToolBoundedSchedulerOwnershipError(
                "a reused Scheduler must remain active after the operation"
            )
        if not self.running_during_operation:
            raise ToolBoundedSchedulerOwnershipError(
                "the operation must execute while the Scheduler is running"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "scheduler_lifecycle": self.scheduler_lifecycle,
            "running_before": self.running_before,
            "scheduler_started_by_owner": self.scheduler_started_by_owner,
            "running_during_operation": self.running_during_operation,
            "scheduler_shutdown_by_owner": self.scheduler_shutdown_by_owner,
            "run_task_joined": self.run_task_joined,
            "running_after": self.running_after,
            "boundaries": {
                "existing_scheduler_reused": True,
                "new_scheduler_created": False,
                "new_dispatcher_created": False,
                "new_eventbus_created": False,
                "new_thread_created": False,
                "new_process_created": False,
                "same_process_event_loop": True,
            },
        }


@dataclass(frozen=True, slots=True)
class ToolBoundedSchedulerExecution(Generic[T]):
    """Operation value paired with its Scheduler ownership evidence."""

    value: T
    receipt: ToolBoundedSchedulerOwnershipReceipt


@dataclass(frozen=True, slots=True)
class OwnedSchedulerPreparedResult(Generic[T]):
    """Transparent prepared result carrying the Scheduler-cycle evidence."""

    prepared: T
    scheduler_cycle: ToolBoundedSchedulerOwnershipReceipt

    def __getattr__(self, name: str) -> Any:
        return getattr(self.prepared, name)

    def to_mapping(self) -> dict[str, object]:
        serializer = getattr(self.prepared, "to_mapping", None)
        if not callable(serializer):
            raise ToolBoundedSchedulerOwnershipError(
                "prepared result does not expose to_mapping"
            )
        candidate = serializer()
        if not isinstance(candidate, Mapping):
            raise ToolBoundedSchedulerOwnershipError(
                "prepared result to_mapping must return a mapping"
            )
        mapping = dict(candidate)
        if "scheduler_cycle" in mapping:
            raise ToolBoundedSchedulerOwnershipError(
                "prepared result already contains scheduler_cycle"
            )
        mapping["scheduler_cycle"] = self.scheduler_cycle.to_mapping()
        return mapping


async def run_with_owned_tool_bounded_scheduler(
    *,
    scheduler: RuntimeSchedulerPort,
    scheduler_lifecycle: str,
    operation: Callable[[], Awaitable[T]],
    task_name: str = "missipy-tool-bounded-scheduler",
) -> ToolBoundedSchedulerExecution[T]:
    """Execute one operation with the exact injected Scheduler active."""

    lifecycle = str(scheduler_lifecycle).strip()
    if lifecycle not in {"tool-bounded", "externally-managed"}:
        raise ToolBoundedSchedulerOwnershipError(
            "scheduler_lifecycle must be tool-bounded or externally-managed"
        )
    if not callable(operation):
        raise ToolBoundedSchedulerOwnershipError("operation must be callable")

    running_before = bool(scheduler.running)

    if lifecycle == "externally-managed":
        if not running_before:
            raise ToolBoundedSchedulerOwnershipError(
                "an externally-managed Scheduler must already be running"
            )
        value = await operation()
        if not scheduler.running:
            raise ToolBoundedSchedulerOwnershipError(
                "the externally-managed Scheduler stopped during the operation"
            )
        return ToolBoundedSchedulerExecution(
            value=value,
            receipt=ToolBoundedSchedulerOwnershipReceipt(
                schema=SCHEDULER_OWNERSHIP_RECEIPT_SCHEMA,
                scheduler_lifecycle=lifecycle,
                running_before=True,
                scheduler_started_by_owner=False,
                running_during_operation=True,
                scheduler_shutdown_by_owner=False,
                run_task_joined=False,
                running_after=True,
            ),
        )

    if running_before:
        value = await operation()
        if not scheduler.running:
            raise ToolBoundedSchedulerOwnershipError(
                "the reused tool-bounded Scheduler stopped during the operation"
            )
        return ToolBoundedSchedulerExecution(
            value=value,
            receipt=ToolBoundedSchedulerOwnershipReceipt(
                schema=SCHEDULER_OWNERSHIP_RECEIPT_SCHEMA,
                scheduler_lifecycle=lifecycle,
                running_before=True,
                scheduler_started_by_owner=False,
                running_during_operation=True,
                scheduler_shutdown_by_owner=False,
                run_task_joined=False,
                running_after=True,
            ),
        )

    run_task = asyncio.create_task(scheduler.run(), name=task_name)
    await asyncio.sleep(0)

    if run_task.done():
        await run_task
        raise ToolBoundedSchedulerOwnershipError(
            "the owned Scheduler run task completed before the operation"
        )
    if not scheduler.running:
        run_task.cancel()
        try:
            await run_task
        except asyncio.CancelledError:
            pass
        raise ToolBoundedSchedulerOwnershipError(
            "the owned Scheduler did not enter its running state"
        )

    try:
        value = await operation()
        if run_task.done() or not scheduler.running:
            await run_task
            raise ToolBoundedSchedulerOwnershipError(
                "the owned Scheduler stopped before the operation completed"
            )
    finally:
        if scheduler.running:
            await scheduler.shutdown()
        await run_task

    return ToolBoundedSchedulerExecution(
        value=value,
        receipt=ToolBoundedSchedulerOwnershipReceipt(
            schema=SCHEDULER_OWNERSHIP_RECEIPT_SCHEMA,
            scheduler_lifecycle=lifecycle,
            running_before=False,
            scheduler_started_by_owner=True,
            running_during_operation=True,
            scheduler_shutdown_by_owner=True,
            run_task_joined=True,
            running_after=bool(scheduler.running),
        ),
    )


async def prepare_github_research_love_closed_loop(
    command: GitHubResearchLoveClosedLoopPrepareCommand,
) -> OwnedSchedulerPreparedResult[Any]:
    """Run the existing prepare composition under the injected Scheduler."""

    runtime_ports = command.runtime_ports
    execution = await run_with_owned_tool_bounded_scheduler(
        scheduler=runtime_ports.scheduler,
        scheduler_lifecycle=runtime_ports.scheduler_lifecycle,
        operation=lambda: _prepare_without_scheduler_owner(command),
        task_name="missipy-love-tool-bounded-scheduler",
    )
    return OwnedSchedulerPreparedResult(
        prepared=execution.value,
        scheduler_cycle=execution.receipt,
    )
