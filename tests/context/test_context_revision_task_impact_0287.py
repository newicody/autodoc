from __future__ import annotations

import pytest

from context.context_revision_sql_authority_0287 import (
    CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
    CONTEXT_REVISION_SCHEMA,
    ContextRevision,
    ContextRevisionMembership,
)
from context.context_revision_task_impact_0287 import (
    CONTEXT_IMPACT_PLAN_SCHEMA,
    CONTEXT_REVISION_CHANGE_SET_SCHEMA,
    SCHEDULER_CONTEXT_IMPACT_DECISION_SCHEMA,
    TASK_CONTEXT_BINDING_SCHEMA,
    ContextTaskImpactError,
    assess_task_context_impact,
    build_context_impact_plan,
    build_context_revision_change_set,
    build_task_context_binding,
    decide_task_context_impact,
)
from context.specialist_multitask_model_0287 import (
    SPECIALIST_TASK_REQUEST_SCHEMA,
    SpecialistTaskRequest,
)


def _membership(
    object_ref: str,
    state: str = "active",
    replacement_ref: str | None = None,
) -> ContextRevisionMembership:
    return ContextRevisionMembership(
        schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
        object_ref=object_ref,
        state=state,
        replacement_ref=replacement_ref,
    )


def _revision(
    ref: str,
    *,
    parent_refs: tuple[str, ...] = (),
    memberships: tuple[ContextRevisionMembership, ...] = (),
    significance: str = "minor",
) -> ContextRevision:
    return ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref=ref,
        context_ref="ctx:research-1",
        parent_revision_refs=parent_refs,
        memberships=memberships,
        validation_status="accepted",
        significance=significance,
        evidence_refs=("artifact:evidence-1",),
        created_at="2026-07-16T00:00:00Z",
    )


def _task(context_refs: tuple[str, ...] = ("sql:object-a",)) -> SpecialistTaskRequest:
    return SpecialistTaskRequest(
        schema=SPECIALIST_TASK_REQUEST_SCHEMA,
        task_ref="specialist-task:analysis-1",
        plan_ref="specialist-task-plan:plan-1",
        mission_ref="mission:research-1",
        specialist_ref="specialist:analyst-1",
        task_type_ref="specialist-task-type:analysis.deep",
        capability="analysis.deep",
        objective="Analyse the research material.",
        input_contract_ref="contract:research-input.v1",
        expected_output_contract_ref="contract:analysis-output.v1",
        conversation_ref="laboratory-conversation:conversation-1",
        return_route_ref="route:return-1",
        constraints=(),
        success_criteria=("Produce evidence-backed findings.",),
        context_refs=context_refs,
        idempotency_key="task-analysis-1",
    )


def _change() -> tuple[ContextRevision, ContextRevision, object]:
    previous = _revision(
        "context-revision:r1",
        memberships=(
            _membership("sql:object-a"),
            _membership("sql:object-b"),
        ),
    )
    current = _revision(
        "context-revision:r2",
        parent_refs=(previous.revision_ref,),
        significance="material",
        memberships=(
            _membership(
                "sql:object-a",
                "superseded",
                "sql:object-a-v2",
            ),
            _membership("sql:object-a-v2"),
            _membership("sql:object-b", "invalidated"),
            _membership("sql:object-c"),
        ),
    )
    return previous, current, build_context_revision_change_set(
        previous=previous,
        current=current,
    )


def test_change_set_detects_added_superseded_invalidated_and_replacement() -> None:
    _, _, change = _change()

    assert change.schema == CONTEXT_REVISION_CHANGE_SET_SCHEMA
    assert change.added_refs == ("sql:object-a-v2", "sql:object-c")
    assert change.superseded_refs == ("sql:object-a",)
    assert change.invalidated_refs == ("sql:object-b",)
    assert change.replacement_pairs == (("sql:object-a", "sql:object-a-v2"),)
    assert change.to_mapping()["route_generation_changed"] is False


def test_change_set_requires_direct_accepted_child_of_same_context() -> None:
    previous = _revision("context-revision:r1")
    unrelated = _revision("context-revision:r2")

    with pytest.raises(ContextTaskImpactError, match="directly descend"):
        build_context_revision_change_set(previous=previous, current=unrelated)


def test_task_binding_defaults_to_task_references_and_scheduler_ownership() -> None:
    previous, _, _ = _change()
    binding = build_task_context_binding(
        task=_task(),
        revision=previous,
        update_policy="snapshot",
    )

    assert binding.schema == TASK_CONTEXT_BINDING_SCHEMA
    assert binding.watched_refs == ("sql:object-a",)
    assert binding.to_mapping()["scheduler_owned"] is True


def test_selective_binding_is_affected_only_by_intersecting_refs() -> None:
    previous, _, change = _change()
    binding = build_task_context_binding(
        task=_task(("sql:unrelated",)),
        revision=previous,
        update_policy="notify_only",
    )
    assessment = assess_task_context_impact(binding=binding, change=change)

    assert assessment.affected is False
    assert assessment.matched_refs == ()


