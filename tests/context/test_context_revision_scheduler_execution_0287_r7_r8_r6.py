from __future__ import annotations

import asyncio
from dataclasses import replace

import pytest

from contracts.event import Event, EventType
from context.context_revision_scheduler_execution_0287 import (
    CONTEXT_IMPACT_EXECUTION_AUTHORIZATION_SCHEMA,
    CONTEXT_IMPACT_EXECUTION_COMMAND_SCHEMA,
    CONTEXT_IMPACT_EXECUTION_TARGET_SCHEMA,
    TASK_CONTEXT_RUNTIME_STATE_SCHEMA,
    ContextImpactExecutionAuthorization,
    ContextImpactExecutionCommand,
    ContextImpactExecutionError,
    ContextImpactExecutionTarget,
    InMemorySchedulerTaskMutationPort,
    SchedulerContextImpactExecutionHandler,
    TaskContextRuntimeState,
    build_context_impact_execution_authorization,
    build_context_impact_execution_command,
    compute_plan_sha256,
    execute_context_impact_command,
)
from context.context_revision_task_impact_0287 import (
    CONTEXT_IMPACT_PLAN_SCHEMA,
    SCHEDULER_CONTEXT_IMPACT_DECISION_SCHEMA,
    ContextImpactPlan,
    SchedulerContextImpactDecision,
)

NOW = "2026-07-16T00:00:00Z"
FROM = "context-revision:from"
TARGET = "context-revision:target"
POLICY = "scheduler-policy:context-impact"
POLICY_DECISION = "policy-decision:approved"


def _decision(
    *,
    task_ref: str = "specialist-task:one",
    state: str = "queued",
    action: str = "rebind_before_start",
    checkpoint_ref: str | None = None,
    fork_task_ref: str | None = None,
) -> SchedulerContextImpactDecision:
    suffix = task_ref.rsplit(":", 1)[-1]
    return SchedulerContextImpactDecision(
        schema=SCHEDULER_CONTEXT_IMPACT_DECISION_SCHEMA,
        decision_ref=f"scheduler-decision:{suffix}-{action}",
        scheduler_policy_ref=POLICY,
        assessment_ref=f"context-impact-assessment:{suffix}",
        task_ref=task_ref,
        execution_state=state,
        action=action,
        from_revision_ref=FROM,
        target_revision_ref=TARGET,
        reason="test decision",
        checkpoint_ref=checkpoint_ref,
        fork_task_ref=fork_task_ref,
    )


def _plan(*decisions: SchedulerContextImpactDecision) -> ContextImpactPlan:
    return ContextImpactPlan(
        schema=CONTEXT_IMPACT_PLAN_SCHEMA,
        plan_ref="context-impact-plan:test",
        change_ref="context-change:test",
        decisions=tuple(decisions),
    )


def _state(
    *,
    task_ref: str = "specialist-task:one",
    state: str = "queued",
    version: int = 0,
    checkpoint_ref: str | None = None,
    result_ref: str | None = None,
) -> TaskContextRuntimeState:
    return TaskContextRuntimeState(
        schema=TASK_CONTEXT_RUNTIME_STATE_SCHEMA,
        task_ref=task_ref,
        plan_ref="specialist-task-plan:test",
        execution_ref=f"task-execution:{task_ref.rsplit(':', 1)[-1]}",
        execution_state=state,
        bound_revision_ref=FROM,
        state_version=version,
        specialist_ref="specialist:test",
        laboratory_ref="laboratory:one",
        conversation_ref="laboratory-conversation:test",
        return_route_ref="route:return",
        active_checkpoint_ref=checkpoint_ref,
        result_ref=result_ref,
    )


def _target(
    *,
    task_ref: str = "specialist-task:one",
    version: int = 0,
    notify: tuple[str, ...] = ("laboratory:two",),
    route: bool = False,
) -> ContextImpactExecutionTarget:
    return ContextImpactExecutionTarget(
        schema=CONTEXT_IMPACT_EXECUTION_TARGET_SCHEMA,
        task_ref=task_ref,
        expected_state_version=version,
        notification_laboratory_refs=notify,
        route_transition_required=route,
        route_id="context-impact-route" if route else None,
    )


