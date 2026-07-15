from dataclasses import FrozenInstanceError

import pytest

from context.multi_laboratory_evidence_contradiction_detection_0287 import (
    MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DETECTION_SCHEMA,
    MULTI_LABORATORY_EVIDENCE_CONTRADICTION_SCHEMA,
    MultiLaboratoryEvidenceContradiction,
    MultiLaboratoryEvidenceContradictionDetectionResult,
)
from context.multi_laboratory_evidence_operator_weighting_policy_0287 import (
    MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DISPOSITION_SCHEMA,
    MULTI_LABORATORY_EVIDENCE_WEIGHT_SCHEMA,
    MultiLaboratoryEvidenceContradictionDisposition,
    MultiLaboratoryEvidenceOperatorWeightingError,
    MultiLaboratoryEvidenceWeight,
    decide_multi_laboratory_evidence_weighting,
)


def _contradiction(
    *,
    same_canonical: bool = False,
) -> MultiLaboratoryEvidenceContradiction:
    return MultiLaboratoryEvidenceContradiction(
        schema=MULTI_LABORATORY_EVIDENCE_CONTRADICTION_SCHEMA,
        contradiction_ref="contradiction:" + "a" * 64,
        contradiction_kind="relation_opposition",
        claim_key="technical.temperature",
        left_evidence_ref="artifact:evidence-a",
        right_evidence_ref="artifact:evidence-b",
        left_canonical_evidence_ref="artifact:evidence-a",
        right_canonical_evidence_ref=(
            "artifact:evidence-a"
            if same_canonical
            else "artifact:evidence-b"
        ),
        left_claim_value="safe",
        right_claim_value="safe",
        left_claim_relation="supports",
        right_claim_relation="opposes",
        content_digests=("b" * 64, "c" * 64),
        source_refs=("result:visit-a", "result:visit-b"),
        laboratory_refs=("laboratory:a", "laboratory:b"),
        specialist_refs=("specialist:a", "specialist:b"),
    )


def _detection(
    *,
    contradiction: MultiLaboratoryEvidenceContradiction | None = None,
    valid: bool = True,
) -> MultiLaboratoryEvidenceContradictionDetectionResult:
    contradictions = () if contradiction is None else (contradiction,)
    refs = tuple(item.contradiction_ref for item in contradictions)
    return MultiLaboratoryEvidenceContradictionDetectionResult(
        schema=MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DETECTION_SCHEMA,
        valid=valid,
        issues=() if valid else ("invalid detection",),
        aggregation_ref="aggregation:chalouf-drive:1",
        aggregation_digest="d" * 64,
        deduplication_digest="e" * 64,
        policy_ref="policy:contradiction:test",
        policy_digest="f" * 64,
        contradictions=contradictions,
        contradiction_refs=refs,
        unresolved_contradictions=contradictions,
        unresolved_contradiction_refs=refs,
        evidence_refs_with_contradictions=(
            ()
            if contradiction is None
            else (
                contradiction.left_evidence_ref,
                contradiction.right_evidence_ref,
            )
        ),
        unaffected_canonical_evidence_refs=(
            ("artifact:evidence-a", "artifact:evidence-b")
            if contradiction is None
            else ()
        ),
        contradiction_count=len(contradictions),
        unresolved_contradiction_count=len(contradictions),
        contradiction_free=not contradictions,
        contradiction_detection_performed=valid,
        ready_for_operator_weighting=valid,
        detection_digest="1" * 64,
    )


def _weight(
    evidence_ref: str,
    basis_points: int,
) -> MultiLaboratoryEvidenceWeight:
    return MultiLaboratoryEvidenceWeight(
        schema=MULTI_LABORATORY_EVIDENCE_WEIGHT_SCHEMA,
        canonical_evidence_ref=evidence_ref,
        weight_basis_points=basis_points,
        reason="operator assessment",
    )


def _disposition(
    action: str,
) -> MultiLaboratoryEvidenceContradictionDisposition:
    return MultiLaboratoryEvidenceContradictionDisposition(
        schema=(
            MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DISPOSITION_SCHEMA
        ),
        contradiction_ref="contradiction:" + "a" * 64,
        action=action,
        reason="explicit operator treatment",
    )


def test_approve_contradiction_free_weighting() -> None:
    decision = decide_multi_laboratory_evidence_weighting(
        _detection(),
        outcome="approve",
        operator_ref="operator:eric",
        reason="reviewed",
        weights=(
            _weight("artifact:evidence-b", 4_000),
            _weight("artifact:evidence-a", 6_000),
        ),
    )
    assert decision.approved is True
    assert decision.weighting_authorized is True
    assert decision.durable_history_append_allowed is True
    assert tuple(
        item.canonical_evidence_ref for item in decision.weights
    ) == (
        "artifact:evidence-a",
        "artifact:evidence-b",
    )


