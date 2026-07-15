from hashlib import sha256

from context.multi_laboratory_evidence_aggregation_contract_0287 import (
    MULTI_LABORATORY_EVIDENCE_AGGREGATE_SCHEMA,
    MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA,
    MultiLaboratoryEvidenceAggregate,
    MultiLaboratoryEvidenceItem,
)
from context.multi_laboratory_evidence_contradiction_detection_0287 import (
    MULTI_LABORATORY_EVIDENCE_CONTRADICTION_POLICY_SCHEMA,
    MultiLaboratoryEvidenceContradictionPolicy,
    detect_multi_laboratory_evidence_contradictions,
)
from context.multi_laboratory_evidence_digest_deduplication_0287 import (
    deduplicate_multi_laboratory_evidence,
)
from context.multi_laboratory_evidence_provenance_contract_0287 import (
    MULTI_LABORATORY_EVIDENCE_PROVENANCE_SCHEMA,
    MultiLaboratoryEvidenceProvenance,
)


def _item(
    index: int,
    *,
    claim_key: str = "technical.temperature",
    claim_value: str = "safe",
    relation: str = "supports",
    digest: str | None = None,
) -> MultiLaboratoryEvidenceItem:
    return MultiLaboratoryEvidenceItem(
        schema=MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA,
        evidence_ref=f"artifact:evidence-{index}",
        evidence_kind="execution_result",
        subject_ref="requirement:chalouf-drive",
        specialist_ref=f"specialist:technical-{index}",
        capability="technical.review",
        source_ref=f"result:visit-{index}",
        provenance_ref=f"provenance:visit-{index}",
        digest_sha256=digest
        or sha256(f"content-{index}".encode()).hexdigest(),
        claim_key=claim_key,
        claim_value=claim_value,
        claim_relation=relation,
    )


def _aggregate(
    items: tuple[MultiLaboratoryEvidenceItem, ...],
) -> MultiLaboratoryEvidenceAggregate:
    return MultiLaboratoryEvidenceAggregate(
        schema=MULTI_LABORATORY_EVIDENCE_AGGREGATE_SCHEMA,
        aggregation_ref="aggregation:chalouf-drive:1",
        subject_ref="requirement:chalouf-drive",
        conversation_ref="conversation:chalouf-drive",
        context_refs=("context:design",),
        evidence_items=items,
        aggregation_policy_ref="policy:multi-laboratory-evidence:v1",
    )


def _provenance(
    item: MultiLaboratoryEvidenceItem,
    index: int,
) -> MultiLaboratoryEvidenceProvenance:
    laboratory = (
        "laboratory:local-a"
        if index % 2
        else "laboratory:local-b"
    )
    return MultiLaboratoryEvidenceProvenance(
        schema=MULTI_LABORATORY_EVIDENCE_PROVENANCE_SCHEMA,
        provenance_ref=item.provenance_ref,
        evidence_ref=item.evidence_ref,
        laboratory_ref=laboratory,
        visit_ref=f"laboratory-visit:{index}",
        specialist_ref=item.specialist_ref,
        source_ref=item.source_ref,
        visit_status="completed",
        origin_laboratory_ref=laboratory,
        target_laboratory_ref=laboratory,
    )


def _dedup(
    items: tuple[MultiLaboratoryEvidenceItem, ...],
):
    return deduplicate_multi_laboratory_evidence(
        _aggregate(items),
        tuple(
            _provenance(
                item,
                int(item.evidence_ref.rsplit("-", 1)[1]),
            )
            for item in items
        ),
    )


def _policy(
    *,
    exclusive_claim_keys: tuple[str, ...] = (),
    exclusive_value_pairs: tuple[tuple[str, str, str], ...] = (),
) -> MultiLaboratoryEvidenceContradictionPolicy:
    return MultiLaboratoryEvidenceContradictionPolicy(
        schema=(
            MULTI_LABORATORY_EVIDENCE_CONTRADICTION_POLICY_SCHEMA
        ),
        policy_ref="policy:contradiction:test",
        exclusive_claim_keys=exclusive_claim_keys,
        exclusive_value_pairs=exclusive_value_pairs,
    )


def test_support_and_oppose_same_value_is_direct_contradiction() -> None:
    result = detect_multi_laboratory_evidence_contradictions(
        _dedup(
            (
                _item(1, claim_value="safe", relation="supports"),
                _item(2, claim_value="safe", relation="opposes"),
            )
        )
    )
    assert result.valid is True
    assert result.contradiction_count == 1
    assert result.contradictions[0].contradiction_kind == (
        "relation_opposition"
    )
    assert result.unresolved_contradictions == result.contradictions


