from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from context.multi_laboratory_evidence_aggregation_contract_0287 import (
    MULTI_LABORATORY_EVIDENCE_AGGREGATE_SCHEMA,
    MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA,
    MultiLaboratoryEvidenceAggregate,
    MultiLaboratoryEvidenceAggregationContractError,
    MultiLaboratoryEvidenceItem,
    multi_laboratory_evidence_item_from_specialist_capability_evidence_ref,
)
from context.specialist_capability_growth_proposal_contract_0285 import (
    SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
    SpecialistCapabilityEvidenceRef,
)


def _existing_evidence(index: int) -> SpecialistCapabilityEvidenceRef:
    return SpecialistCapabilityEvidenceRef(
        schema=SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
        evidence_ref=f"evidence:technical:{index}",
        evidence_kind="execution_result",
        specialist_ref=f"specialist:technical-{index}",
        capability="technical.review",
        source_ref=f"result:visit-{index}",
        digest_sha256=sha256(f"content-{index}".encode()).hexdigest(),
        claim=f"technical claim {index}",
        metadata=(("unit", "fixture"),),
    )


def _item(index: int, *, digest: str | None = None) -> MultiLaboratoryEvidenceItem:
    evidence = _existing_evidence(index)
    if digest is not None:
        evidence = SpecialistCapabilityEvidenceRef(
            schema=evidence.schema,
            evidence_ref=evidence.evidence_ref,
            evidence_kind=evidence.evidence_kind,
            specialist_ref=evidence.specialist_ref,
            capability=evidence.capability,
            source_ref=evidence.source_ref,
            digest_sha256=digest,
            claim=evidence.claim,
            metadata=evidence.metadata,
        )
    return multi_laboratory_evidence_item_from_specialist_capability_evidence_ref(
        evidence,
        subject_ref="requirement:chalouf-drive",
        provenance_ref=f"provenance:visit-{index}",
    )


def _aggregate(items: tuple[MultiLaboratoryEvidenceItem, ...]) -> MultiLaboratoryEvidenceAggregate:
    return MultiLaboratoryEvidenceAggregate(
        schema=MULTI_LABORATORY_EVIDENCE_AGGREGATE_SCHEMA,
        aggregation_ref="aggregation:chalouf-drive:1",
        subject_ref="requirement:chalouf-drive",
        conversation_ref="conversation:chalouf-drive",
        context_refs=("context:design", "sql:requirement:chalouf-drive"),
        evidence_items=items,
        aggregation_policy_ref="policy:multi-laboratory-evidence:v1",
        metadata=(("phase", "0287-r2"),),
    )


def test_existing_0285_evidence_is_reused() -> None:
    item = _item(1)
    assert item.schema == MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA
    assert item.claim_key == "technical.review"
    assert item.claim_value == "technical claim 1"
    assert item.provenance_ref == "provenance:visit-1"
    assert len(item.item_digest) == 64


def test_aggregate_order_and_digest_are_deterministic() -> None:
    first = _aggregate((_item(2), _item(1)))
    second = _aggregate((_item(1), _item(2)))
    assert first.evidence_refs == (
        "evidence:technical:1",
        "evidence:technical:2",
    )
    assert first.aggregation_digest == second.aggregation_digest
    assert first.to_mapping() == second.to_mapping()


def test_duplicate_content_digest_is_allowed_for_r4() -> None:
    digest = "a" * 64
    aggregate = _aggregate((_item(1, digest=digest), _item(2, digest=digest)))
    assert aggregate.content_digests == (digest, digest)
    assert aggregate.to_mapping()["deduplication_performed"] is False


def test_duplicate_evidence_ref_is_rejected() -> None:
    item = _item(1)
    with pytest.raises(
        MultiLaboratoryEvidenceAggregationContractError,
        match="unique evidence_ref",
    ):
        _aggregate((item, item))


def test_at_least_two_provenance_refs_are_required() -> None:
    first = _item(1)
    second = MultiLaboratoryEvidenceItem(
        schema=first.schema,
        evidence_ref="evidence:technical:2",
        evidence_kind=first.evidence_kind,
        subject_ref=first.subject_ref,
        specialist_ref="specialist:technical-2",
        capability=first.capability,
        source_ref="result:visit-2",
        provenance_ref=first.provenance_ref,
        digest_sha256="b" * 64,
        claim_key=first.claim_key,
        claim_value="second claim",
        claim_relation="supports",
    )
    with pytest.raises(
        MultiLaboratoryEvidenceAggregationContractError,
        match="two provenance refs",
    ):
        _aggregate((first, second))


def test_subject_drift_is_rejected() -> None:
    item = _item(2)
    drifted = MultiLaboratoryEvidenceItem(
        schema=item.schema,
        evidence_ref=item.evidence_ref,
        evidence_kind=item.evidence_kind,
        subject_ref="requirement:other",
        specialist_ref=item.specialist_ref,
        capability=item.capability,
        source_ref=item.source_ref,
        provenance_ref=item.provenance_ref,
        digest_sha256=item.digest_sha256,
        claim_key=item.claim_key,
        claim_value=item.claim_value,
        claim_relation=item.claim_relation,
    )
    with pytest.raises(
        MultiLaboratoryEvidenceAggregationContractError,
        match="subject_ref",
    ):
        _aggregate((_item(1), drifted))


def test_contracts_are_immutable() -> None:
    aggregate = _aggregate((_item(1), _item(2)))
    with pytest.raises(FrozenInstanceError):
        aggregate.subject_ref = "requirement:changed"  # type: ignore[misc]


def test_mapping_locks_non_authoritative_boundaries() -> None:
    mapping = _aggregate((_item(1), _item(2))).to_mapping()
    assert mapping["authoritative"] is False
    assert mapping["approved"] is False
    assert mapping["provenance_chain_validated"] is False
    assert mapping["deduplication_performed"] is False
    assert mapping["contradiction_detection_performed"] is False
    assert mapping["weighting_authorized"] is False
    assert mapping["durable_state_written"] is False
    assert mapping["scheduler_selection_allowed"] is False
    assert mapping["laboratory_self_authorization_allowed"] is False
    assert mapping["specialist_self_authorization_allowed"] is False
    assert mapping["qdrant_authoritative"] is False
    assert mapping["github_projects_authoritative"] is False
