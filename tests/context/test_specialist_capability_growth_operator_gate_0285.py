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
from context.portable_specialist_revision_lineage_contract_0285 import (
    PORTABLE_SPECIALIST_REVISION_SCHEMA,
    SPECIALIST_REVISION_LINEAGE_SCHEMA,
    PortableSpecialistRevision,
    SpecialistRevisionLineage,
)
from context.specialist_capability_growth_operator_gate_0285 import (
    SPECIALIST_CAPABILITY_GROWTH_DECISION_SCHEMA,
    SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_SCHEMA,
    SpecialistCapabilityGrowthDecision,
    SpecialistCapabilityGrowthOperatorGate,
    SpecialistCapabilityGrowthOperatorGateError,
)
from context.specialist_capability_growth_proposal_contract_0285 import (
    SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
    SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA,
    SpecialistCapabilityEvidenceRef,
    SpecialistCapabilityGrowthProposal,
)


def _descriptor(version: str, capability: str) -> PortableSpecialistDescriptor:
    specialist_ref = "specialist:researcher"
    input_ref = "contract:research.input.v1"
    output_ref = "contract:research.output.v1"
    return PortableSpecialistDescriptor(
        schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
        specialist_ref=specialist_ref,
        display_name="Research specialist",
        specialist_version=version,
        capabilities=(
            SpecialistCapabilityContract(
                schema=SPECIALIST_CAPABILITY_SCHEMA,
                capability=capability,
                description=f"Capability {capability}",
                accepted_input_contract_refs=(input_ref,),
                produced_output_contract_refs=(output_ref,),
            ),
        ),
        accepted_input_contract_refs=(input_ref,),
        produced_output_contract_refs=(output_ref,),
        execution_profile=SpecialistExecutionProfile(
            schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
            preferred_execution_boundaries=("in_process",),
        ),
        laboratory_bindings=(
            SpecialistLaboratoryBinding(
                schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
                specialist_ref=specialist_ref,
                laboratory_ref="laboratory:fake-local",
                visit_modes=("resident", "visitor"),
                required_laboratory_capabilities=("deterministic.execution",),
            ),
        ),
    )


def _root() -> PortableSpecialistRevision:
    return PortableSpecialistRevision(
        schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
        revision_ref="revision:researcher:1",
        revision_number=1,
        descriptor=_descriptor("1.0", "research.synthesis"),
    )


def _lineage() -> SpecialistRevisionLineage:
    root = _root()
    return SpecialistRevisionLineage(
        schema=SPECIALIST_REVISION_LINEAGE_SCHEMA,
        lineage_ref="lineage:researcher",
        specialist_ref=root.specialist_ref,
        revisions=(root,),
        head_revision_ref=root.revision_ref,
    )


def _evidence(
    *,
    evidence_ref: str = "evidence:researcher:2",
    evidence_kind: str = "test_report",
    source_ref: str = "test:researcher:2",
) -> SpecialistCapabilityEvidenceRef:
    return SpecialistCapabilityEvidenceRef(
        schema=SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
        evidence_ref=evidence_ref,
        evidence_kind=evidence_kind,  # type: ignore[arg-type]
        specialist_ref="specialist:researcher",
        capability="research.validation",
        source_ref=source_ref,
        digest_sha256="b" * 64,
        claim="The validation capability passed its controlled tests.",
    )


def _proposal(
    *,
    evidence_refs: tuple[SpecialistCapabilityEvidenceRef, ...] | None = None,
    proposer_ref: str = "system:capability-review",
    action: str = "add",
) -> SpecialistCapabilityGrowthProposal:
    return SpecialistCapabilityGrowthProposal(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA,
        proposal_ref="proposal:researcher:2",
        specialist_ref="specialist:researcher",
        base_specialist_version="1.0",
        action=action,  # type: ignore[arg-type]
        capability="research.validation",
        proposed_description="Add controlled research validation.",
        evidence_refs=evidence_refs or (_evidence(),),
        proposer_ref=proposer_ref,
        conversation_ref="conversation:0285-r4",
        context_refs=("context:0285-r4",),
        requested_input_contract_refs=("contract:research.input.v1",),
        requested_output_contract_refs=("contract:research.output.v1",),
        requested_laboratory_capability_refs=(
            "laboratory-capability:deterministic.execution",
        ),
    )


