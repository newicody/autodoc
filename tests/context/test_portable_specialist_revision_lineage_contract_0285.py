from dataclasses import FrozenInstanceError

import pytest

from context.portable_specialist_contract_0284 import (
    PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
    SPECIALIST_CAPABILITY_SCHEMA,
    SPECIALIST_EXECUTION_PROFILE_SCHEMA,
    SPECIALIST_LABORATORY_BINDING_SCHEMA,
    PortableSpecialistDescriptor,
    SpecialistCapabilityContract,
    SpecialistExecutionProfile,
    SpecialistLaboratoryBinding,
)
from context.specialist_capability_growth_proposal_contract_0285 import (
    SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
    SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA,
    SpecialistCapabilityEvidenceRef,
    SpecialistCapabilityGrowthProposal,
)
from context.portable_specialist_revision_lineage_contract_0285 import (
    PORTABLE_SPECIALIST_REVISION_SCHEMA,
    SPECIALIST_REVISION_LINEAGE_SCHEMA,
    PortableSpecialistRevision,
    PortableSpecialistRevisionLineageContractError,
    SpecialistRevisionLineage,
    validate_revision_against_growth_proposal,
)


def _descriptor(version: str, capability: str = "research.synthesis") -> PortableSpecialistDescriptor:
    specialist_ref = "specialist:researcher"
    input_ref = "contract:research.input.v1"
    output_ref = "contract:research.output.v1"
    capability_contract = SpecialistCapabilityContract(
        schema=SPECIALIST_CAPABILITY_SCHEMA,
        capability=capability,
        description=f"Capability {capability}",
        accepted_input_contract_refs=(input_ref,),
        produced_output_contract_refs=(output_ref,),
    )
    profile = SpecialistExecutionProfile(
        schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
        preferred_execution_boundaries=("in_process",),
    )
    binding = SpecialistLaboratoryBinding(
        schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
        specialist_ref=specialist_ref,
        laboratory_ref="laboratory:fake-local",
        visit_modes=("resident", "visitor"),
        required_laboratory_capabilities=("deterministic.execution",),
    )
    return PortableSpecialistDescriptor(
        schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
        specialist_ref=specialist_ref,
        display_name="Research specialist",
        specialist_version=version,
        capabilities=(capability_contract,),
        accepted_input_contract_refs=(input_ref,),
        produced_output_contract_refs=(output_ref,),
        execution_profile=profile,
        laboratory_bindings=(binding,),
    )


def _root() -> PortableSpecialistRevision:
    return PortableSpecialistRevision(
        schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
        revision_ref="revision:researcher:1",
        revision_number=1,
        descriptor=_descriptor("1.0"),
    )


def _child(
    *,
    revision_ref: str = "revision:researcher:2",
    revision_number: int = 2,
    parent_revision_ref: str = "revision:researcher:1",
    version: str = "1.1",
    specialist_ref_change: bool = False,
    proposal_digest: str = "a" * 64,
    evidence_ref: str | None = None,
) -> PortableSpecialistRevision:
    descriptor = _descriptor(version, "research.validation")
    if specialist_ref_change:
        descriptor = PortableSpecialistDescriptor(
            schema=descriptor.schema,
            specialist_ref="specialist:other",
            display_name=descriptor.display_name,
            specialist_version=descriptor.specialist_version,
            capabilities=descriptor.capabilities,
            accepted_input_contract_refs=descriptor.accepted_input_contract_refs,
            produced_output_contract_refs=descriptor.produced_output_contract_refs,
            execution_profile=descriptor.execution_profile,
            laboratory_bindings=(
                SpecialistLaboratoryBinding(
                    schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
                    specialist_ref="specialist:other",
                    laboratory_ref="laboratory:fake-local",
                    visit_modes=("resident",),
                    required_laboratory_capabilities=("deterministic.execution",),
                ),
            ),
        )
    return PortableSpecialistRevision(
        schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
        revision_ref=revision_ref,
        revision_number=revision_number,
        descriptor=descriptor,
        parent_revision_ref=parent_revision_ref,
        source_proposal_ref=f"proposal:researcher:{revision_number}",
        source_proposal_digest_sha256=proposal_digest,
        evidence_refs=(evidence_ref or f"evidence:researcher:{revision_number}",),
    )



def _proposal() -> SpecialistCapabilityGrowthProposal:
    evidence = SpecialistCapabilityEvidenceRef(
        schema=SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
        evidence_ref="evidence:researcher:2",
        evidence_kind="test_report",
        specialist_ref="specialist:researcher",
        capability="research.validation",
        source_ref="test:researcher:2",
        digest_sha256="b" * 64,
        claim="The validation capability passed its controlled tests.",
    )
    return SpecialistCapabilityGrowthProposal(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA,
        proposal_ref="proposal:researcher:2",
        specialist_ref="specialist:researcher",
        base_specialist_version="1.0",
        action="add",
        capability="research.validation",
        proposed_description="Add controlled research validation.",
        evidence_refs=(evidence,),
        proposer_ref="operator:eric",
        conversation_ref="conversation:0285-r3",
        context_refs=("context:0285-r3",),
        requested_input_contract_refs=("contract:research.input.v1",),
        requested_output_contract_refs=("contract:research.output.v1",),
        requested_laboratory_capability_refs=(
            "laboratory-capability:deterministic.execution",
        ),
    )