def test_approve_prefer_left_requires_greater_left_weight() -> None:
    decision = decide_multi_laboratory_evidence_weighting(
        _detection(contradiction=_contradiction()),
        outcome="approve",
        operator_ref="operator:eric",
        reason="left evidence is stronger",
        weights=(
            _weight("artifact:evidence-a", 7_000),
            _weight("artifact:evidence-b", 3_000),
        ),
        contradiction_dispositions=(
            _disposition("prefer_left"),
        ),
    )
    assert decision.operator_reviewed_contradiction_refs == (
        "contradiction:" + "a" * 64,
    )
    assert decision.unresolved_contradiction_refs == (
        "contradiction:" + "a" * 64,
    )
    assert decision.to_mapping()[
        "contradiction_resolution_performed"
    ] is False


def test_same_canonical_conflict_cannot_prefer_one_side() -> None:
    with pytest.raises(
        MultiLaboratoryEvidenceOperatorWeightingError,
        match="same-canonical",
    ):
        decide_multi_laboratory_evidence_weighting(
            _detection(contradiction=_contradiction(same_canonical=True)),
            outcome="approve",
            operator_ref="operator:eric",
            reason="invalid preference",
            weights=(_weight("artifact:evidence-a", 10_000),),
            contradiction_dispositions=(
                _disposition("prefer_left"),
            ),
        )


def test_approve_requires_complete_weight_coverage() -> None:
    with pytest.raises(
        MultiLaboratoryEvidenceOperatorWeightingError,
        match="every canonical",
    ):
        decide_multi_laboratory_evidence_weighting(
            _detection(),
            outcome="approve",
            operator_ref="operator:eric",
            reason="incomplete",
            weights=(_weight("artifact:evidence-a", 10_000),),
        )


def test_reject_does_not_authorize_weighting() -> None:
    decision = decide_multi_laboratory_evidence_weighting(
        _detection(),
        outcome="reject",
        operator_ref="operator:eric",
        reason="insufficient evidence",
    )
    assert decision.rejected is True
    assert decision.weighting_authorized is False
    assert decision.durable_history_append_allowed is False


def test_defer_explicitly_defers_every_contradiction() -> None:
    decision = decide_multi_laboratory_evidence_weighting(
        _detection(contradiction=_contradiction()),
        outcome="defer",
        operator_ref="operator:eric",
        reason="additional measurement required",
        contradiction_dispositions=(_disposition("defer"),),
    )
    assert decision.deferred is True
    assert decision.weighting_authorized is False
    assert decision.unresolved_contradiction_refs == (
        "contradiction:" + "a" * 64,
    )


def test_weighting_digest_is_order_independent() -> None:
    left = decide_multi_laboratory_evidence_weighting(
        _detection(),
        outcome="approve",
        operator_ref="operator:eric",
        reason="reviewed",
        weights=(
            _weight("artifact:evidence-a", 6_000),
            _weight("artifact:evidence-b", 4_000),
        ),
    )
    right = decide_multi_laboratory_evidence_weighting(
        _detection(),
        outcome="approve",
        operator_ref="operator:eric",
        reason="reviewed",
        weights=(
            _weight("artifact:evidence-b", 4_000),
            _weight("artifact:evidence-a", 6_000),
        ),
    )
    assert left.to_mapping() == right.to_mapping()
    assert left.weighting_digest == right.weighting_digest


def test_invalid_detection_is_rejected() -> None:
    with pytest.raises(
        MultiLaboratoryEvidenceOperatorWeightingError,
        match="valid r5 detection",
    ):
        decide_multi_laboratory_evidence_weighting(
            _detection(valid=False),
            outcome="reject",
            operator_ref="operator:eric",
            reason="invalid input",
        )


def test_decision_is_immutable_and_keeps_boundaries_closed() -> None:
    decision = decide_multi_laboratory_evidence_weighting(
        _detection(),
        outcome="approve",
        operator_ref="operator:eric",
        reason="reviewed",
        weights=(
            _weight("artifact:evidence-a", 5_000),
            _weight("artifact:evidence-b", 5_000),
        ),
    )
    mapping = decision.to_mapping()
    assert mapping["durable_state_written"] is False
    assert mapping["scheduler_selection_allowed"] is False
    assert mapping["eventbus_observation_published"] is False
    assert mapping["qdrant_projection_written"] is False
    assert mapping["github_mutation_performed"] is False
    assert mapping["scheduler_remains_only_orchestrator"] is True
    assert mapping["sql_remains_durable_authority"] is True
    with pytest.raises(FrozenInstanceError):
        decision.outcome = "reject"  # type: ignore[misc]