def _candidate(proposal: SpecialistCapabilityGrowthProposal) -> PortableSpecialistRevision:
    return PortableSpecialistRevision(
        schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
        revision_ref="revision:researcher:2",
        revision_number=2,
        descriptor=_descriptor("1.1", "research.validation"),
        parent_revision_ref="revision:researcher:1",
        source_proposal_ref=proposal.proposal_ref,
        source_proposal_digest_sha256=proposal.proposal_digest,
        evidence_refs=tuple(item.evidence_ref for item in proposal.evidence_refs),
    )


def _gate(**overrides: object) -> SpecialistCapabilityGrowthOperatorGate:
    values: dict[str, object] = {
        "schema": SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_SCHEMA,
        "gate_ref": "gate:specialist-capability-growth",
        "policy_ref": "policy:specialist-capability-growth:v1",
    }
    values.update(overrides)
    return SpecialistCapabilityGrowthOperatorGate(**values)  # type: ignore[arg-type]


def test_explicit_operator_approval_authorizes_revision_without_dispatch() -> None:
    proposal = _proposal()
    decision = _gate().decide(
        proposal,
        _candidate(proposal),
        _lineage(),
        outcome="approve",
        decision_ref="decision:researcher:2:approve",
        operator_ref="operator:eric",
        reason="Evidence and candidate revision are coherent.",
    )

    assert decision.approved is True
    assert decision.revision_authorized is True
    assert decision.terminal is True
    assert decision.policy_issues == ()
    assert decision.to_mapping()["scheduler_selection_allowed"] is False
    assert decision.to_mapping()["durable_state_written"] is False
    assert len(decision.decision_digest) == 64


@pytest.mark.parametrize(
    ("outcome", "terminal"),
    (("reject", True), ("defer", False)),
)
def test_reject_and_defer_never_authorize_revision(
    outcome: str, terminal: bool
) -> None:
    proposal = _proposal()
    decision = _gate().decide(
        proposal,
        _candidate(proposal),
        _lineage(),
        outcome=outcome,  # type: ignore[arg-type]
        decision_ref=f"decision:researcher:2:{outcome}",
        operator_ref="operator:eric",
        reason="Explicit operator decision.",
    )

    assert decision.revision_authorized is False
    assert decision.terminal is terminal


def test_approval_fails_when_policy_requires_more_evidence() -> None:
    proposal = _proposal()
    gate = _gate(minimum_evidence_count=2)

    with pytest.raises(
        SpecialistCapabilityGrowthOperatorGateError,
        match="minimum evidence count",
    ):
        gate.decide(
            proposal,
            _candidate(proposal),
            _lineage(),
            outcome="approve",
            decision_ref="decision:researcher:2:approve",
            operator_ref="operator:eric",
            reason="Attempted approval.",
        )


def test_reject_records_policy_issues_for_a_non_approvable_candidate() -> None:
    proposal = _proposal()
    decision = _gate(required_evidence_kinds=("benchmark",)).decide(
        proposal,
        _candidate(proposal),
        _lineage(),
        outcome="reject",
        decision_ref="decision:researcher:2:reject",
        operator_ref="operator:eric",
        reason="Required benchmark evidence is missing.",
    )

    assert decision.rejected is True
    assert decision.revision_authorized is False
    assert "proposal is missing required evidence kinds: benchmark" in decision.policy_issues


def test_gate_accepts_only_explicit_operator_identity() -> None:
    proposal = _proposal()
    with pytest.raises(SpecialistCapabilityGrowthOperatorGateError):
        _gate().decide(
            proposal,
            _candidate(proposal),
            _lineage(),
            outcome="approve",
            decision_ref="decision:researcher:2:approve",
            operator_ref="copilot:advisor",
            reason="Copilot cannot approve.",
        )


def test_operator_allowlist_and_separation_of_duties_are_policy_checks() -> None:
    proposal = _proposal(proposer_ref="operator:eric")
    candidate = _candidate(proposal)
    gate = _gate(
        allowed_operator_refs=("operator:alice",),
        require_distinct_operator_from_proposer=True,
    )

    issues = gate.evaluate(
        proposal,
        candidate,
        _lineage(),
        operator_ref="operator:eric",
    )
    assert "operator_ref is not allowed by the gate policy" in issues
    assert "operator must be distinct from proposal proposer" in issues


