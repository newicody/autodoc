import asyncio
from dataclasses import FrozenInstanceError, replace

import pytest

from contracts.event import Event, EventType
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
from context.scheduler_approved_specialist_revision_selection_0285 import (
    SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_COMMAND_SCHEMA,
    SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_POLICY_SCHEMA,
    SchedulerApprovedSpecialistRevisionSelectionCommand,
    SchedulerApprovedSpecialistRevisionSelectionError,
    SchedulerApprovedSpecialistRevisionSelectionHandler,
    SchedulerApprovedSpecialistRevisionSelectionPolicy,
    SchedulerApprovedSpecialistRevisionSelector,
    build_scheduler_approved_specialist_revision_selection_event,
    register_scheduler_approved_specialist_revision_selection,
)
from context.specialist_capability_growth_durable_history_0285 import (
    SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_COMMAND_SCHEMA,
    DeterministicSpecialistCapabilityGrowthHistoryAdapter,
    SpecialistCapabilityGrowthHistoryAppendCommand,
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


SPECIALIST_REF = "specialist:researcher"
LABORATORY_REF = "laboratory:fake-local"
INPUT_REF = "contract:research.input.v1"
OUTPUT_REF = "contract:research.output.v1"
CAPABILITY = "research.validation"


def _descriptor(
    version: str,
    capability: str,
    *,
    availability: str = "ready",
    boundaries: tuple[str, ...] = ("in_process", "local_process"),
    visit_modes: tuple[str, ...] = ("resident", "visitor"),
    laboratory_ref: str = LABORATORY_REF,
    required_laboratory_capabilities: tuple[str, ...] = (
        "deterministic.execution",
    ),
) -> PortableSpecialistDescriptor:
    return PortableSpecialistDescriptor(
        schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
        specialist_ref=SPECIALIST_REF,
        display_name="Research specialist",
        specialist_version=version,
        capabilities=(
            SpecialistCapabilityContract(
                schema=SPECIALIST_CAPABILITY_SCHEMA,
                capability=capability,
                description=f"Capability {capability}",
                accepted_input_contract_refs=(INPUT_REF,),
                produced_output_contract_refs=(OUTPUT_REF,),
            ),
        ),
        accepted_input_contract_refs=(INPUT_REF,),
        produced_output_contract_refs=(OUTPUT_REF,),
        execution_profile=SpecialistExecutionProfile(
            schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
            preferred_execution_boundaries=boundaries,  # type: ignore[arg-type]
        ),
        laboratory_bindings=(
            SpecialistLaboratoryBinding(
                schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
                specialist_ref=SPECIALIST_REF,
                laboratory_ref=laboratory_ref,
                visit_modes=visit_modes,  # type: ignore[arg-type]
                required_laboratory_capabilities=(
                    required_laboratory_capabilities
                ),
            ),
        ),
        availability=availability,  # type: ignore[arg-type]
    )


def _root_lineage() -> SpecialistRevisionLineage:
    root = PortableSpecialistRevision(
        schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
        revision_ref="revision:researcher:1",
        revision_number=1,
        descriptor=_descriptor("1.0", "research.synthesis", availability="ready"),
    )
    return SpecialistRevisionLineage(
        schema=SPECIALIST_REVISION_LINEAGE_SCHEMA,
        lineage_ref="lineage:researcher",
        specialist_ref=SPECIALIST_REF,
        revisions=(root,),
        head_revision_ref=root.revision_ref,
    )


def _proposal(
    *,
    suffix: str = "2",
    base_version: str = "1.0",
    capability: str = CAPABILITY,
) -> SpecialistCapabilityGrowthProposal:
    evidence = SpecialistCapabilityEvidenceRef(
        schema=SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
        evidence_ref=f"evidence:researcher:{suffix}",
        evidence_kind="test_report",
        specialist_ref=SPECIALIST_REF,
        capability=capability,
        source_ref=f"test:researcher:{suffix}",
        digest_sha256=suffix[-1] * 64,
        claim=f"The {capability} capability passed controlled tests.",
    )
    return SpecialistCapabilityGrowthProposal(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA,
        proposal_ref=f"proposal:researcher:{suffix}",
        specialist_ref=SPECIALIST_REF,
        base_specialist_version=base_version,
        action="add",
        capability=capability,
        proposed_description=f"Add {capability}.",
        evidence_refs=(evidence,),
        proposer_ref="system:capability-review",
        conversation_ref="conversation:0285-r6",
        context_refs=("context:0285-r6",),
        requested_input_contract_refs=(INPUT_REF,),
        requested_output_contract_refs=(OUTPUT_REF,),
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
    descriptor: PortableSpecialistDescriptor | None = None,
) -> PortableSpecialistRevision:
    return PortableSpecialistRevision(
        schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
        revision_ref=f"revision:researcher:{revision_number}",
        revision_number=revision_number,
        descriptor=descriptor or _descriptor(version, proposal.capability),
        parent_revision_ref=parent_revision_ref,
        source_proposal_ref=proposal.proposal_ref,
        source_proposal_digest_sha256=proposal.proposal_digest,
        evidence_refs=tuple(item.evidence_ref for item in proposal.evidence_refs),
    )


def _history_command(
    *,
    lineage: SpecialistRevisionLineage | None = None,
    proposal: SpecialistCapabilityGrowthProposal | None = None,
    candidate: PortableSpecialistRevision | None = None,
    expected_entry_count: int = 0,
    entry_number: int = 1,
) -> SpecialistCapabilityGrowthHistoryAppendCommand:
    base = lineage or _root_lineage()
    growth = proposal or _proposal()
    revision = candidate or _candidate(growth)
    gate = SpecialistCapabilityGrowthOperatorGate(
        schema=SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_SCHEMA,
        gate_ref="gate:specialist-capability-growth",
        policy_ref="policy:specialist-capability-growth:v1",
    )
    decision = gate.decide(
        growth,
        revision,
        base,
        outcome="approve",
        decision_ref=f"decision:researcher:{revision.revision_number}:approve",
        operator_ref="operator:eric",
        reason="Explicit operator review.",
    )
    return SpecialistCapabilityGrowthHistoryAppendCommand(
        schema=SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_COMMAND_SCHEMA,
        history_ref="history:specialist-capability-growth:researcher",
        entry_ref=f"history-entry:researcher:{entry_number}",
        sql_ref=f"sql:specialist-capability-history:researcher:{entry_number}",
        base_lineage=base,
        candidate_revision=revision,
        decision=decision,
        expected_entry_count=expected_entry_count,
    )


def _durable_result(
    *,
    descriptor: PortableSpecialistDescriptor | None = None,
):
    proposal = _proposal()
    candidate = _candidate(proposal, descriptor=descriptor)
    result = DeterministicSpecialistCapabilityGrowthHistoryAdapter().append(
        _history_command(proposal=proposal, candidate=candidate)
    )
    return replace(
        result,
        adapter_kind="dbapi_sql_specialist_capability_history",
        durable_write_performed=True,
    )


def _policy(**changes) -> SchedulerApprovedSpecialistRevisionSelectionPolicy:
    values = {
        "schema": SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_POLICY_SCHEMA,
        "policy_ref": "policy:scheduler-specialist-revision-selection:v1",
        "scheduler_ref": "scheduler:main",
        "allowed_laboratory_refs": (LABORATORY_REF,),
    }
    values.update(changes)
    return SchedulerApprovedSpecialistRevisionSelectionPolicy(**values)


def _command(*, history_result=None, **changes):
    durable = history_result or _durable_result()
    values = {
        "schema": SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_COMMAND_SCHEMA,
        "command_ref": "selection-command:researcher:1",
        "selection_ref": "selection:researcher:1",
        "scheduler_ref": "scheduler:main",
        "history_result": durable,
        "expected_snapshot_digest_sha256": durable.snapshot.snapshot_digest,
        "specialist_ref": SPECIALIST_REF,
        "capability": CAPABILITY,
        "input_contract_ref": INPUT_REF,
        "output_contract_ref": OUTPUT_REF,
        "laboratory_ref": LABORATORY_REF,
        "visit_mode": "visitor",
        "available_laboratory_capabilities": ("deterministic.execution",),
        "available_execution_boundaries": ("local_process", "in_process"),
        "conversation_ref": "conversation:0285-r6",
        "context_refs": ("context:0285-r6", durable.entry.sql_ref),
    }
    values.update(changes)
    return SchedulerApprovedSpecialistRevisionSelectionCommand(**values)


def test_selects_latest_durable_operator_approved_revision() -> None:
    command = _command()
    result = SchedulerApprovedSpecialistRevisionSelector().select(command, _policy())

    assert result.selected_revision.revision_ref == "revision:researcher:2"
    assert result.sql_ref == command.history_result.entry.sql_ref
    assert result.decision_ref == command.history_result.entry.decision.decision_ref
    assert result.execution_boundary == "in_process"
    mapping = result.to_mapping()
    assert mapping["scheduler_selection_performed"] is True
    assert mapping["scheduler_dispatch_performed"] is False
    assert mapping["laboratory_execution_performed"] is False
    assert mapping["sql_write_performed"] is False
    assert mapping["qdrant_write_performed"] is False
    assert mapping["new_scheduler_created"] is False


def test_event_builder_targets_existing_scheduler_event_path() -> None:
    command = _command()
    event = build_scheduler_approved_specialist_revision_selection_event(
        command,
        source="operator-gate",
        priority=42,
        correlation_id="correlation:0285-r6",
    )
    assert event.type is EventType.SPECIALIST_REVISION_SELECTION
    assert event.dest == "scheduler"
    assert event.payload is command
    assert event.source == "operator-gate"
    assert event.priority == 42
    assert event.metadata["phase"] == "0285-r6"


def test_handler_is_dispatcher_compatible() -> None:
    command = _command()
    handler = SchedulerApprovedSpecialistRevisionSelectionHandler(_policy())
    event = build_scheduler_approved_specialist_revision_selection_event(command)
    result = asyncio.run(handler.handle(event))
    assert result.selection_ref == command.selection_ref


class _FakeDispatcher:
    def __init__(self) -> None:
        self.registration = None

    def register(self, event_type, handler) -> None:
        self.registration = (event_type, handler)


def test_registration_uses_existing_dispatcher_without_new_registry() -> None:
    dispatcher = _FakeDispatcher()
    handler = SchedulerApprovedSpecialistRevisionSelectionHandler(_policy())
    register_scheduler_approved_specialist_revision_selection(dispatcher, handler)
    assert dispatcher.registration == (
        EventType.SPECIALIST_REVISION_SELECTION,
        handler,
    )


def test_non_durable_history_result_is_rejected() -> None:
    non_durable = replace(
        DeterministicSpecialistCapabilityGrowthHistoryAdapter().append(
            _history_command()
        ),
        adapter_kind="dbapi_sql_specialist_capability_history",
    )
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="durable SQL-authoritative",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(
            _command(history_result=non_durable),
            _policy(),
        )



def test_test_only_history_adapter_cannot_claim_selection_authority() -> None:
    forged = replace(
        DeterministicSpecialistCapabilityGrowthHistoryAdapter().append(
            _history_command()
        ),
        durable_write_performed=True,
    )
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="test-only history adapter",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(
            _command(history_result=forged),
            _policy(),
        )

def test_snapshot_digest_must_match_command() -> None:
    command = _command(expected_snapshot_digest_sha256="f" * 64)
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="snapshot digest",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(command, _policy())


def test_only_latest_durable_history_entry_can_be_selected() -> None:
    adapter = DeterministicSpecialistCapabilityGrowthHistoryAdapter()
    first = adapter.append(_history_command())
    proposal = _proposal(suffix="3", base_version="1.1", capability="research.audit")
    candidate = _candidate(
        proposal,
        revision_number=3,
        version="1.2",
        parent_revision_ref="revision:researcher:2",
    )
    second = adapter.append(
        _history_command(
            lineage=first.snapshot.latest_lineage,
            proposal=proposal,
            candidate=candidate,
            expected_entry_count=1,
            entry_number=2,
        )
    )
    stale = replace(
        first,
        snapshot=second.snapshot,
        inserted=False,
        adapter_kind="dbapi_sql_specialist_capability_history",
        durable_write_performed=True,
    )
    command = _command(
        history_result=stale,
        expected_snapshot_digest_sha256=second.snapshot.snapshot_digest,
    )
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="latest durable history entry",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(command, _policy())


def test_specialist_identity_must_match_history() -> None:
    command = _command(specialist_ref="specialist:other")
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="specialist_ref",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(command, _policy())


def test_descriptor_must_be_ready() -> None:
    descriptor = _descriptor("1.1", CAPABILITY, availability="declared")
    command = _command(history_result=_durable_result(descriptor=descriptor))
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="must be ready",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(command, _policy())


def test_requested_capability_must_exist() -> None:
    command = _command(capability="research.unknown")
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="requested capability",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(command, _policy())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("input_contract_ref", "contract:other.input.v1", "input contract"),
        ("output_contract_ref", "contract:other.output.v1", "output contract"),
    ),
)
def test_contract_envelope_must_match_capability(field, value, message) -> None:
    command = _command(**{field: value})
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match=message,
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(command, _policy())