def _lineage(*revisions: PortableSpecialistRevision) -> SpecialistRevisionLineage:
    return SpecialistRevisionLineage(
        schema=SPECIALIST_REVISION_LINEAGE_SCHEMA,
        lineage_ref="lineage:researcher",
        specialist_ref="specialist:researcher",
        revisions=revisions,
        head_revision_ref=revisions[-1].revision_ref,
    )


def test_root_revision_bootstraps_existing_descriptor_without_authority() -> None:
    revision = _root()
    mapping = revision.to_mapping()

    assert revision.specialist_ref == "specialist:researcher"
    assert mapping["approval_embedded"] is False
    assert mapping["operator_decision_required"] is False
    assert mapping["durable_state_written"] is False
    assert len(mapping["revision_digest"]) == 64


def test_non_root_revision_requires_proposal_digest_and_evidence() -> None:
    with pytest.raises(PortableSpecialistRevisionLineageContractError):
        PortableSpecialistRevision(
            schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
            revision_ref="revision:researcher:2",
            revision_number=2,
            descriptor=_descriptor("1.1", "research.validation"),
            parent_revision_ref="revision:researcher:1",
        )


def test_root_revision_rejects_growth_proposal_fields() -> None:
    with pytest.raises(PortableSpecialistRevisionLineageContractError):
        PortableSpecialistRevision(
            schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
            revision_ref="revision:researcher:1",
            revision_number=1,
            descriptor=_descriptor("1.0"),
            source_proposal_ref="proposal:unexpected",
        )


def test_revision_contract_is_immutable() -> None:
    revision = _root()
    with pytest.raises(FrozenInstanceError):
        revision.revision_number = 9  # type: ignore[misc]


def test_lineage_preserves_stable_identity_and_linear_parent_chain() -> None:
    lineage = _lineage(_root(), _child())

    assert lineage.head_revision.specialist_version == "1.1"
    assert lineage.to_mapping()["append_only"] is True
    assert lineage.to_mapping()["operator_decision_external"] is True


def test_append_returns_new_lineage_without_mutating_previous_value() -> None:
    initial = _lineage(_root())
    extended = initial.append(_child())

    assert len(initial.revisions) == 1
    assert len(extended.revisions) == 2
    assert extended.head_revision_ref == "revision:researcher:2"


def test_append_rejects_non_child_revision() -> None:
    lineage = _lineage(_root())
    with pytest.raises(PortableSpecialistRevisionLineageContractError):
        lineage.append(_child(revision_number=3))


def test_lineage_rejects_identity_change() -> None:
    with pytest.raises(PortableSpecialistRevisionLineageContractError):
        _lineage(_root(), _child(specialist_ref_change=True))


def test_lineage_rejects_gap_or_branch() -> None:
    with pytest.raises(PortableSpecialistRevisionLineageContractError):
        _lineage(
            _root(),
            _child(revision_ref="revision:researcher:3", revision_number=3),
        )

    with pytest.raises(PortableSpecialistRevisionLineageContractError):
        _lineage(
            _root(),
            _child(parent_revision_ref="revision:researcher:unrelated"),
        )


def test_lineage_rejects_reused_version_or_descriptor_snapshot() -> None:
    with pytest.raises(PortableSpecialistRevisionLineageContractError):
        _lineage(_root(), _child(version="1.0"))


def test_head_must_be_latest_revision() -> None:
    root = _root()
    child = _child()
    with pytest.raises(PortableSpecialistRevisionLineageContractError):
        SpecialistRevisionLineage(
            schema=SPECIALIST_REVISION_LINEAGE_SCHEMA,
            lineage_ref="lineage:researcher",
            specialist_ref="specialist:researcher",
            revisions=(root, child),
            head_revision_ref=root.revision_ref,
        )


def test_lineage_digest_is_deterministic_and_metadata_is_normalized() -> None:
    first = SpecialistRevisionLineage(
        schema=SPECIALIST_REVISION_LINEAGE_SCHEMA,
        lineage_ref="lineage:researcher",
        specialist_ref="specialist:researcher",
        revisions=(_root(), _child()),
        head_revision_ref="revision:researcher:2",
        metadata=(("z", "last"), ("a", "first")),
    )
    second = SpecialistRevisionLineage(
        schema=SPECIALIST_REVISION_LINEAGE_SCHEMA,
        lineage_ref="lineage:researcher",
        specialist_ref="specialist:researcher",
        revisions=(_root(), _child()),
        head_revision_ref="revision:researcher:2",
        metadata=(("a", "first"), ("z", "last")),
    )

    assert first.metadata == (("a", "first"), ("z", "last"))
    assert first.lineage_digest == second.lineage_digest


def test_revision_is_correlated_with_r2_proposal_and_parent() -> None:
    proposal = _proposal()
    root = _root()
    child = _child(
        proposal_digest=proposal.proposal_digest,
        evidence_ref=proposal.evidence_refs[0].evidence_ref,
    )

    assert validate_revision_against_growth_proposal(child, proposal, root) == ()


def test_revision_proposal_validation_reports_digest_and_evidence_drift() -> None:
    proposal = _proposal()
    issues = validate_revision_against_growth_proposal(
        _child(proposal_digest="c" * 64, evidence_ref="evidence:other"),
        proposal,
        _root(),
    )

    assert "revision source proposal digest must match proposal_digest" in issues
    assert "revision evidence refs must match proposal evidence refs" in issues