def test_candidate_must_extend_current_lineage_head() -> None:
    proposal = _proposal()
    candidate = PortableSpecialistRevision(
        schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
        revision_ref="revision:researcher:3",
        revision_number=3,
        descriptor=_descriptor("1.2", "research.validation"),
        parent_revision_ref="revision:researcher:2",
        source_proposal_ref=proposal.proposal_ref,
        source_proposal_digest_sha256=proposal.proposal_digest,
        evidence_refs=(proposal.evidence_refs[0].evidence_ref,),
    )

    issues = _gate().evaluate(
        proposal,
        candidate,
        _lineage(),
        operator_ref="operator:eric",
    )
    assert "candidate revision must extend the current lineage head" in issues
    assert "candidate revision number must follow the current lineage" in issues


def test_distinct_evidence_source_policy_is_enforced() -> None:
    first = _evidence(evidence_ref="evidence:researcher:a")
    second = _evidence(
        evidence_ref="evidence:researcher:b",
        evidence_kind="benchmark",
        source_ref=first.source_ref,
    )
    proposal = _proposal(evidence_refs=(first, second))

    issues = _gate(require_distinct_evidence_sources=True).evaluate(
        proposal,
        _candidate(proposal),
        _lineage(),
        operator_ref="operator:eric",
    )
    assert "proposal evidence sources must be distinct" in issues


def test_gate_policy_can_disable_restore() -> None:
    proposal = _proposal(action="restore")
    issues = _gate(allow_restore=False).evaluate(
        proposal,
        _candidate(proposal),
        _lineage(),
        operator_ref="operator:eric",
    )
    assert "restore proposals are disabled by the gate policy" in issues


def test_policy_and_decision_digests_are_deterministic() -> None:
    first_gate = _gate(metadata=(("z", "last"), ("a", "first")))
    second_gate = _gate(metadata=(("a", "first"), ("z", "last")))
    assert first_gate.policy_digest == second_gate.policy_digest

    proposal = _proposal()
    first = first_gate.decide(
        proposal,
        _candidate(proposal),
        _lineage(),
        outcome="defer",
        decision_ref="decision:researcher:2:defer",
        operator_ref="operator:eric",
        reason="Awaiting a second review.",
        metadata=(("z", "last"), ("a", "first")),
    )
    second = second_gate.decide(
        proposal,
        _candidate(proposal),
        _lineage(),
        outcome="defer",
        decision_ref="decision:researcher:2:defer",
        operator_ref="operator:eric",
        reason="Awaiting a second review.",
        metadata=(("a", "first"), ("z", "last")),
    )
    assert first.decision_digest == second.decision_digest


def test_decision_rejects_approval_with_embedded_policy_issues() -> None:
    with pytest.raises(SpecialistCapabilityGrowthOperatorGateError):
        SpecialistCapabilityGrowthDecision(
            schema=SPECIALIST_CAPABILITY_GROWTH_DECISION_SCHEMA,
            decision_ref="decision:researcher:2:approve",
            outcome="approve",
            operator_ref="operator:eric",
            policy_ref="policy:specialist-capability-growth:v1",
            policy_digest_sha256="a" * 64,
            proposal_ref="proposal:researcher:2",
            proposal_digest_sha256="b" * 64,
            candidate_revision_ref="revision:researcher:2",
            candidate_revision_digest_sha256="c" * 64,
            base_lineage_ref="lineage:researcher",
            base_lineage_digest_sha256="d" * 64,
            specialist_ref="specialist:researcher",
            reason="Invalid approval.",
            conversation_ref="conversation:0285-r4",
            context_refs=("context:0285-r4",),
            policy_issues=("missing evidence",),
        )


def test_gate_and_decision_are_immutable() -> None:
    gate = _gate()
    with pytest.raises(FrozenInstanceError):
        gate.minimum_evidence_count = 9  # type: ignore[misc]

    proposal = _proposal()
    decision = gate.decide(
        proposal,
        _candidate(proposal),
        _lineage(),
        outcome="approve",
        decision_ref="decision:researcher:2:approve",
        operator_ref="operator:eric",
        reason="Approved.",
    )
    with pytest.raises(FrozenInstanceError):
        decision.outcome = "reject"  # type: ignore[misc]