def test_target_laboratory_must_be_declared() -> None:
    command = _command(laboratory_ref="laboratory:other")
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="not declared",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(
            command,
            _policy(allowed_laboratory_refs=()),
        )


def test_scheduler_policy_must_allow_target_laboratory() -> None:
    command = _command()
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="not allowed by Scheduler",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(
            command,
            _policy(allowed_laboratory_refs=("laboratory:other",)),
        )


def test_visit_mode_must_match_policy_and_binding() -> None:
    command = _command(visit_mode="transfer")
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="selection policy",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(command, _policy())


def test_target_laboratory_must_supply_required_capabilities() -> None:
    command = _command(
        available_laboratory_capabilities=("artifact.exchange",),
    )
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="required capabilities",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(command, _policy())


def test_execution_boundary_is_selected_in_specialist_preference_order() -> None:
    descriptor = _descriptor(
        "1.1",
        CAPABILITY,
        boundaries=("local_process", "in_process"),
    )
    command = _command(history_result=_durable_result(descriptor=descriptor))
    result = SchedulerApprovedSpecialistRevisionSelector().select(command, _policy())
    assert result.execution_boundary == "local_process"


def test_missing_compatible_execution_boundary_is_rejected() -> None:
    command = _command(available_execution_boundaries=("local_process",))
    policy = _policy(allowed_execution_boundaries=("in_process",))
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="no compatible execution boundary",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(command, policy)