def test_same_content_interpretation_variant_is_preserved() -> None:
    digest = "a" * 64
    result = detect_multi_laboratory_evidence_contradictions(
        _dedup(
            (
                _item(1, claim_value="safe", digest=digest),
                _item(
                    2,
                    claim_value="needs review",
                    digest=digest,
                ),
            )
        )
    )
    contradiction = result.contradictions[0]
    assert contradiction.contradiction_kind == (
        "same_content_claim_variant"
    )
    assert contradiction.left_canonical_evidence_ref == (
        contradiction.right_canonical_evidence_ref
    )
    assert result.unresolved_contradiction_count == 1


def test_single_value_policy_detects_different_positive_values() -> None:
    result = detect_multi_laboratory_evidence_contradictions(
        _dedup(
            (
                _item(1, claim_value="safe"),
                _item(2, claim_value="unsafe"),
            )
        ),
        _policy(
            exclusive_claim_keys=("technical.temperature",),
        ),
    )
    assert result.contradictions[0].contradiction_kind == (
        "exclusive_value_conflict"
    )


def test_explicit_value_pair_detects_only_declared_pair() -> None:
    result = detect_multi_laboratory_evidence_contradictions(
        _dedup(
            (
                _item(1, claim_value="manual"),
                _item(2, claim_value="automatic"),
            )
        ),
        _policy(
            exclusive_value_pairs=(
                (
                    "technical.temperature",
                    "automatic",
                    "manual",
                ),
            ),
        ),
    )
    assert result.contradiction_count == 1

    unrelated = detect_multi_laboratory_evidence_contradictions(
        _dedup(
            (
                _item(1, claim_value="manual"),
                _item(2, claim_value="assisted"),
            )
        ),
        _policy(
            exclusive_value_pairs=(
                (
                    "technical.temperature",
                    "automatic",
                    "manual",
                ),
            ),
        ),
    )
    assert unrelated.contradiction_free is True


def test_different_claim_keys_are_not_guessed_as_contradictory() -> None:
    result = detect_multi_laboratory_evidence_contradictions(
        _dedup(
            (
                _item(
                    1,
                    claim_key="technical.temperature",
                    claim_value="safe",
                ),
                _item(
                    2,
                    claim_key="technical.pressure",
                    claim_value="unsafe",
                ),
            )
        ),
        _policy(
            exclusive_claim_keys=("technical.temperature",),
        ),
    )
    assert result.contradiction_free is True
    assert result.ready_for_operator_weighting is True


def test_result_is_deterministic_for_reordered_input() -> None:
    left = _item(1, claim_value="safe", relation="supports")
    right = _item(2, claim_value="safe", relation="opposes")
    first = detect_multi_laboratory_evidence_contradictions(
        _dedup((left, right))
    )
    second = detect_multi_laboratory_evidence_contradictions(
        _dedup((right, left))
    )
    assert first.to_mapping() == second.to_mapping()
    assert first.detection_digest == second.detection_digest


def test_invalid_deduplication_blocks_detection() -> None:
    first = _item(1)
    second = _item(2)
    invalid = deduplicate_multi_laboratory_evidence(
        _aggregate((first, second)),
        (
            MultiLaboratoryEvidenceProvenance(
                schema=MULTI_LABORATORY_EVIDENCE_PROVENANCE_SCHEMA,
                provenance_ref=first.provenance_ref,
                evidence_ref=first.evidence_ref,
                laboratory_ref="laboratory:one",
                visit_ref="laboratory-visit:1",
                specialist_ref=first.specialist_ref,
                source_ref=first.source_ref,
                visit_status="completed",
                origin_laboratory_ref="laboratory:one",
                target_laboratory_ref="laboratory:one",
            ),
            MultiLaboratoryEvidenceProvenance(
                schema=MULTI_LABORATORY_EVIDENCE_PROVENANCE_SCHEMA,
                provenance_ref=second.provenance_ref,
                evidence_ref=second.evidence_ref,
                laboratory_ref="laboratory:one",
                visit_ref="laboratory-visit:2",
                specialist_ref=second.specialist_ref,
                source_ref=second.source_ref,
                visit_status="completed",
                origin_laboratory_ref="laboratory:one",
                target_laboratory_ref="laboratory:one",
            ),
        ),
    )
    result = detect_multi_laboratory_evidence_contradictions(invalid)
    assert result.valid is False
    assert result.contradiction_detection_performed is False
    assert result.ready_for_operator_weighting is False


def test_mapping_locks_later_authority_boundaries() -> None:
    mapping = detect_multi_laboratory_evidence_contradictions(
        _dedup((_item(1), _item(2, claim_key="technical.pressure")))
    ).to_mapping()
    assert mapping["contradiction_detection_performed"] is True
    assert mapping["weighting_authorized"] is False
    assert mapping["durable_state_written"] is False
    assert mapping["scheduler_selection_allowed"] is False
    assert mapping["laboratory_self_authorization_allowed"] is False
    assert mapping["specialist_self_authorization_allowed"] is False
    assert mapping["sql_remains_durable_authority"] is True
    assert mapping["scheduler_remains_only_orchestrator"] is True
    assert mapping["qdrant_authoritative"] is False
    assert mapping["github_projects_authoritative"] is False