def _command(
    plan: ContextImpactPlan,
    *targets: ContextImpactExecutionTarget,
) -> ContextImpactExecutionCommand:
    auth = build_context_impact_execution_authorization(
        plan=plan,
        scheduler_policy_ref=POLICY,
        policy_decision_id=POLICY_DECISION,
        authorized_at=NOW,
    )
    return build_context_impact_execution_command(
        plan=plan,
        authorization=auth,
        targets=targets,
        requested_at=NOW,
    )


def _execute(command, port, *, route_requester=None):
    observed: list[Event] = []
    scheduled: list[Event] = []

    async def publish(event: Event) -> None:
        observed.append(event)

    async def emit(event: Event) -> None:
        scheduled.append(event)

    report = asyncio.run(
        execute_context_impact_command(
            command=command,
            task_mutation_port=port,
            event_bus_publish=publish,
            scheduler_emit=emit,
            route_requester=route_requester,
        )
    )
    return report, observed, scheduled


def test_queued_task_rebinds_and_notifies_laboratory() -> None:
    decision = _decision()
    plan = _plan(decision)
    port = InMemorySchedulerTaskMutationPort((_state(),))

    report, observed, scheduled = _execute(
        _command(plan, _target()),
        port,
    )

    current = port.state("specialist-task:one")
    assert current.bound_revision_ref == TARGET
    assert current.state_version == 1
    assert report.items[0].route_status == "not_requested"
    assert observed[0].type is EventType.CONTEXT_IMPACT_EXECUTION_RESULT
    assert scheduled[0].type is EventType.LABORATORY_CONTEXT_UPDATE
    assert scheduled[0].dest == "laboratory:two"


def test_snapshot_continues_on_old_revision_but_marks_staleness() -> None:
    decision = _decision(state="running", action="continue_snapshot")
    plan = _plan(decision)
    port = InMemorySchedulerTaskMutationPort((_state(state="running"),))

    _execute(_command(plan, _target()), port)

    current = port.state("specialist-task:one")
    assert current.bound_revision_ref == FROM
    assert current.stale_against_revision_ref == TARGET


def test_checkpoint_rebase_uses_route_adapter_only_when_requested() -> None:
    checkpoint = "checkpoint:safe"
    decision = _decision(
        state="checkpointed",
        action="rebase_at_checkpoint",
        checkpoint_ref=checkpoint,
    )
    plan = _plan(decision)
    port = InMemorySchedulerTaskMutationPort(
        (_state(state="checkpointed", checkpoint_ref=checkpoint),)
    )
    requests: list[dict[str, object]] = []

    def route_requester(request):
        requests.append(dict(request))
        return {
            "status": "ready",
            "route_handle": "context-impact-ready",
            "policy_decision_id": POLICY_DECISION,
        }

    report, _, _ = _execute(
        _command(plan, _target(route=True)),
        port,
        route_requester=route_requester,
    )

    assert len(requests) == 1
    assert requests[0]["schema"] == "missipy.scheduler.route_adapter_request.v1"
    assert requests[0]["authorized"] is True
    assert report.items[0].route_ref == "route:context-impact-ready"
    assert port.state("specialist-task:one").route_ref == report.items[0].route_ref


def test_route_adapter_is_not_called_without_transport_transition() -> None:
    decision = _decision()
    plan = _plan(decision)
    port = InMemorySchedulerTaskMutationPort((_state(),))

    def route_requester(_request):
        raise AssertionError("route adapter must not be called")

    _execute(
        _command(plan, _target(route=False)),
        port,
        route_requester=route_requester,
    )


def test_restart_is_idempotent_on_mutation_replay() -> None:
    decision = _decision(state="running", action="restart_task")
    plan = _plan(decision)
    port = InMemorySchedulerTaskMutationPort((_state(state="running"),))
    command = _command(plan, _target())

    first, _, _ = _execute(command, port)
    second, _, _ = _execute(command, port)

    assert first.items[0].mutation_receipt.replay is False
    assert second.items[0].mutation_receipt.replay is True
    assert port.state("specialist-task:one").state_version == 1


