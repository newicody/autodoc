from __future__ import annotations

import asyncio
from types import SimpleNamespace

from kernel.scheduler_handler_catalog import SchedulerHandlerCatalog
from kernel.scheduler_handler_contract import (
    HandlerExecutionPolicy,
    HandlerIdempotencyKind,
    HandlerInformation,
    HandlerLifecyclePhase,
    SchedulerHandler,
)
from kernel.scheduler_handler_execution import (
    SchedulerHandlerExecutionService,
    SchedulerHandlerExecutionStatus,
    SchedulerHandlerFailureClassification,
    SchedulerHandlerResultProjection,
)
from kernel.scheduler_handler_instance_lifecycle import (
    ExplicitSchedulerHandlerFactory,
    SchedulerHandlerInstanceLifecycleService,
)
from kernel.scheduler_task_launch_preparation import SchedulerHandlerLaunchTicket
from kernel.scheduler_task_model import (
    SchedulerTask,
    SchedulerTaskAttemptState,
    SchedulerTaskState,
)


class _Command:
    def __init__(self, command_ref: str) -> None:
        self.command_ref = command_ref


class _Result:
    def __init__(self, ref: str = "evidence:test-result") -> None:
        self.ref = ref


class _OtherResult:
    pass


class _Handler(SchedulerHandler[_Command, _Result]):
    HANDLER_REF = "handler:test-execution"
    CAPABILITY_REF = "capability:test-execution"
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
        title="Handler d'exécution",
        summary="Valide l'issue contrôlée.",
        succeeded_text="{handler_title} a produit {result_ref} en {elapsed_ms} ms.",
        failed_text="{handler_title} a échoué: {error_type}.",
        cancelled_text="{handler_title} a été annulé.",
        closed_text="{handler_title} a été fermé.",
    )

    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.execute_count = 0

    async def execute(self, command: _Command, context: object) -> _Result:
        self.execute_count += 1
        if self.mode == "failure":
            raise OSError("backend indisponible")
        if self.mode == "wait":
            await asyncio.Event().wait()
        if self.mode == "wrong-result":
            return _OtherResult()  # type: ignore[return-value]
        return _Result()


class _Sink:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.notices = []

    def publish(self, notice) -> None:
        if self.fail:
            raise OSError("sink indisponible")
        self.notices.append(notice)


class _Projector:
    def project(self, *, result: _Result, lease) -> SchedulerHandlerResultProjection:
        return SchedulerHandlerResultProjection(
            result_type_ref="result-type:test-execution",
            evidence_refs=(result.ref,),
        )


class _Classifier:
    def __init__(self, *, retryable: bool = True) -> None:
        self.retryable = retryable

    def classify(self, *, error: BaseException, lease) -> SchedulerHandlerFailureClassification:
        return SchedulerHandlerFailureClassification(
            error_type=type(error).__name__,
            message=str(error) or type(error).__name__,
            retryable=self.retryable,
        )


class _Closer:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    async def close(self, *, handler, lease) -> None:
        self.calls += 1
        if self.fail:
            raise OSError("fermeture impossible")


class _Cancellation:
    def __init__(self, cancelled: bool) -> None:
        self.cancelled = cancelled
        self.event = asyncio.Event()
        if cancelled:
            self.event.set()

    def is_cancelled(self) -> bool:
        return self.cancelled

    async def wait(self) -> None:
        await self.event.wait()


class _Clock:
    def __init__(self, *values: str) -> None:
        self.values = iter(values)

    def __call__(self) -> str:
        return next(self.values)


def _lease(mode: str = "success"):
    command = _Command("scheduler-command:test-execution")
    binding = SchedulerHandlerCatalog((_Handler,)).resolve_for(
        command,
        capability_ref=_Handler.CAPABILITY_REF,
        contract_version=1,
    )
    planned = SchedulerTask.plan(
        task_ref="scheduler-task:test-execution",
        command_ref=command.command_ref,
        task_kind_ref="task-kind:test-execution",
        capability_ref=_Handler.CAPABILITY_REF,
        contract_version=1,
        priority=60,
        max_attempts=2,
        created_at="2026-07-19T10:00:00Z",
    )
    ready = planned.mark_ready(
        dependency_states={},
        occurred_at="2026-07-19T10:00:01Z",
        actor_ref="scheduler:canonical",
        cause_ref="scheduler-cause:ready",
    ).task
    started = ready.start_attempt(
        handler_ref=_Handler.HANDLER_REF,
        contract_version=1,
        started_at="2026-07-19T10:01:00Z",
        deadline_at="2026-07-19T10:06:00Z",
        actor_ref="scheduler:canonical",
        cause_ref="scheduler-cause:start",
        effective_priority=70,
    )
    ticket = object.__new__(SchedulerHandlerLaunchTicket)
    values = {
        "schema": "missipy.scheduler.handler_launch_ticket.v1",
        "ticket_ref": "scheduler-handler-launch:test-execution",
        "scheduler_ref": "scheduler:canonical",
        "command": command,
        "handler_binding": binding,
        "task_before": ready,
        "task_running": started.task,
        "attempt": started.attempt,
        "transition": started.transition,
        "reservation": SimpleNamespace(
            reservation_ref="scheduler-reservation:test-execution"
        ),
        "budget_mutation": SimpleNamespace(),
        "launch_commit": SimpleNamespace(
            transaction_ref="scheduler-launch-transaction:test-execution",
            committed_at="2026-07-19T10:01:00Z",
        ),
        "ticket_digest": "sha256:" + "a" * 64,
    }
    for name, value in values.items():
        object.__setattr__(ticket, name, value)
    sink = _Sink()
    lifecycle = SchedulerHandlerInstanceLifecycleService()
    created = lifecycle.create(
        ticket=ticket,
        factory=ExplicitSchedulerHandlerFactory(
            {_Handler.HANDLER_REF: lambda binding, value: _Handler(mode)}
        ),
        information_sink=sink,
        created_at="2026-07-19T10:01:01Z",
    )
    lease = lifecycle.start(
        created=created,
        information_sink=sink,
        started_at="2026-07-19T10:01:02Z",
    )
    return lease, sink


