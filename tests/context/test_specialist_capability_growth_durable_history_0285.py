from dataclasses import FrozenInstanceError, replace

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
from context.specialist_capability_growth_durable_history_0285 import (
    SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_COMMAND_SCHEMA,
    DeterministicSpecialistCapabilityGrowthHistoryAdapter,
    SpecialistCapabilityGrowthDurableHistoryError,
    SpecialistCapabilityGrowthHistoryAppendCommand,
    SpecialistCapabilityGrowthHistoryConflictError,
    SpecialistCapabilityGrowthHistoryPort,
)
from context.specialist_capability_growth_operator_gate_0285 import (
    SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_SCHEMA,
    SpecialistCapabilityGrowthOperatorGate,
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


def _root_lineage() -> SpecialistRevisionLineage:
    root = PortableSpecialistRevision(
        schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
        revision_ref="revision:researcher:1",
        revision_number=1,
        descriptor=_descriptor("1.0", "research.synthesis"),
    )
    return SpecialistRevisionLineage(
        schema=SPECIALIST_REVISION_LINEAGE_SCHEMA,
        lineage_ref="lineage:researcher",
        specialist_ref=root.specialist_ref,
        revisions=(root,),
        head_revision_ref=root.revision_ref,
    )


def _proposal(
    *,
    suffix: str = "2",
    base_version: str = "1.0",
    capability: str = "research.validation",
) -> SpecialistCapabilityGrowthProposal:
    evidence = SpecialistCapabilityEvidenceRef(
        schema=SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
        evidence_ref=f"evidence:researcher:{suffix}",
        evidence_kind="test_report",
        specialist_ref="specialist:researcher",
        capability=capability,
        source_ref=f"test:researcher:{suffix}",
        digest_sha256=suffix[-1] * 64,
        claim=f"The {capability} capability passed controlled tests.",
    )
    return SpecialistCapabilityGrowthProposal(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA,
        proposal_ref=f"proposal:researcher:{suffix}",
        specialist_ref="specialist:researcher",
        base_specialist_version=base_version,
        action="add",
        capability=capability,
        proposed_description=f"Add {capability}.",
        evidence_refs=(evidence,),
        proposer_ref="system:capability-review",
        conversation_ref="conversation:0285-r5",
        context_refs=("context:0285-r5",),
        requested_input_contract_refs=("contract:research.input.v1",),
        requested_output_contract_refs=("contract:research.output.v1",),
        requested_laboratory_capability_refs=(
            "laboratory-capability:deterministic.execution",
        ),
    )


def _candidate(
    proposal: SpecialistCapabilityGrowthProposal,
    *,
    revision_number: int = 2,
    version: str = "1.1",
    parent_revision_ref: str = "revision:researcher:1",
) -> PortableSpecialistRevision:
    return PortableSpecialistRevision(
        schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
        revision_ref=f"revision:researcher:{revision_number}",
        revision_number=revision_number,
        descriptor=_descriptor(version, proposal.capability),
        parent_revision_ref=parent_revision_ref,
        source_proposal_ref=proposal.proposal_ref,
        source_proposal_digest_sha256=proposal.proposal_digest,
        evidence_refs=tuple(item.evidence_ref for item in proposal.evidence_refs),
    )


def _gate() -> SpecialistCapabilityGrowthOperatorGate:
    return SpecialistCapabilityGrowthOperatorGate(
        schema=SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_SCHEMA,
        gate_ref="gate:specialist-capability-growth",
        policy_ref="policy:specialist-capability-growth:v1",
    )


def _command(
    *,
    base_lineage: SpecialistRevisionLineage | None = None,
    proposal: SpecialistCapabilityGrowthProposal | None = None,
    candidate: PortableSpecialistRevision | None = None,
    outcome: str = "approve",
    expected_entry_count: int = 0,
    entry_ref: str = "history-entry:researcher:1",
    sql_ref: str = "sql:specialist-capability-history:researcher:1",
    metadata: tuple[tuple[str, str], ...] = (),
) -> SpecialistCapabilityGrowthHistoryAppendCommand:
    lineage = base_lineage or _root_lineage()
    growth = proposal or _proposal()
    revision = candidate or _candidate(growth)
    decision = _gate().decide(
        growth,
        revision,
        lineage,
        outcome=outcome,  # type: ignore[arg-type]
        decision_ref=f"decision:researcher:{revision.revision_number}:{outcome}",
        operator_ref="operator:eric",
        reason="Explicit operator review.",
    )
    return SpecialistCapabilityGrowthHistoryAppendCommand(
        schema=SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_COMMAND_SCHEMA,
        history_ref="history:specialist-capability-growth:researcher",
        entry_ref=entry_ref,
        sql_ref=sql_ref,
        base_lineage=lineage,
        candidate_revision=revision,
        decision=decision,
        expected_entry_count=expected_entry_count,
        metadata=metadata,
    )


def test_approved_revision_is_appended_without_runtime_side_effects() -> None:
    adapter = DeterministicSpecialistCapabilityGrowthHistoryAdapter()
    result = adapter.append(_command())

    assert result.inserted is True
    assert result.entry.sequence_number == 1
    assert result.snapshot.latest_lineage.head_revision_ref == "revision:researcher:2"
    assert adapter.load(result.entry.history_ref) == result.snapshot
    assert result.durable_write_performed is False
    mapping = result.to_mapping()
    assert mapping["authority_contract"] == "sql"
    assert mapping["qdrant_write_performed"] is False
    assert mapping["scheduler_selection_performed"] is False
    assert mapping["laboratory_execution_performed"] is False


def test_test_adapter_implements_port_without_claiming_durability() -> None:
    adapter = DeterministicSpecialistCapabilityGrowthHistoryAdapter()
    assert isinstance(adapter, SpecialistCapabilityGrowthHistoryPort)
    assert adapter.authority_contract == "sql"
    assert adapter.durable is False


@pytest.mark.parametrize("outcome", ("reject", "defer"))
def test_non_approved_decisions_cannot_enter_history(outcome: str) -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthDurableHistoryError,
        match="operator-approved",
    ):
        _command(outcome=outcome)