def test_scheduler_refs_must_match() -> None:
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="scheduler_ref",
    ):
        SchedulerApprovedSpecialistRevisionSelector().select(
            _command(),
            _policy(scheduler_ref="scheduler:other"),
        )


def test_handler_rejects_wrong_event_and_payload() -> None:
    handler = SchedulerApprovedSpecialistRevisionSelectionHandler(_policy())
    wrong_type = Event(EventType.TICK, source="test", payload=_command())
    with pytest.raises(
        SchedulerApprovedSpecialistRevisionSelectionError,
        match="only accepts",
    ):
        asyncio.run(handler.handle(wrong_type))

    wrong_payload = Event(
        EventType.SPECIALIST_REVISION_SELECTION,
        source="test",
        payload={"not": "a command"},
    )
    with pytest.raises(TypeError, match="event payload"):
        asyncio.run(handler.handle(wrong_payload))


def test_contracts_are_immutable_and_digests_are_deterministic() -> None:
    first = _command(metadata=(("z", "last"), ("a", "first")))
    second = _command(metadata=(("a", "first"), ("z", "last")))
    assert first.command_digest == second.command_digest
    with pytest.raises(FrozenInstanceError):
        first.scheduler_ref = "scheduler:other"  # type: ignore[misc]

    policy_first = _policy(metadata=(("z", "last"), ("a", "first")))
    policy_second = _policy(metadata=(("a", "first"), ("z", "last")))
    assert policy_first.policy_digest == policy_second.policy_digest