def _run(lease, sink, *, closer=None, cancellation=None, classifier=None, clock=None):
    return asyncio.run(
        SchedulerHandlerExecutionService().execute(
            lease=lease,
            result_projector=_Projector(),
            failure_classifier=classifier or _Classifier(),
            closer=closer or _Closer(),
            information_sink=sink,
            utc_now=clock
            or _Clock("2026-07-19T10:01:03Z", "2026-07-19T10:01:04Z"),
            cancellation_signal=cancellation,
        )
    )


def test_success_executes_once_completes_task_and_closes() -> None:
    lease, sink = _lease()
    closer = _Closer()

    outcome = _run(lease, sink, closer=closer)

    assert outcome.status is SchedulerHandlerExecutionStatus.SUCCEEDED
    assert outcome.task_state is SchedulerTaskState.COMPLETED
    assert outcome.completion is not None
    assert outcome.completion.attempt.state is SchedulerTaskAttemptState.SUCCEEDED
    assert isinstance(outcome.handler_result, _Result)
    assert lease.created.handler.execute_count == 1
    assert closer.calls == 1
    assert outcome.close_receipt.closed is True
    assert [notice.phase for notice in sink.notices][-2:] == [
        HandlerLifecyclePhase.SUCCEEDED,
        HandlerLifecyclePhase.CLOSED,
    ]


def test_retryable_failure_returns_retry_wait_and_always_closes() -> None:
    lease, sink = _lease("failure")
    closer = _Closer()

    outcome = _run(lease, sink, closer=closer, classifier=_Classifier(retryable=True))

    assert outcome.status is SchedulerHandlerExecutionStatus.RETRY_WAIT
    assert outcome.task_state is SchedulerTaskState.RETRY_WAIT
    assert outcome.failure_outcome is not None
    assert outcome.failure_outcome.failure.error_type == "OSError"
    assert closer.calls == 1
    assert [notice.phase for notice in sink.notices][-2:] == [
        HandlerLifecyclePhase.FAILED,
        HandlerLifecyclePhase.CLOSED,
    ]


def test_pre_requested_cancellation_never_calls_handler() -> None:
    lease, sink = _lease("wait")

    outcome = _run(
        lease,
        sink,
        cancellation=_Cancellation(True),
    )

    assert outcome.status is SchedulerHandlerExecutionStatus.CANCELLED
    assert outcome.task_state is SchedulerTaskState.CANCELLED
    assert outcome.interruption is not None
    assert outcome.interruption.attempt.state is SchedulerTaskAttemptState.CANCELLED
    assert lease.created.handler.execute_count == 0
    assert [notice.phase for notice in sink.notices][-2:] == [
        HandlerLifecyclePhase.CANCELLED,
        HandlerLifecyclePhase.CLOSED,
    ]


def test_expired_deadline_returns_timed_out_without_execute() -> None:
    lease, sink = _lease("wait")

    outcome = _run(
        lease,
        sink,
        clock=_Clock("2026-07-19T10:06:00Z", "2026-07-19T10:06:00Z"),
    )

    assert outcome.status is SchedulerHandlerExecutionStatus.TIMED_OUT
    assert outcome.task_state is SchedulerTaskState.TIMED_OUT
    assert outcome.interruption is not None
    assert outcome.interruption.attempt.state is SchedulerTaskAttemptState.TIMED_OUT
    assert lease.created.handler.execute_count == 0


def test_wrong_result_type_is_a_classified_failure() -> None:
    lease, sink = _lease("wrong-result")

    outcome = _run(lease, sink, classifier=_Classifier(retryable=False))

    assert outcome.status is SchedulerHandlerExecutionStatus.FAILED
    assert outcome.failure_outcome is not None
    assert outcome.failure_outcome.failure.error_type == "TypeError"
    assert outcome.handler_result is None


def test_close_failure_is_recorded_without_rewriting_success() -> None:
    lease, sink = _lease()

    outcome = _run(lease, sink, closer=_Closer(fail=True))

    assert outcome.status is SchedulerHandlerExecutionStatus.SUCCEEDED
    assert outcome.task_state is SchedulerTaskState.COMPLETED
    assert outcome.close_receipt.closed is False
    assert outcome.close_receipt.error_type == "OSError"


def test_sink_failure_remains_observation_only() -> None:
    lease, _sink = _lease()
    sink = _Sink(fail=True)

    outcome = _run(lease, sink)

    assert outcome.status is SchedulerHandlerExecutionStatus.SUCCEEDED
    assert outcome.finished_publication.published is False
    assert outcome.closed_publication.published is False
