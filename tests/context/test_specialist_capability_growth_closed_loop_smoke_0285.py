import asyncio
from dataclasses import FrozenInstanceError, dataclass, replace

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
    SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_POLICY_SCHEMA,
    SchedulerApprovedSpecialistRevisionSelectionPolicy,
)
from context.specialist_capability_growth_closed_loop_smoke_0285 import (
    SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_COMMAND_SCHEMA,
    SpecialistCapabilityGrowthClosedLoopSmokeCommand,
    SpecialistCapabilityGrowthClosedLoopSmokeError,
    prove_unapproved_specialist_revisions_blocked,
    run_specialist_capability_growth_closed_loop_smoke,
)
from context.specialist_capability_growth_durable_history_0285 import (
    DeterministicSpecialistCapabilityGrowthHistoryAdapter,
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

SPECIALIST_REF = "specialist:technical"
LABORATORY_REF = "laboratory:local-fake"
CAPABILITY = "laboratory.analysis"
INPUT_REF = "contract:missipy.specialist.demand.v1"
OUTPUT_REF = "contract:missipy.laboratory.visit_result.v1"


def _descriptor(version: str, capability: str) -> PortableSpecialistDescriptor:
    return PortableSpecialistDescriptor(
        schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
        specialist_ref=SPECIALIST_REF,
        display_name="Portable technical specialist",
        specialist_version=version,
        capabilities=(
            SpecialistCapabilityContract(
                schema=SPECIALIST_CAPABILITY_SCHEMA,
                capability=capability,
                description=f"Execute {capability} deterministically.",
                accepted_input_contract_refs=(INPUT_REF,),
                produced_output_contract_refs=(OUTPUT_REF,),
            ),
        ),
        accepted_input_contract_refs=(INPUT_REF,),
        produced_output_contract_refs=(OUTPUT_REF,),
        execution_profile=SpecialistExecutionProfile(
            schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
            preferred_execution_boundaries=("in_process",),
            determinism_preference="required",
        ),
        laboratory_bindings=(
            SpecialistLaboratoryBinding(
                schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
                specialist_ref=SPECIALIST_REF,
                laboratory_ref=LABORATORY_REF,
                visit_modes=("resident", "visitor"),
                required_laboratory_capabilities=(
                    "laboratory.visit.execute",
                    "laboratory.specialist.simulate",
                ),
            ),
        ),
        availability="ready",
    )


def _lineage() -> SpecialistRevisionLineage:
    root = PortableSpecialistRevision(
        schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
        revision_ref="revision:technical:1",
        revision_number=1,
        descriptor=_descriptor("1.0.0", "laboratory.synthesis"),
    )
    return SpecialistRevisionLineage(
        schema=SPECIALIST_REVISION_LINEAGE_SCHEMA,
        lineage_ref="lineage:technical",
        specialist_ref=SPECIALIST_REF,
        revisions=(root,),
        head_revision_ref=root.revision_ref,
    )


def _proposal() -> SpecialistCapabilityGrowthProposal:
    evidence = SpecialistCapabilityEvidenceRef(
        schema=SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA,
        evidence_ref="evidence:0285-r8:technical",
        evidence_kind="test_report",
        specialist_ref=SPECIALIST_REF,
        capability=CAPABILITY,
        source_ref="test:0285-r8:technical",
        digest_sha256="8" * 64,
        claim="The portable specialist completed the bounded deterministic analysis.",
    )
    return SpecialistCapabilityGrowthProposal(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA,
        proposal_ref="proposal:0285-r8:technical",
        specialist_ref=SPECIALIST_REF,
        base_specialist_version="1.0.0",
        action="add",
        capability=CAPABILITY,
        proposed_description="Add deterministic laboratory analysis.",
        evidence_refs=(evidence,),
        proposer_ref="system:capability-review",
        conversation_ref="conversation:0285-r8",
        context_refs=("context:0285-r8",),
        requested_input_contract_refs=(INPUT_REF,),
        requested_output_contract_refs=(OUTPUT_REF,),
        requested_laboratory_capability_refs=(
            "laboratory-capability:laboratory.visit.execute",
            "laboratory-capability:laboratory.specialist.simulate",
        ),
    )


def _candidate(proposal: SpecialistCapabilityGrowthProposal) -> PortableSpecialistRevision:
    return PortableSpecialistRevision(
        schema=PORTABLE_SPECIALIST_REVISION_SCHEMA,
        revision_ref="revision:technical:2",
        revision_number=2,
        descriptor=_descriptor("1.1.0", CAPABILITY),
        parent_revision_ref="revision:technical:1",
        source_proposal_ref=proposal.proposal_ref,
        source_proposal_digest_sha256=proposal.proposal_digest,
        evidence_refs=tuple(item.evidence_ref for item in proposal.evidence_refs),
    )


def _command() -> SpecialistCapabilityGrowthClosedLoopSmokeCommand:
    proposal = _proposal()
    return SpecialistCapabilityGrowthClosedLoopSmokeCommand(
        schema=SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_COMMAND_SCHEMA,
        smoke_ref="smoke:0285-r8:technical",
        proposal=proposal,
        candidate_revision=_candidate(proposal),
        base_lineage=_lineage(),
        operator_gate=SpecialistCapabilityGrowthOperatorGate(
            schema=SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_SCHEMA,
            gate_ref="gate:0285-r8",
            policy_ref="policy:0285-r8:operator",
            allowed_operator_refs=("operator:eric",),
        ),
        decision_ref="decision:0285-r8:approve",
        operator_ref="operator:eric",
        decision_reason="Explicit operator approval for the closed-loop smoke.",
        history_ref="history:0285-r8:technical",
        history_entry_ref="history-entry:0285-r8:technical:1",
        history_sql_ref="sql:0285-r8:technical:1",
        expected_history_entry_count=0,
        selection_policy=SchedulerApprovedSpecialistRevisionSelectionPolicy(
            schema=SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_POLICY_SCHEMA,
            policy_ref="policy:0285-r8:scheduler-selection",
            scheduler_ref="scheduler:main",
            allowed_laboratory_refs=(LABORATORY_REF,),
        ),
        selection_command_ref="selection-command:0285-r8:technical",
        selection_ref="selection:0285-r8:technical",
        capability=CAPABILITY,
        input_contract_ref=INPUT_REF,
        output_contract_ref=OUTPUT_REF,
        laboratory_ref=LABORATORY_REF,
        visit_mode="visitor",
        available_laboratory_capabilities=(
            "laboratory.visit.execute",
            "laboratory.specialist.simulate",
        ),
        available_execution_boundaries=("in_process",),
        observation_event_id="event-0285-r8-technical",
        conversation_ref=proposal.conversation_ref,
        context_refs=proposal.context_refs,
    )


class DurableHistoryPort:
    def __init__(self) -> None:
        self.delegate = DeterministicSpecialistCapabilityGrowthHistoryAdapter()
        self.append_calls = 0

    @property
    def authority_contract(self) -> str:
        return "sql"

    @property
    def durable(self) -> bool:
        return True

    def append(self, command):
        self.append_calls += 1
        return replace(
            self.delegate.append(command),
            adapter_kind="dbapi_sql_specialist_capability_history",
            durable_write_performed=True,
        )

    def load(self, history_ref):
        return self.delegate.load(history_ref)


class NonDurableHistoryPort(DurableHistoryPort):
    @property
    def durable(self) -> bool:
        return False


@dataclass(frozen=True)
class LabCommand:
    descriptor: PortableSpecialistDescriptor


@dataclass(frozen=True)
class FakeExistingLaboratoryResult:
    command: LabCommand
    valid: bool = True
    issues: tuple[str, ...] = ()
    visit_ref: str = "visit:0285-r8"
    provider_ref: str = LABORATORY_REF
    visit_status: str = "completed"
    portable_identity_preserved: bool = True
    existing_scheduler_path_verified: bool = True
    fake_specialist_executed: bool = True
    message_contract_closed: bool = True
    durable_closed_loop_preserved: bool = True
    existing_scheduler_used: bool = True
    scheduler_created: bool = False
    scheduler_modified: bool = False
    parallel_orchestrator_created: bool = False
    parallel_queue_created: bool = False
    parallel_eventbus_created: bool = False
    github_mutation_performed: bool = False
    real_specialist_backend_used: bool = False
    transfer_execution_performed: bool = False

    def to_mapping(self):
        return {
            "valid": self.valid,
            "issues": list(self.issues),
            "visit_ref": self.visit_ref,
            "provider_ref": self.provider_ref,
            "visit_status": self.visit_status,
            "portable_identity_preserved": self.portable_identity_preserved,
            "existing_scheduler_path_verified": self.existing_scheduler_path_verified,
            "fake_specialist_executed": self.fake_specialist_executed,
            "message_contract_closed": self.message_contract_closed,
            "durable_closed_loop_preserved": self.durable_closed_loop_preserved,
            "existing_scheduler_used": self.existing_scheduler_used,
            "scheduler_created": self.scheduler_created,
            "scheduler_modified": self.scheduler_modified,
            "parallel_orchestrator_created": self.parallel_orchestrator_created,
            "parallel_queue_created": self.parallel_queue_created,
            "parallel_eventbus_created": self.parallel_eventbus_created,
            "github_mutation_performed": self.github_mutation_performed,
            "real_specialist_backend_used": self.real_specialist_backend_used,
            "transfer_execution_performed": self.transfer_execution_performed,
        }


class RecordingLaboratoryExecutor:
    def __init__(self, **changes) -> None:
        self.calls = []
        self.changes = changes

    async def __call__(self, selection):
        self.calls.append(selection)
        return FakeExistingLaboratoryResult(
            command=LabCommand(selection.selected_revision.descriptor),
            **self.changes,
        )


class RecordingEventBus:
    def __init__(self) -> None:
        self.events: list[Event] = []

    async def publish(self, event: Event) -> None:
        self.events.append(event)


def test_closed_loop_composes_r2_through_r7_and_existing_laboratory_smoke() -> None:
    history = DurableHistoryPort()
    laboratory = RecordingLaboratoryExecutor()
    bus = RecordingEventBus()

    result = asyncio.run(
        run_specialist_capability_growth_closed_loop_smoke(
            _command(),
            history_port=history,
            laboratory_executor=laboratory,
            event_bus=bus,
        )
    )

    assert result.phase_0285_closed is True
    assert result.blocking_proof.valid is True
    assert result.decision.revision_authorized is True
    assert result.history_result.durable_write_performed is True
    assert result.selection.specialist_ref == SPECIALIST_REF
    assert result.laboratory_result.fake_specialist_executed is True
    assert result.observation_publication.published_count == 1
    assert result.passive_read_model.valid is True
    assert history.append_calls == 1
    assert len(laboratory.calls) == 1
    assert len(bus.events) == 1
    assert bus.events[0].type is EventType.SPECIALIST_REVISION_SELECTION_RESULT


def test_reject_and_defer_are_blocked_before_history_port() -> None:
    proof = prove_unapproved_specialist_revisions_blocked(_command())
    assert proof.valid is True
    assert proof.blocked_outcomes == ("reject", "defer")
    assert proof.to_mapping()["history_write_performed"] is False


def test_non_durable_history_port_is_rejected_before_append() -> None:
    history = NonDurableHistoryPort()
    with pytest.raises(
        SpecialistCapabilityGrowthClosedLoopSmokeError,
        match="durable SQL-authoritative",
    ):
        asyncio.run(
            run_specialist_capability_growth_closed_loop_smoke(
                _command(),
                history_port=history,
                laboratory_executor=RecordingLaboratoryExecutor(),
                event_bus=RecordingEventBus(),
            )
        )
    assert history.append_calls == 0


def test_laboratory_execution_must_preserve_existing_scheduler_path() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthClosedLoopSmokeError,
        match="existing_scheduler_path_verified",
    ):
        asyncio.run(
            run_specialist_capability_growth_closed_loop_smoke(
                _command(),
                history_port=DurableHistoryPort(),
                laboratory_executor=RecordingLaboratoryExecutor(
                    existing_scheduler_path_verified=False,
                    valid=False,
                ),
                event_bus=RecordingEventBus(),
            )
        )