def test_decision_and_base_lineage_digests_must_match() -> None:
    command = _command()
    invalid_decision = replace(
        command.decision,
        base_lineage_digest_sha256="f" * 64,
    )
    with pytest.raises(
        SpecialistCapabilityGrowthDurableHistoryError,
        match="base lineage digest",
    ):
        replace(command, decision=invalid_decision)


def test_append_uses_optimistic_entry_count() -> None:
    adapter = DeterministicSpecialistCapabilityGrowthHistoryAdapter()
    first = adapter.append(_command())
    proposal = _proposal(
        suffix="3",
        base_version="1.1",
        capability="research.audit",
    )
    candidate = _candidate(
        proposal,
        revision_number=3,
        version="1.2",
        parent_revision_ref="revision:researcher:2",
    )
    stale = _command(
        base_lineage=first.snapshot.latest_lineage,
        proposal=proposal,
        candidate=candidate,
        expected_entry_count=0,
        entry_ref="history-entry:researcher:2",
        sql_ref="sql:specialist-capability-history:researcher:2",
    )
    with pytest.raises(
        SpecialistCapabilityGrowthHistoryConflictError,
        match="expected_entry_count",
    ):
        adapter.append(stale)


def test_identical_append_is_idempotent() -> None:
    adapter = DeterministicSpecialistCapabilityGrowthHistoryAdapter()
    command = _command()
    first = adapter.append(command)
    second = adapter.append(command)

    assert first.inserted is True
    assert second.inserted is False
    assert second.entry.entry_digest == first.entry.entry_digest
    assert len(second.snapshot.entries) == 1



def test_replay_of_older_entry_after_later_append_remains_idempotent() -> None:
    adapter = DeterministicSpecialistCapabilityGrowthHistoryAdapter()
    first_command = _command()
    first = adapter.append(first_command)
    proposal = _proposal(
        suffix="3",
        base_version="1.1",
        capability="research.audit",
    )
    candidate = _candidate(
        proposal,
        revision_number=3,
        version="1.2",
        parent_revision_ref="revision:researcher:2",
    )
    adapter.append(
        _command(
            base_lineage=first.snapshot.latest_lineage,
            proposal=proposal,
            candidate=candidate,
            expected_entry_count=1,
            entry_ref="history-entry:researcher:2",
            sql_ref="sql:specialist-capability-history:researcher:2",
        )
    )

    replay = adapter.append(first_command)
    assert replay.inserted is False
    assert replay.entry.entry_ref == "history-entry:researcher:1"
    assert len(replay.snapshot.entries) == 2

def test_same_entry_ref_with_different_content_is_rejected() -> None:
    adapter = DeterministicSpecialistCapabilityGrowthHistoryAdapter()
    adapter.append(_command())
    conflict = _command(sql_ref="sql:specialist-capability-history:other")
    with pytest.raises(
        SpecialistCapabilityGrowthHistoryConflictError,
        match="different content",
    ):
        adapter.append(conflict)


def test_second_approved_revision_continues_append_only_chain() -> None:
    adapter = DeterministicSpecialistCapabilityGrowthHistoryAdapter()
    first = adapter.append(_command())
    proposal = _proposal(
        suffix="3",
        base_version="1.1",
        capability="research.audit",
    )
    candidate = _candidate(
        proposal,
        revision_number=3,
        version="1.2",
        parent_revision_ref="revision:researcher:2",
    )
    second_command = _command(
        base_lineage=first.snapshot.latest_lineage,
        proposal=proposal,
        candidate=candidate,
        expected_entry_count=1,
        entry_ref="history-entry:researcher:2",
        sql_ref="sql:specialist-capability-history:researcher:2",
    )
    second = adapter.append(second_command)

    assert second.entry.sequence_number == 2
    assert len(second.snapshot.entries) == 2
    assert second.snapshot.latest_lineage.head_revision_ref == "revision:researcher:3"
    assert (
        second.entry.base_lineage_digest_sha256
        == first.snapshot.latest_lineage.lineage_digest
    )


def test_sql_ref_is_required_for_authoritative_addressing() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthDurableHistoryError,
        match="sql_ref",
    ):
        _command(sql_ref="history:researcher:1")


def test_digests_are_deterministic_under_metadata_ordering() -> None:
    first = _command(metadata=(("z", "last"), ("a", "first")))
    second = _command(metadata=(("a", "first"), ("z", "last")))
    assert first.command_digest == second.command_digest
    assert first.build_entry(sequence_number=1).entry_digest == second.build_entry(
        sequence_number=1
    ).entry_digest


def test_history_contracts_are_immutable() -> None:
    command = _command()
    with pytest.raises(FrozenInstanceError):
        command.expected_entry_count = 2  # type: ignore[misc]

    result = DeterministicSpecialistCapabilityGrowthHistoryAdapter().append(command)
    with pytest.raises(FrozenInstanceError):
        result.entry.sequence_number = 3  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.snapshot.entries = ()  # type: ignore[misc]
