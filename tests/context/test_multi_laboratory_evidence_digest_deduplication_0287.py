from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from context.multi_laboratory_evidence_aggregation_contract_0287 import (
    MULTI_LABORATORY_EVIDENCE_AGGREGATE_SCHEMA,
    MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA,
    MultiLaboratoryEvidenceAggregate,
    MultiLaboratoryEvidenceItem,
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
    digest: str | None = None,
    source_ref: str | None = None,
    claim_value: str | None = None,
) -> MultiLaboratoryEvidenceItem:
    return MultiLaboratoryEvidenceItem(
        schema=MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA,
        evidence_ref=f"artifact:evidence-{index}",
        evidence_kind="execution_result",
        subject_ref="requirement:chalouf-drive",
        specialist_ref=f"specialist:technical-{index}",
        capability="technical.review",
        source_ref=source_ref or f"result:visit-{index}",
        provenance_ref=f"provenance:visit-{index}",
        digest_sha256=digest
        or sha256(f"content-{index}".encode()).hexdigest(),
        claim_key="technical.review",
        claim_value=claim_value or f"claim {index}",
        claim_relation="supports",
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
    laboratory_ref: str,
    visit_index: int,
) -> MultiLaboratoryEvidenceProvenance:
    return MultiLaboratoryEvidenceProvenance(
        schema=MULTI_LABORATORY_EVIDENCE_PROVENANCE_SCHEMA,
        provenance_ref=item.provenance_ref,
        evidence_ref=item.evidence_ref,
        laboratory_ref=laboratory_ref,
        visit_ref=f"laboratory-visit:{visit_index}",
        specialist_ref=item.specialist_ref,
        source_ref=item.source_ref,
        visit_status="completed",
        origin_laboratory_ref=laboratory_ref,
        target_laboratory_ref=laboratory_ref,
    )


def _deduplicate(
    items: tuple[MultiLaboratoryEvidenceItem, ...],
):
    provenances = tuple(
        _provenance(
            item,
            "laboratory:local-a"
            if index % 2
            else "laboratory:local-b",
            index,
        )
        for index, item in enumerate(items, start=1)
    )
    return deduplicate_multi_laboratory_evidence(
        _aggregate(items),
        provenances,
    )


def test_unique_content_keeps_every_item_canonical() -> None:
    result = _deduplicate((_item(1), _item(2)))
    assert result.valid is True
    assert result.deduplication_performed is True
    assert result.canonical_evidence_refs == (
        "artifact:evidence-1",
        "artifact:evidence-2",
    )
    assert result.duplicate_evidence_refs == ()
    assert result.original_evidence_count == 2
    assert result.canonical_evidence_count == 2


def test_duplicate_digest_uses_deterministic_canonical_ref() -> None:
    digest = "a" * 64
    result = _deduplicate(
        (
            _item(2, digest=digest, source_ref="result:shared"),
            _item(1, digest=digest, source_ref="result:shared"),
        )
    )
    assert result.canonical_evidence_refs == (
        "artifact:evidence-1",
    )
    assert result.duplicate_evidence_refs == (
        "artifact:evidence-2",
    )
    assert result.evidence_aliases == (
        ("artifact:evidence-2", "artifact:evidence-1"),
    )
    assert result.content_duplicates_found is True


def test_cross_source_and_cross_laboratory_corroboration_are_preserved() -> None:
    digest = "b" * 64
    first = _item(1, digest=digest, source_ref="result:source-a")
    second = _item(2, digest=digest, source_ref="result:source-b")
    result = _deduplicate((first, second))
    group = result.digest_groups[0]
    assert group.source_refs == (
        "result:source-a",
        "result:source-b",
    )
    assert group.laboratory_refs == (
        "laboratory:local-a",
        "laboratory:local-b",
    )
    assert group.provenance_refs == (
        "provenance:visit-1",
        "provenance:visit-2",
    )
    assert group.cross_source_corroborated is True
    assert group.cross_laboratory_corroborated is True
    assert result.cross_source_corroboration_group_count == 1


def test_claim_variants_are_not_erased_before_r5() -> None:
    digest = "c" * 64
    result = _deduplicate(
        (
            _item(1, digest=digest, claim_value="temperature is safe"),
            _item(2, digest=digest, claim_value="temperature needs review"),
        )
    )
    assert result.valid is True
    assert result.claim_variant_evidence_refs == (
        "artifact:evidence-1",
        "artifact:evidence-2",
    )
    assert len(result.digest_groups[0].claim_signatures) == 2
    assert len(result.retained_evidence_items) == 2
    assert result.to_mapping()["contradiction_detection_performed"] is False


def test_order_does_not_change_deduplication_digest() -> None:
    digest = "d" * 64
    first = _item(1, digest=digest)
    second = _item(2, digest=digest)
    p1 = _provenance(first, "laboratory:local-a", 1)
    p2 = _provenance(second, "laboratory:local-b", 2)
    left = deduplicate_multi_laboratory_evidence(
        _aggregate((second, first)),
        (p2, p1),
    )
    right = deduplicate_multi_laboratory_evidence(
        _aggregate((first, second)),
        (p1, p2),
    )
    assert left.to_mapping() == right.to_mapping()
    assert left.deduplication_digest == right.deduplication_digest


def test_invalid_single_laboratory_provenance_blocks_deduplication() -> None:
    first = _item(1)
    second = _item(2)
    result = deduplicate_multi_laboratory_evidence(
        _aggregate((first, second)),
        (
            _provenance(first, "laboratory:local-a", 1),
            _provenance(second, "laboratory:local-a", 2),
        ),
    )
    assert result.valid is False
    assert result.deduplication_performed is False
    assert result.canonical_evidence_refs == ()
    assert any("two distinct" in issue for issue in result.issues)


def test_result_is_immutable() -> None:
    result = _deduplicate((_item(1), _item(2)))
    with pytest.raises(FrozenInstanceError):
        result.valid = False  # type: ignore[misc]


def test_mapping_keeps_later_phase_boundaries_closed() -> None:
    mapping = _deduplicate((_item(1), _item(2))).to_mapping()
    assert mapping["provenance_chain_validated"] is True
    assert mapping["deduplication_performed"] is True
    assert mapping["contradiction_detection_performed"] is False
    assert mapping["weighting_authorized"] is False
    assert mapping["durable_state_written"] is False
    assert mapping["scheduler_selection_allowed"] is False
    assert mapping["sql_remains_durable_authority"] is True
    assert mapping["scheduler_remains_only_orchestrator"] is True
    assert mapping["qdrant_authoritative"] is False
    assert mapping["github_projects_authoritative"] is False
