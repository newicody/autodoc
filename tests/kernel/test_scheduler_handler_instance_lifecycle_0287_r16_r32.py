from __future__ import annotations

from types import SimpleNamespace

import pytest

from kernel.scheduler_handler_catalog import SchedulerHandlerCatalog
from kernel.scheduler_handler_contract import (
    HandlerExecutionPolicy,
    HandlerIdempotencyKind,
    HandlerInformation,
    HandlerLifecyclePhase,
    SchedulerHandler,
)
from kernel.scheduler_handler_instance_lifecycle import (
    ExplicitSchedulerHandlerFactory,
    SchedulerHandlerInstanceLifecycleError,
    SchedulerHandlerInstanceLifecycleService,
)
from kernel.scheduler_task_launch_preparation import SchedulerHandlerLaunchTicket
from kernel.scheduler_task_model import SchedulerTaskState


class _Command:
    def __init__(self, command_ref: str) -> None:
        self.command_ref = command_ref


class _Result:
    pass


class _Handler(SchedulerHandler[_Command, _Result]):
    HANDLER_REF = "handler:test-research"
    CAPABILITY_REF = "capability:test-research"
    COMMAND_TYPE = _Command
    RESULT_TYPE = _Result
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.DEDUPLICATED,
        timeout_policy_ref="timeout-policy:test",
        retry_policy_ref="retry-policy:test",
        resource_profile_ref="resource-profile:test",
    )
    INFORMATION = HandlerInformation(
        title="Handler de test",
        summary="Valide la création contrôlée.",
        created_text="{handler_title} créé pour {task_ref}.",
        started_text="{handler_title} démarre la tentative {attempt}.",
    )

    def __init__(self, dependency: object) -> None:
        self.dependency = dependency
        self.execute_count = 0

    async def execute(self, command: _Command, context: object) -> _Result:
        self.execute_count += 1
        return _Result()


class _Sink:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.notices = []

    def publish(self, notice) -> None:
        if self.fail:
            raise OSError("sink indisponible")
        self.notices.append(notice)


def _ticket() -> SchedulerHandlerLaunchTicket[_Command]:
    command = _Command("scheduler-command:test-1")
    binding = SchedulerHandlerCatalog((_Handler,)).resolve_for(
        command,
        capability_ref="capability:test-research",
        contract_version=1,
    )
    ticket = object.__new__(SchedulerHandlerLaunchTicket)
    values = {
        "schema": "missipy.scheduler.handler_launch_ticket.v1",
        "ticket_ref": "scheduler-handler-launch:test-1",
        "scheduler_ref": "scheduler:canonical",
        "command": command,
        "handler_binding": binding,
        "task_before": SimpleNamespace(state=SchedulerTaskState.READY),
        "task_running": SimpleNamespace(
            state=SchedulerTaskState.RUNNING,
            task_ref="scheduler-task:test-1",
            command_ref=command.command_ref,
        ),
        "attempt": SimpleNamespace(
            attempt_ref="scheduler-attempt:test-1",
            number=1,
            deadline_at="2026-07-19T10:06:00Z",
        ),
        "transition": SimpleNamespace(),
        "reservation": SimpleNamespace(
            reservation_ref="scheduler-reservation:test-1"
        ),
        "budget_mutation": SimpleNamespace(),
        "launch_commit": SimpleNamespace(
            transaction_ref="scheduler-launch-transaction:test-1",
            committed_at="2026-07-19T10:01:00Z",
        ),
        "ticket_digest": "sha256:" + "a" * 64,
    }
    for name, value in values.items():
        object.__setattr__(ticket, name, value)
    return ticket


def test_create_and_start_publish_advanced_information_without_execute() -> None:
    ticket = _ticket()
    dependency = object()
    factory = ExplicitSchedulerHandlerFactory(
        {_Handler.HANDLER_REF: lambda binding, value: _Handler(dependency)}
    )
    sink = _Sink()
    service = SchedulerHandlerInstanceLifecycleService()

    created = service.create(
        ticket=ticket,
        factory=factory,
        information_sink=sink,
        created_at="2026-07-19T10:01:01Z",
    )
    lease = service.start(
        created=created,
        information_sink=sink,
        started_at="2026-07-19T10:01:02Z",
    )

    assert isinstance(created.handler, _Handler)
    assert created.handler.dependency is dependency
    assert created.handler.execute_count == 0
    assert [notice.phase for notice in sink.notices] == [
        HandlerLifecyclePhase.CREATED,
        HandlerLifecyclePhase.STARTED,
    ]
    assert "scheduler-task:test-1" in sink.notices[0].text
    assert "tentative 1" in sink.notices[1].text
    assert lease.context.handler_instance_ref == created.instance_ref
    assert lease.context.task_ref == ticket.task_running.task_ref


def test_information_sink_failure_never_cancels_scheduler_decision() -> None:
    ticket = _ticket()
    factory = ExplicitSchedulerHandlerFactory(
        {_Handler.HANDLER_REF: lambda binding, value: _Handler(object())}
    )
    sink = _Sink(fail=True)
    service = SchedulerHandlerInstanceLifecycleService()

    created = service.create(
        ticket=ticket,
        factory=factory,
        information_sink=sink,
        created_at="2026-07-19T10:01:01Z",
    )
    lease = service.start(
        created=created,
        information_sink=sink,
        started_at="2026-07-19T10:01:02Z",
    )

    assert created.publication.published is False
    assert created.publication.error_type == "OSError"
    assert lease.publication.published is False
    assert created.handler.execute_count == 0


def test_wrong_instance_type_is_rejected_and_failed_notice_is_published() -> None:
    ticket = _ticket()
    factory = ExplicitSchedulerHandlerFactory(
        {_Handler.HANDLER_REF: lambda binding, value: object()}
    )
    sink = _Sink()

    with pytest.raises(SchedulerHandlerInstanceLifecycleError):
        SchedulerHandlerInstanceLifecycleService().create(
            ticket=ticket,
            factory=factory,
            information_sink=sink,
            created_at="2026-07-19T10:01:01Z",
        )

    assert sink.notices[-1].phase is HandlerLifecyclePhase.FAILED


def test_start_refuses_expired_deadline_without_started_notice() -> None:
    ticket = _ticket()
    factory = ExplicitSchedulerHandlerFactory(
        {_Handler.HANDLER_REF: lambda binding, value: _Handler(object())}
    )
    sink = _Sink()
    service = SchedulerHandlerInstanceLifecycleService()
    created = service.create(
        ticket=ticket,
        factory=factory,
        information_sink=sink,
        created_at="2026-07-19T10:01:01Z",
    )

    with pytest.raises(SchedulerHandlerInstanceLifecycleError):
        service.start(
            created=created,
            information_sink=sink,
            started_at="2026-07-19T10:06:00Z",
        )

    assert [notice.phase for notice in sink.notices] == [
        HandlerLifecyclePhase.CREATED
    ]
    assert created.handler.execute_count == 0
