from __future__ import annotations

import pytest

from src.context.context_variation_core import (
    ContextExplorationBudget,
    ContextExplorationResult,
    ContextVariationAxis,
    ContextVariationObjective,
    build_context_exploration_plan,
    build_context_reduction_plan,
    build_inference_context_draft,
)


def test_context_exploration_budget_is_bounded() -> None:
    with pytest.raises(ValueError, match="max_variants must be > 0"):
        ContextExplorationBudget(
            max_variants=0,
            max_depth=1,
            max_specialist_calls=1,
            max_retrievals=1,
            max_wall_time_s=1.0,
        )


def test_context_exploration_plan_builds_reference_only_variants() -> None:
    objective = ContextVariationObjective(
        objective_id="obj-baby-fork",
        title="Baby fork project",
        statement="Explore a safer fork for a baby project item.",
        source_ref="github:artifact:copilot-first-pass",
        parent_context_ref="ctx:project:fork",
    )
    axes = (
        ContextVariationAxis(
            axis_id="safety",
            label="Safety",
            question="Which context helps evaluate child safety constraints?",
            tags=("child", "norms"),
        ),
        ContextVariationAxis(
            axis_id="material",
            label="Material",
            question="Which material context should be recalled?",
            tags=("food", "fabrication"),
        ),
    )
    budget = ContextExplorationBudget(
        max_variants=1,
        max_depth=2,
        max_specialist_calls=4,
        max_retrievals=8,
        max_wall_time_s=20.0,
    )

    plan = build_context_exploration_plan(
        plan_id="plan-001",
        objective=objective,
        axes=axes,
        budget=budget,
        base_context_refs=("sql:fact:project-constraint",),
        payload_refs=("artifact:github:baby-fork",),
        specialist_refs=("specialist:safety",),
    )

    assert len(plan.candidates) == 1
    candidate = plan.candidates[0]
    assert candidate.variant_id == "plan-001:variant:01:safety"
    assert candidate.context_refs == ("sql:fact:project-constraint",)
    assert candidate.payload_refs == ("artifact:github:baby-fork",)
    assert candidate.specialist_refs == ("specialist:safety",)
    assert candidate.trajectory.steps[0].capability_hint == "context.axis.explore"
    assert "artifact:github:baby-fork" in candidate.trajectory.steps[0].input_refs


def test_context_variation_refs_reject_embedded_payloads() -> None:
    objective = ContextVariationObjective(
        objective_id="obj",
        title="Objective",
        statement="Statement",
    )
    axis = ContextVariationAxis(axis_id="axis", label="Axis", question="Question")
    budget = ContextExplorationBudget(
        max_variants=1,
        max_depth=1,
        max_specialist_calls=1,
        max_retrievals=1,
        max_wall_time_s=1.0,
    )

    with pytest.raises(ValueError, match="typed reference"):
        build_context_exploration_plan(
            plan_id="plan",
            objective=objective,
            axes=(axis,),
            budget=budget,
            payload_refs=("the heavy payload itself",),
        )


def test_context_reduction_plan_keeps_results_as_refs() -> None:
    objective = ContextVariationObjective(
        objective_id="obj",
        title="Objective",
        statement="Statement",
        source_ref="github:item:1",
    )
    axis = ContextVariationAxis(axis_id="axis", label="Axis", question="Question")
    budget = ContextExplorationBudget(
        max_variants=1,
        max_depth=1,
        max_specialist_calls=1,
        max_retrievals=1,
        max_wall_time_s=1.0,
    )
    plan = build_context_exploration_plan(
        plan_id="plan",
        objective=objective,
        axes=(axis,),
        budget=budget,
    )
    result = ContextExplorationResult(
        result_id="result-1",
        plan_id="plan",
        variant_id=plan.candidates[0].variant_id,
        produced_context_refs=("ctx:variant:axis",),
        observations=("safety constraints recalled",),
        score_hint=0.7,
    )

    reduction = build_context_reduction_plan(
        reduction_id="reduce-1",
        plan=plan,
        results=(result,),
    )

    assert reduction.result_refs == ("ctx-result:result-1",)
    assert reduction.target_kind == "inference_context_draft"


def test_inference_context_draft_deduplicates_context_refs() -> None:
    objective = ContextVariationObjective(
        objective_id="obj",
        title="Objective",
        statement="Statement",
    )
    axis = ContextVariationAxis(axis_id="axis", label="Axis", question="Question")
    budget = ContextExplorationBudget(
        max_variants=1,
        max_depth=1,
        max_specialist_calls=1,
        max_retrievals=1,
        max_wall_time_s=1.0,
    )
    plan = build_context_exploration_plan(
        plan_id="plan",
        objective=objective,
        axes=(axis,),
        budget=budget,
    )
    result = ContextExplorationResult(
        result_id="result-1",
        plan_id="plan",
        variant_id=plan.candidates[0].variant_id,
        produced_context_refs=("ctx:a", "ctx:b", "ctx:a"),
    )

    draft = build_inference_context_draft(
        draft_id="draft-1",
        plan=plan,
        results=(result,),
        rationale="Keep the safety and material facts for the next specialist call.",
    )

    assert draft.context_refs == ("ctx:a", "ctx:b")
    assert draft.selected_variant_ids == (plan.candidates[0].variant_id,)
    assert draft.to_mapping()["draft_id"] == "draft-1"
