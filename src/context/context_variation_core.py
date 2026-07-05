"""Context variability core contracts.

Phase 0114-r2 recenters the project on context variability.  The objects in
this module are intentionally pure contracts: they describe bounded context
exploration trajectories that the Scheduler can carry toward handlers without
learning backend or route-runtime details.

context variability is the project center.
Scheduler orchestrates context exploration jobs; it does not build variants itself.
MVTC remains future, not runtime in 0114-r2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

_ALLOWED_COST_HINTS = frozenset({"tiny", "small", "medium", "large"})
_REF_PREFIXES = (
    "sql:",
    "ctx:",
    "artifact:",
    "github:",
    "route:",
    "doc:",
    "event:",
    "specialist:",
    "qdrant:",
    "ctx-result:",
)


@dataclass(frozen=True, slots=True)
class ContextExplorationBudget:
    """Bounded budget for context exploration.

    This is a boundary guard: it prevents unbounded variation jobs without
    selecting the exploration strategy.  Strategy belongs to handlers and
    specialists, not to Scheduler.run().
    """

    max_variants: int
    max_depth: int
    max_specialist_calls: int
    max_retrievals: int
    max_wall_time_s: float

    def __post_init__(self) -> None:
        _require_positive_int("max_variants", self.max_variants)
        _require_positive_int("max_depth", self.max_depth)
        _require_positive_int("max_specialist_calls", self.max_specialist_calls)
        _require_positive_int("max_retrievals", self.max_retrievals)
        if self.max_wall_time_s <= 0:
            raise ValueError("max_wall_time_s must be > 0")

    def to_mapping(self) -> dict[str, int | float]:
        return {
            "max_variants": self.max_variants,
            "max_depth": self.max_depth,
            "max_specialist_calls": self.max_specialist_calls,
            "max_retrievals": self.max_retrievals,
            "max_wall_time_s": self.max_wall_time_s,
        }


@dataclass(frozen=True, slots=True)
class ContextVariationObjective:
    """User-facing objective that starts a context exploration."""

    objective_id: str
    title: str
    statement: str
    source_ref: str | None = None
    parent_context_ref: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty("objective_id", self.objective_id)
        _require_non_empty("title", self.title)
        _require_non_empty("statement", self.statement)
        _require_ref_or_none("source_ref", self.source_ref)
        _require_ref_or_none("parent_context_ref", self.parent_context_ref)

    def to_mapping(self) -> dict[str, str | None]:
        return {
            "objective_id": self.objective_id,
            "title": self.title,
            "statement": self.statement,
            "source_ref": self.source_ref,
            "parent_context_ref": self.parent_context_ref,
        }


@dataclass(frozen=True, slots=True)
class ContextVariationAxis:
    """One axis along which the context can vary."""

    axis_id: str
    label: str
    question: str
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty("axis_id", self.axis_id)
        _require_non_empty("label", self.label)
        _require_non_empty("question", self.question)
        object.__setattr__(self, "tags", _as_non_empty_tuple("tags", self.tags, allow_empty=True))

    def to_mapping(self) -> dict[str, str | list[str]]:
        return {
            "axis_id": self.axis_id,
            "label": self.label,
            "question": self.question,
            "tags": list(self.tags),
        }


@dataclass(frozen=True, slots=True)
class ContextTrajectoryStep:
    """A reference-only step in a context trajectory."""

    step_id: str
    capability_hint: str
    input_refs: tuple[str, ...] = ()
    expected_output_ref_kind: str = "ctx"
    note: str = ""

    def __post_init__(self) -> None:
        _require_non_empty("step_id", self.step_id)
        _require_non_empty("capability_hint", self.capability_hint)
        object.__setattr__(self, "input_refs", _validate_refs("input_refs", self.input_refs, allow_empty=True))
        _require_non_empty("expected_output_ref_kind", self.expected_output_ref_kind)

    def to_mapping(self) -> dict[str, str | list[str]]:
        return {
            "step_id": self.step_id,
            "capability_hint": self.capability_hint,
            "input_refs": list(self.input_refs),
            "expected_output_ref_kind": self.expected_output_ref_kind,
            "note": self.note,
        }


@dataclass(frozen=True, slots=True)
class ContextTrajectory:
    """A bounded path for exploring one or more context axes."""

    trajectory_id: str
    axis_ids: tuple[str, ...]
    steps: tuple[ContextTrajectoryStep, ...]
    rationale: str

    def __post_init__(self) -> None:
        _require_non_empty("trajectory_id", self.trajectory_id)
        object.__setattr__(self, "axis_ids", _as_non_empty_tuple("axis_ids", self.axis_ids))
        if not self.steps:
            raise ValueError("steps must not be empty")
        _require_non_empty("rationale", self.rationale)

    def to_mapping(self) -> dict[str, str | list[str] | list[dict[str, str | list[str]]]]:
        return {
            "trajectory_id": self.trajectory_id,
            "axis_ids": list(self.axis_ids),
            "steps": [step.to_mapping() for step in self.steps],
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class ContextVariantCandidate:
    """Candidate context variant produced from an objective and trajectory."""

    variant_id: str
    objective_id: str
    trajectory: ContextTrajectory
    context_refs: tuple[str, ...] = ()
    payload_refs: tuple[str, ...] = ()
    specialist_refs: tuple[str, ...] = ()
    cost_hint: str = "small"
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty("variant_id", self.variant_id)
        _require_non_empty("objective_id", self.objective_id)
        object.__setattr__(self, "context_refs", _validate_refs("context_refs", self.context_refs, allow_empty=True))
        object.__setattr__(self, "payload_refs", _validate_refs("payload_refs", self.payload_refs, allow_empty=True))
        object.__setattr__(self, "specialist_refs", _validate_refs("specialist_refs", self.specialist_refs, allow_empty=True))
        if self.cost_hint not in _ALLOWED_COST_HINTS:
            raise ValueError("cost_hint must be one of tiny, small, medium, large")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "objective_id": self.objective_id,
            "trajectory": self.trajectory.to_mapping(),
            "context_refs": list(self.context_refs),
            "payload_refs": list(self.payload_refs),
            "specialist_refs": list(self.specialist_refs),
            "cost_hint": self.cost_hint,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ContextExplorationPlan:
    """A bounded plan of context trajectories for handlers to execute."""

    plan_id: str
    objective: ContextVariationObjective
    axes: tuple[ContextVariationAxis, ...]
    candidates: tuple[ContextVariantCandidate, ...]
    budget: ContextExplorationBudget

    def __post_init__(self) -> None:
        _require_non_empty("plan_id", self.plan_id)
        if not self.axes:
            raise ValueError("axes must not be empty")
        if not self.candidates:
            raise ValueError("candidates must not be empty")
        if len(self.candidates) > self.budget.max_variants:
            raise ValueError("candidates exceed budget.max_variants")
        axis_ids = {axis.axis_id for axis in self.axes}
        for candidate in self.candidates:
            missing = set(candidate.trajectory.axis_ids) - axis_ids
            if missing:
                raise ValueError("candidate trajectory references unknown axis")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "objective": self.objective.to_mapping(),
            "axes": [axis.to_mapping() for axis in self.axes],
            "candidates": [candidate.to_mapping() for candidate in self.candidates],
            "budget": self.budget.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class ContextExplorationResult:
    """Result of executing one candidate trajectory."""

    result_id: str
    plan_id: str
    variant_id: str
    produced_context_refs: tuple[str, ...]
    observations: tuple[str, ...] = ()
    score_hint: float | None = None

    def __post_init__(self) -> None:
        _require_non_empty("result_id", self.result_id)
        _require_non_empty("plan_id", self.plan_id)
        _require_non_empty("variant_id", self.variant_id)
        object.__setattr__(self, "produced_context_refs", _validate_refs("produced_context_refs", self.produced_context_refs))
        object.__setattr__(self, "observations", _as_non_empty_tuple("observations", self.observations, allow_empty=True))
        if self.score_hint is not None and not 0.0 <= self.score_hint <= 1.0:
            raise ValueError("score_hint must be between 0.0 and 1.0")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "plan_id": self.plan_id,
            "variant_id": self.variant_id,
            "produced_context_refs": list(self.produced_context_refs),
            "observations": list(self.observations),
            "score_hint": self.score_hint,
        }


@dataclass(frozen=True, slots=True)
class ContextReductionPlan:
    """Reference-only reduction request that can produce an inference draft."""

    reduction_id: str
    plan_id: str
    result_refs: tuple[str, ...]
    target_kind: str = "inference_context_draft"

    def __post_init__(self) -> None:
        _require_non_empty("reduction_id", self.reduction_id)
        _require_non_empty("plan_id", self.plan_id)
        object.__setattr__(self, "result_refs", _validate_refs("result_refs", self.result_refs))
        _require_non_empty("target_kind", self.target_kind)

    def to_mapping(self) -> dict[str, str | list[str]]:
        return {
            "reduction_id": self.reduction_id,
            "plan_id": self.plan_id,
            "result_refs": list(self.result_refs),
            "target_kind": self.target_kind,
        }


@dataclass(frozen=True, slots=True)
class InferenceContextDraft:
    """Draft context packet built from selected exploration results."""

    draft_id: str
    plan_id: str
    selected_variant_ids: tuple[str, ...]
    context_refs: tuple[str, ...]
    rationale: str

    def __post_init__(self) -> None:
        _require_non_empty("draft_id", self.draft_id)
        _require_non_empty("plan_id", self.plan_id)
        object.__setattr__(self, "selected_variant_ids", _as_non_empty_tuple("selected_variant_ids", self.selected_variant_ids))
        object.__setattr__(self, "context_refs", _validate_refs("context_refs", self.context_refs))
        _require_non_empty("rationale", self.rationale)

    def to_mapping(self) -> dict[str, str | list[str]]:
        return {
            "draft_id": self.draft_id,
            "plan_id": self.plan_id,
            "selected_variant_ids": list(self.selected_variant_ids),
            "context_refs": list(self.context_refs),
            "rationale": self.rationale,
        }


def build_axis_trajectory_candidate(
    *,
    plan_id: str,
    objective: ContextVariationObjective,
    axis: ContextVariationAxis,
    ordinal: int,
    base_context_refs: tuple[str, ...] = (),
    payload_refs: tuple[str, ...] = (),
    specialist_refs: tuple[str, ...] = (),
    cost_hint: str = "small",
) -> ContextVariantCandidate:
    """Build a deterministic candidate for one context axis.

    The candidate remains reference-only.  Heavy documents, vectors, model
    outputs, or route payloads must stay behind refs handled by later adapters.
    """

    _require_non_empty("plan_id", plan_id)
    _require_positive_int("ordinal", ordinal)
    slug = _slug(axis.axis_id)
    step = ContextTrajectoryStep(
        step_id=f"step-{ordinal:02d}-{slug}",
        capability_hint="context.axis.explore",
        input_refs=tuple(ref for ref in (objective.source_ref, objective.parent_context_ref) if ref is not None)
        + tuple(base_context_refs)
        + tuple(payload_refs),
        expected_output_ref_kind="ctx",
        note=f"Explore axis {axis.axis_id} without embedding a heavy payload in the Scheduler event.",
    )
    trajectory = ContextTrajectory(
        trajectory_id=f"traj-{ordinal:02d}-{slug}",
        axis_ids=(axis.axis_id,),
        steps=(step,),
        rationale=f"Vary context around axis {axis.label}.",
    )
    return ContextVariantCandidate(
        variant_id=f"{plan_id}:variant:{ordinal:02d}:{slug}",
        objective_id=objective.objective_id,
        trajectory=trajectory,
        context_refs=base_context_refs,
        payload_refs=payload_refs,
        specialist_refs=specialist_refs,
        cost_hint=cost_hint,
        metadata=(("axis", axis.axis_id),),
    )


def build_context_exploration_plan(
    *,
    plan_id: str,
    objective: ContextVariationObjective,
    axes: tuple[ContextVariationAxis, ...],
    budget: ContextExplorationBudget,
    base_context_refs: tuple[str, ...] = (),
    payload_refs: tuple[str, ...] = (),
    specialist_refs: tuple[str, ...] = (),
    cost_hint: str = "small",
) -> ContextExplorationPlan:
    """Build a bounded deterministic exploration plan from axes."""

    if not axes:
        raise ValueError("axes must not be empty")
    selected_axes = axes[: budget.max_variants]
    candidates = tuple(
        build_axis_trajectory_candidate(
            plan_id=plan_id,
            objective=objective,
            axis=axis,
            ordinal=index,
            base_context_refs=base_context_refs,
            payload_refs=payload_refs,
            specialist_refs=specialist_refs,
            cost_hint=cost_hint,
        )
        for index, axis in enumerate(selected_axes, start=1)
    )
    return ContextExplorationPlan(
        plan_id=plan_id,
        objective=objective,
        axes=axes,
        candidates=candidates,
        budget=budget,
    )


def build_context_reduction_plan(
    *,
    reduction_id: str,
    plan: ContextExplorationPlan,
    results: tuple[ContextExplorationResult, ...],
) -> ContextReductionPlan:
    """Build a reference-only reduction plan from exploration results."""

    if not results:
        raise ValueError("results must not be empty")
    known_variants = {candidate.variant_id for candidate in plan.candidates}
    for result in results:
        if result.plan_id != plan.plan_id:
            raise ValueError("result plan_id does not match plan")
        if result.variant_id not in known_variants:
            raise ValueError("result variant_id is not part of plan")
    return ContextReductionPlan(
        reduction_id=reduction_id,
        plan_id=plan.plan_id,
        result_refs=tuple(f"ctx-result:{result.result_id}" for result in results),
    )


def build_inference_context_draft(
    *,
    draft_id: str,
    plan: ContextExplorationPlan,
    results: tuple[ContextExplorationResult, ...],
    rationale: str,
) -> InferenceContextDraft:
    """Build an inference context draft from selected exploration results."""

    if not results:
        raise ValueError("results must not be empty")
    selected_variant_ids: list[str] = []
    context_refs: list[str] = []
    for result in results:
        if result.plan_id != plan.plan_id:
            raise ValueError("result plan_id does not match plan")
        selected_variant_ids.append(result.variant_id)
        context_refs.extend(result.produced_context_refs)
    return InferenceContextDraft(
        draft_id=draft_id,
        plan_id=plan.plan_id,
        selected_variant_ids=tuple(selected_variant_ids),
        context_refs=tuple(dict.fromkeys(context_refs)),
        rationale=rationale,
    )


def _require_non_empty(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_positive_int(name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be > 0")


def _require_ref_or_none(name: str, value: str | None) -> None:
    if value is None:
        return
    _validate_ref(name, value)


def _validate_refs(name: str, values: tuple[str, ...], *, allow_empty: bool = False) -> tuple[str, ...]:
    if not values and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    refs = _as_non_empty_tuple(name, values, allow_empty=allow_empty)
    for value in refs:
        _validate_ref(name, value)
    return refs


def _validate_ref(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if not value.startswith(_REF_PREFIXES):
        raise ValueError(f"{name} must be a typed reference, not an embedded payload")


def _as_non_empty_tuple(name: str, values: tuple[str, ...], *, allow_empty: bool = False) -> tuple[str, ...]:
    normalized = tuple(values)
    if not normalized and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        _require_non_empty(name, value)
    return normalized


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized.append((key, value))
    return tuple(sorted(normalized))


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "axis"
