from dataclasses import FrozenInstanceError

import pytest

from context.specialist_capability_growth_proposal_contract_0285 import (
    SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
    SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA,
    SpecialistCapabilityEvidenceRef,
    SpecialistCapabilityGrowthProposal,
    SpecialistCapabilityGrowthProposalContractError,
)

_DIGEST_A = "a" * 64
_DIGEST_B = "b" * 64


def _evidence(
    *,
    evidence_ref: str = "evidence:capability:planning:1",
    specialist_ref: str = "specialist:planner",
    capability: str = "planning.variant_compare",
    digest: str = _DIGEST_A,
) -> SpecialistCapabilityEvidenceRef:
    return SpecialistCapabilityEvidenceRef(
        schema=SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
        evidence_ref=evidence_ref,
        evidence_kind="test_report",
        specialist_ref=specialist_ref,
        capability=capability,
        source_ref="report:phase-0284-live-path",
        digest_sha256=digest,
        claim="The specialist produced a deterministic comparison artifact.",
        metadata=(("suite", "context"),),
    )


def _proposal(
    *,
    evidence_refs: tuple[SpecialistCapabilityEvidenceRef, ...] | None = None,
    action: str = "add",
    input_refs: tuple[str, ...] = ("contract:variant-request.v1",),
    output_refs: tuple[str, ...] = ("contract:variant-comparison.v1",),
) -> SpecialistCapabilityGrowthProposal:
    return SpecialistCapabilityGrowthProposal(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA,
        proposal_ref="proposal:specialist:planner:variant-compare:1",
        specialist_ref="specialist:planner",
        base_specialist_version="1.2.0",
        action=action,  # type: ignore[arg-type]
        capability="planning.variant_compare",
        proposed_description="Compare bounded design variants.",
        evidence_refs=evidence_refs or (_evidence(),),
        proposer_ref="operator:eric",
        conversation_ref="conversation:chalouf:planning",
        context_refs=("context:chalouf:requirements", "sql:context:42"),
        requested_input_contract_refs=input_refs,
        requested_output_contract_refs=output_refs,
        requested_laboratory_capability_refs=(
            "laboratory-capability:deterministic.execution",
        ),
        metadata=(("priority", "normal"),),
    )


def test_evidence_reference_is_immutable_and_serializable() -> None:
    evidence = _evidence()
    assert evidence.to_mapping()["digest_sha256"] == _DIGEST_A
    with pytest.raises(FrozenInstanceError):
        evidence.claim = "changed"  # type: ignore[misc]


def test_proposal_is_non_authoritative_by_construction() -> None:
    mapping = _proposal().to_mapping()
    assert mapping["authoritative"] is False
    assert mapping["approved"] is False
    assert mapping["scheduler_dispatch_allowed"] is False
    assert mapping["descriptor_mutated"] is False
    assert mapping["durable_state_written"] is False
    assert mapping["specialist_self_authorization_allowed"] is False
    assert mapping["laboratory_self_authorization_allowed"] is False
    assert mapping["copilot_self_authorization_allowed"] is False


def test_proposal_digest_is_deterministic_and_evidence_order_independent() -> None:
    first_evidence = _evidence()
    second_evidence = _evidence(
        evidence_ref="evidence:capability:planning:2", digest=_DIGEST_B
    )
    first = _proposal(evidence_refs=(second_evidence, first_evidence))
    second = _proposal(evidence_refs=(first_evidence, second_evidence))
    assert first.proposal_digest == second.proposal_digest
    assert first.to_mapping() == second.to_mapping()


def test_invalid_sha256_digest_is_rejected() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthProposalContractError, match="SHA-256"
    ):
        _evidence(digest="not-a-digest")


def test_evidence_specialist_must_match_proposal() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthProposalContractError,
        match="evidence specialist_ref",
    ):
        _proposal(evidence_refs=(_evidence(specialist_ref="specialist:other"),))


def test_evidence_capability_must_match_proposal() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthProposalContractError,
        match="evidence capability",
    ):
        _proposal(evidence_refs=(_evidence(capability="planning.other"),))


def test_duplicate_evidence_references_are_rejected() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthProposalContractError, match="unique evidence_ref"
    ):
        _proposal(evidence_refs=(_evidence(), _evidence(digest=_DIGEST_B)))


def test_non_deprecation_proposal_requires_input_and_output_contracts() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthProposalContractError,
        match="requested_input_contract_refs",
    ):
        _proposal(input_refs=())
    with pytest.raises(
        SpecialistCapabilityGrowthProposalContractError,
        match="requested_output_contract_refs",
    ):
        _proposal(output_refs=())


def test_deprecation_proposal_may_omit_contract_refs() -> None:
    proposal = _proposal(action="deprecate", input_refs=(), output_refs=())
    assert proposal.requested_input_contract_refs == ()
    assert proposal.requested_output_contract_refs == ()


def test_metadata_is_normalized_deterministically() -> None:
    evidence = SpecialistCapabilityEvidenceRef(
        schema=SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
        evidence_ref="evidence:capability:planning:1",
        evidence_kind="artifact",
        specialist_ref="specialist:planner",
        capability="planning.variant_compare",
        source_ref="artifact:comparison:1",
        digest_sha256=_DIGEST_A,
        claim="  Stable artifact.  ",
        metadata=((" z ", " 2 "), ("a", "1"), ("z", "3")),
    )
    assert evidence.claim == "Stable artifact."
    assert evidence.metadata == (("a", "1"), ("z", "3"))