def test_snapshot_policy_keeps_running_task_on_original_revision() -> None:
    previous, _, change = _change()
    binding = build_task_context_binding(
        task=_task(),
        revision=previous,
        update_policy="snapshot",
    )
    assessment = assess_task_context_impact(binding=binding, change=change)
    decision = decide_task_context_impact(
        binding=binding,
        change=change,
        assessment=assessment,
        execution_state="running",
        scheduler_policy_ref="scheduler-policy:context-impact-v1",
    )

    assert decision.schema == SCHEDULER_CONTEXT_IMPACT_DECISION_SCHEMA
    assert decision.action == "continue_snapshot"
    assert decision.to_mapping()["action_executed"] is False
    assert decision.to_mapping()["route_changed"] is False


def test_queued_task_is_rebound_before_start_for_material_policy() -> None:
    previous, _, change = _change()
    binding = build_task_context_binding(
        task=_task(),
        revision=previous,
        update_policy="restart_on_material_change",
    )
    assessment = assess_task_context_impact(binding=binding, change=change)
    decision = decide_task_context_impact(
        binding=binding,
        change=change,
        assessment=assessment,
        execution_state="queued",
        scheduler_policy_ref="scheduler-policy:context-impact-v1",
    )

    assert decision.action == "rebind_before_start"


def test_checkpoint_rebase_waits_then_uses_declared_checkpoint() -> None:
    previous, _, change = _change()
    binding = build_task_context_binding(
        task=_task(),
        revision=previous,
        update_policy="checkpoint_rebase",
        checkpoint_refs=("checkpoint:iteration-100",),
    )
    assessment = assess_task_context_impact(binding=binding, change=change)
    waiting = decide_task_context_impact(
        binding=binding,
        change=change,
        assessment=assessment,
        execution_state="running",
        scheduler_policy_ref="scheduler-policy:context-impact-v1",
    )
    rebased = decide_task_context_impact(
        binding=binding,
        change=change,
        assessment=assessment,
        execution_state="checkpointed",
        scheduler_policy_ref="scheduler-policy:context-impact-v1",
        active_checkpoint_ref="checkpoint:iteration-100",
    )

    assert waiting.action == "wait_for_checkpoint"
    assert rebased.action == "rebase_at_checkpoint"
    assert rebased.checkpoint_ref == "checkpoint:iteration-100"


def test_restart_and_fork_policies_are_distinct_scheduler_proposals() -> None:
    previous, _, change = _change()
    task = _task()
    decisions = []
    for policy in ("restart_on_material_change", "fork_on_material_change"):
        binding = build_task_context_binding(
            task=task,
            revision=previous,
            update_policy=policy,
        )
        assessment = assess_task_context_impact(binding=binding, change=change)
        decisions.append(
            decide_task_context_impact(
                binding=binding,
                change=change,
                assessment=assessment,
                execution_state="running",
                scheduler_policy_ref="scheduler-policy:context-impact-v1",
            )
        )

    assert decisions[0].action == "restart_task"
    assert decisions[1].action == "fork_task"
    assert decisions[1].fork_task_ref is not None
    assert decisions[1].to_mapping()["task_created"] is False


def test_completed_task_is_marked_stale_without_deleting_its_result() -> None:
    previous, _, change = _change()
    binding = build_task_context_binding(
        task=_task(),
        revision=previous,
        update_policy="restart_on_material_change",
    )
    assessment = assess_task_context_impact(binding=binding, change=change)
    decision = decide_task_context_impact(
        binding=binding,
        change=change,
        assessment=assessment,
        execution_state="completed",
        scheduler_policy_ref="scheduler-policy:context-impact-v1",
    )

    assert decision.action == "mark_result_stale"
    assert decision.from_revision_ref == "context-revision:r1"
    assert decision.target_revision_ref == "context-revision:r2"


def test_ignore_noncritical_notifies_only_for_critical_change() -> None:
    previous = _revision(
        "context-revision:r1",
        memberships=(_membership("sql:object-a"),),
    )
    current = _revision(
        "context-revision:r2",
        parent_refs=(previous.revision_ref,),
        memberships=(
            _membership("sql:object-a", "invalidated"),
        ),
        significance="critical",
    )
    change = build_context_revision_change_set(previous=previous, current=current)
    binding = build_task_context_binding(
        task=_task(),
        revision=previous,
        update_policy="ignore_noncritical",
    )
    assessment = assess_task_context_impact(binding=binding, change=change)
    decision = decide_task_context_impact(
        binding=binding,
        change=change,
        assessment=assessment,
        execution_state="running",
        scheduler_policy_ref="scheduler-policy:context-impact-v1",
    )

    assert decision.action == "notify_only"


def test_context_impact_plan_is_deterministic_and_effect_free() -> None:
    previous, _, change = _change()
    task = _task()
    binding = build_task_context_binding(
        task=task,
        revision=previous,
        update_policy="snapshot",
    )
    assessment = assess_task_context_impact(binding=binding, change=change)
    decision = decide_task_context_impact(
        binding=binding,
        change=change,
        assessment=assessment,
        execution_state="running",
        scheduler_policy_ref="scheduler-policy:context-impact-v1",
    )
    plan = build_context_impact_plan(change=change, decisions=(decision,))

    assert plan.schema == CONTEXT_IMPACT_PLAN_SCHEMA
    assert plan.to_mapping()["executed"] is False
    assert plan.to_mapping()["controlproxy_is_transport_only"] is True
    assert plan.to_mapping()["action_counts"] == {"continue_snapshot": 1}