def test_laboratory_provider_must_match_scheduler_selection() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthClosedLoopSmokeError,
        match="provider_ref",
    ):
        asyncio.run(
            run_specialist_capability_growth_closed_loop_smoke(
                _command(),
                history_port=DurableHistoryPort(),
                laboratory_executor=RecordingLaboratoryExecutor(
                    provider_ref="laboratory:other"
                ),
                event_bus=RecordingEventBus(),
            )
        )


def test_result_digest_is_deterministic() -> None:
    async def execute_once():
        return await run_specialist_capability_growth_closed_loop_smoke(
            _command(),
            history_port=DurableHistoryPort(),
            laboratory_executor=RecordingLaboratoryExecutor(),
            event_bus=RecordingEventBus(),
        )

    left = asyncio.run(execute_once())
    right = asyncio.run(execute_once())
    assert left.smoke_digest == right.smoke_digest
    assert len(left.smoke_digest) == 64


def test_result_is_immutable() -> None:
    result = asyncio.run(
        run_specialist_capability_growth_closed_loop_smoke(
            _command(),
            history_port=DurableHistoryPort(),
            laboratory_executor=RecordingLaboratoryExecutor(),
            event_bus=RecordingEventBus(),
        )
    )
    with pytest.raises(FrozenInstanceError):
        result.phase_0285_closed = False


def test_command_rejects_context_drift_from_proposal() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthClosedLoopSmokeError,
        match="context_refs must match",
    ):
        replace(_command(), context_refs=("context:other",))


def test_mapping_preserves_authority_boundaries() -> None:
    result = asyncio.run(
        run_specialist_capability_growth_closed_loop_smoke(
            _command(),
            history_port=DurableHistoryPort(),
            laboratory_executor=RecordingLaboratoryExecutor(),
            event_bus=RecordingEventBus(),
        )
    )
    mapping = result.to_mapping()
    assert mapping["phase_0285_closed"] is True
    assert mapping["qdrant_authoritative"] is False
    assert mapping["github_mutation_performed"] is False
    assert mapping["new_scheduler_created"] is False
    assert mapping["parallel_orchestrator_created"] is False