def test_fork_preserves_source_and_creates_target_branch() -> None:
    fork_ref = "specialist-task:forked"
    decision = _decision(
        state="running",
        action="fork_task",
        fork_task_ref=fork_ref,
    )
    plan = _plan(decision)
    port = InMemorySchedulerTaskMutationPort((_state(state="running"),))

    report, _, _ = _execute(_command(plan, _target()), port)

    source = port.state("specialist-task:one")
    forked = port.state(fork_ref)
    assert source.bound_revision_ref == FROM
    assert source.stale_against_revision_ref == TARGET
    assert forked.bound_revision_ref == TARGET
    assert forked.execution_state == "queued"
    assert report.items[0].mutation_receipt.fork_task_ref == fork_ref


def test_completed_result_is_marked_stale_not_rewritten() -> None:
    decision = _decision(state="completed", action="mark_result_stale")
    plan = _plan(decision)
    port = InMemorySchedulerTaskMutationPort(
        (_state(state="completed", result_ref="result:one"),)
    )

    _execute(_command(plan, _target()), port)

    current = port.state("specialist-task:one")
    assert current.result_ref == "result:one"
    assert current.bound_revision_ref == FROM
    assert current.stale_against_revision_ref == TARGET


def test_state_version_drift_fails_closed() -> None:
    decision = _decision()
    plan = _plan(decision)
    port = InMemorySchedulerTaskMutationPort((_state(version=2),))

    with pytest.raises(ContextImpactExecutionError, match="state version"):
        _execute(_command(plan, _target(version=1)), port)


def test_wrong_route_policy_reply_fails_closed() -> None:
    checkpoint = "checkpoint:safe"
    decision = _decision(
        state="checkpointed",
        action="rebase_at_checkpoint",
        checkpoint_ref=checkpoint,
    )
    plan = _plan(decision)
    port = InMemorySchedulerTaskMutationPort(
        (_state(state="checkpointed", checkpoint_ref=checkpoint),)
    )

    def route_requester(_request):
        return {
            "status": "ready",
            "route_handle": "bad",
            "policy_decision_id": "policy-decision:other",
        }

    with pytest.raises(ContextImpactExecutionError, match="policy decision"):
        _execute(
            _command(plan, _target(route=True)),
            port,
            route_requester=route_requester,
        )


def test_authorization_digest_mismatch_is_rejected() -> None:
    plan = _plan(_decision())
    auth = ContextImpactExecutionAuthorization(
        schema=CONTEXT_IMPACT_EXECUTION_AUTHORIZATION_SCHEMA,
        authorization_ref="authorization:test",
        plan_ref=plan.plan_ref,
        plan_sha256="0" * 64,
        scheduler_policy_ref=POLICY,
        policy_decision_id=POLICY_DECISION,
        authorized=True,
        authorized_at=NOW,
    )

    with pytest.raises(ContextImpactExecutionError, match="digest mismatch"):
        ContextImpactExecutionCommand(
            schema=CONTEXT_IMPACT_EXECUTION_COMMAND_SCHEMA,
            command_ref="context-impact-execution:test",
            plan=plan,
            authorization=auth,
            targets=(_target(),),
            requested_at=NOW,
        )


def test_handler_uses_existing_dispatcher_event_boundary() -> None:
    plan = _plan(_decision())
    port = InMemorySchedulerTaskMutationPort((_state(),))
    observed: list[Event] = []
    scheduled: list[Event] = []

    async def publish(event: Event) -> None:
        observed.append(event)

    async def emit(event: Event) -> None:
        scheduled.append(event)

    handler = SchedulerContextImpactExecutionHandler(
        task_mutation_port=port,
        event_bus_publish=publish,
        scheduler_emit=emit,
    )
    event = Event(
        EventType.CONTEXT_IMPACT_EXECUTION,
        source="test",
        payload=_command(plan, _target()),
    )

    report = asyncio.run(handler.handle(event))

    assert report.plan_ref == plan.plan_ref
    assert observed and scheduled


def test_plan_digest_is_deterministic() -> None:
    plan = _plan(_decision())
    assert compute_plan_sha256(plan) == compute_plan_sha256(plan)
    assert len(compute_plan_sha256(plan)) == 64
