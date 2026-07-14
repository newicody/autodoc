"""Closed-loop specialist capability-growth smoke for phase 0285-r8.

The smoke composes the contracts introduced by 0285-r2 through r7 and reuses the
existing portable-specialist laboratory smoke from 0284-r5.  It does not create a
Scheduler, Dispatcher, EventBus, laboratory provider, durable store or parallel
orchestrator.  Runtime dependencies are injected through the existing ports.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Any, Protocol, runtime_checkable

from contracts.event import EventType
from context.portable_specialist_revision_lineage_contract_0285 import (
    PortableSpecialistRevision,
    SpecialistRevisionLineage,
)
from context.scheduler_approved_specialist_revision_selection_0285 import (
    SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_COMMAND_SCHEMA,
    SchedulerApprovedSpecialistRevisionSelectionCommand,
    SchedulerApprovedSpecialistRevisionSelectionHandler,
    SchedulerApprovedSpecialistRevisionSelectionPolicy,
    SchedulerApprovedSpecialistRevisionSelectionResult,
    build_scheduler_approved_specialist_revision_selection_event,
)
from context.specialist_capability_growth_durable_history_0285 import (
    SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_COMMAND_SCHEMA,
    SpecialistCapabilityGrowthDurableHistoryError,
    SpecialistCapabilityGrowthHistoryAppendCommand,
    SpecialistCapabilityGrowthHistoryAppendResult,
    SpecialistCapabilityGrowthHistoryPort,
)
from context.specialist_capability_growth_observation_projection_0285 import (
    SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PUBLICATION_SCHEMA,
    SpecialistCapabilityGrowthObservationEventBusPort,
    SpecialistCapabilityGrowthObservationPublicationReport,
    SpecialistCapabilityGrowthPassiveReadModel,
    build_specialist_capability_growth_observation_event,
    build_specialist_capability_growth_observation_projection,
    build_specialist_capability_growth_passive_read_model,
)
from context.specialist_capability_growth_operator_gate_0285 import (
    SpecialistCapabilityGrowthDecision,
    SpecialistCapabilityGrowthOperatorGate,
)
from context.specialist_capability_growth_proposal_contract_0285 import (
    SpecialistCapabilityGrowthProposal,
)

SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_COMMAND_SCHEMA = (
    "missipy.specialist.capability_growth_closed_loop_smoke_command.v1"
)
SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_RESULT_SCHEMA = (
    "missipy.specialist.capability_growth_closed_loop_smoke_result.v1"
)
SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_VERSION = "0285.r8"

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SMOKE_PREFIXES = ("smoke:",)
_DECISION_PREFIXES = ("decision:",)
_HISTORY_PREFIXES = ("history:",)
_HISTORY_ENTRY_PREFIXES = ("history-entry:",)
_SQL_PREFIXES = ("sql:",)
_SELECTION_COMMAND_PREFIXES = ("selection-command:",)
_SELECTION_PREFIXES = ("selection:",)
_EVENT_PREFIXES = ("event-", "event:")


class SpecialistCapabilityGrowthClosedLoopSmokeError(RuntimeError):
    """Raised when the r8 smoke would bypass one of the existing authorities."""


@runtime_checkable
class ExistingPortableSpecialistLaboratorySmokeResultPort(Protocol):
    """Structural view of the existing 0284-r5 laboratory smoke result."""

    valid: bool
    issues: tuple[str, ...]
    command: object
    visit_ref: str
    provider_ref: str
    visit_status: str
    portable_identity_preserved: bool
    existing_scheduler_path_verified: bool
    fake_specialist_executed: bool
    message_contract_closed: bool
    durable_closed_loop_preserved: bool
    existing_scheduler_used: bool
    scheduler_created: bool
    scheduler_modified: bool
    parallel_orchestrator_created: bool
    parallel_queue_created: bool
    parallel_eventbus_created: bool
    github_mutation_performed: bool
    real_specialist_backend_used: bool
    transfer_execution_performed: bool

    def to_mapping(self) -> Mapping[str, object]:
        """Return the immutable smoke evidence as a serializable mapping."""


ExistingPortableSpecialistLaboratoryExecutor = Callable[
    [SchedulerApprovedSpecialistRevisionSelectionResult],
    Awaitable[ExistingPortableSpecialistLaboratorySmokeResultPort],
]


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthClosedLoopSmokeCommand:
    """All immutable inputs needed to compose the existing r2-r7 contracts."""

    schema: str
    smoke_ref: str
    proposal: SpecialistCapabilityGrowthProposal
    candidate_revision: PortableSpecialistRevision
    base_lineage: SpecialistRevisionLineage
    operator_gate: SpecialistCapabilityGrowthOperatorGate
    decision_ref: str
    operator_ref: str
    decision_reason: str
    history_ref: str
    history_entry_ref: str
    history_sql_ref: str
    expected_history_entry_count: int
    selection_policy: SchedulerApprovedSpecialistRevisionSelectionPolicy
    selection_command_ref: str
    selection_ref: str
    capability: str
    input_contract_ref: str
    output_contract_ref: str
    laboratory_ref: str
    visit_mode: str
    available_laboratory_capabilities: tuple[str, ...]
    available_execution_boundaries: tuple[str, ...]
    observation_event_id: str
    conversation_ref: str
    context_refs: tuple[str, ...]
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_COMMAND_SCHEMA:
            raise SpecialistCapabilityGrowthClosedLoopSmokeError(
                "unsupported specialist capability growth closed-loop smoke schema"
            )
        _require_ref("smoke_ref", self.smoke_ref, _SMOKE_PREFIXES)
        if not isinstance(self.proposal, SpecialistCapabilityGrowthProposal):
            raise TypeError("proposal must be SpecialistCapabilityGrowthProposal")
        if not isinstance(self.candidate_revision, PortableSpecialistRevision):
            raise TypeError("candidate_revision must be PortableSpecialistRevision")
        if not isinstance(self.base_lineage, SpecialistRevisionLineage):
            raise TypeError("base_lineage must be SpecialistRevisionLineage")
        if not isinstance(self.operator_gate, SpecialistCapabilityGrowthOperatorGate):
            raise TypeError("operator_gate must be SpecialistCapabilityGrowthOperatorGate")
        if not isinstance(
            self.selection_policy,
            SchedulerApprovedSpecialistRevisionSelectionPolicy,
        ):
            raise TypeError(
                "selection_policy must be SchedulerApprovedSpecialistRevisionSelectionPolicy"
            )
        _require_ref("decision_ref", self.decision_ref, _DECISION_PREFIXES)
        _require_ref("history_ref", self.history_ref, _HISTORY_PREFIXES)
        _require_ref(
            "history_entry_ref", self.history_entry_ref, _HISTORY_ENTRY_PREFIXES
        )
        _require_ref("history_sql_ref", self.history_sql_ref, _SQL_PREFIXES)
        if (
            isinstance(self.expected_history_entry_count, bool)
            or not isinstance(self.expected_history_entry_count, int)
            or self.expected_history_entry_count < 0
        ):
            raise SpecialistCapabilityGrowthClosedLoopSmokeError(
                "expected_history_entry_count must be a non-negative integer"
            )
        _require_ref(
            "selection_command_ref",
            self.selection_command_ref,
            _SELECTION_COMMAND_PREFIXES,
        )
        _require_ref("selection_ref", self.selection_ref, _SELECTION_PREFIXES)
        if not isinstance(self.observation_event_id, str) or not self.observation_event_id.startswith(
            _EVENT_PREFIXES
        ):
            raise SpecialistCapabilityGrowthClosedLoopSmokeError(
                "observation_event_id must be an event reference"
            )
        if self.proposal.specialist_ref != self.candidate_revision.specialist_ref:
            raise SpecialistCapabilityGrowthClosedLoopSmokeError(
                "proposal and candidate revision must preserve specialist_ref"
            )
        if self.base_lineage.specialist_ref != self.proposal.specialist_ref:
            raise SpecialistCapabilityGrowthClosedLoopSmokeError(
                "base lineage must preserve proposal specialist_ref"
            )
        if self.candidate_revision.parent_revision_ref != self.base_lineage.head_revision_ref:
            raise SpecialistCapabilityGrowthClosedLoopSmokeError(
                "candidate revision must extend the base lineage head"
            )
        if self.conversation_ref != self.proposal.conversation_ref:
            raise SpecialistCapabilityGrowthClosedLoopSmokeError(
                "conversation_ref must match proposal conversation_ref"
            )
        if tuple(self.context_refs) != self.proposal.context_refs:
            raise SpecialistCapabilityGrowthClosedLoopSmokeError(
                "context_refs must match proposal context_refs"
            )
        object.__setattr__(self, "available_laboratory_capabilities", _strings(
            "available_laboratory_capabilities", self.available_laboratory_capabilities
        ))
        object.__setattr__(self, "available_execution_boundaries", _strings(
            "available_execution_boundaries", self.available_execution_boundaries
        ))
        object.__setattr__(self, "context_refs", _strings("context_refs", self.context_refs))
        object.__setattr__(self, "metadata", _metadata(self.metadata))
        _non_empty("operator_ref", self.operator_ref)
        _non_empty("decision_reason", self.decision_reason)
        _non_empty("capability", self.capability)
        _non_empty("input_contract_ref", self.input_contract_ref)
        _non_empty("output_contract_ref", self.output_contract_ref)
        _non_empty("laboratory_ref", self.laboratory_ref)
        _non_empty("visit_mode", self.visit_mode)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "smoke_ref": self.smoke_ref,
            "proposal": self.proposal.to_mapping(),
            "candidate_revision": self.candidate_revision.to_mapping(),
            "base_lineage": self.base_lineage.to_mapping(),
            "operator_gate": self.operator_gate.to_mapping(),
            "decision_ref": self.decision_ref,
            "operator_ref": self.operator_ref,
            "decision_reason": self.decision_reason,
            "history_ref": self.history_ref,
            "history_entry_ref": self.history_entry_ref,
            "history_sql_ref": self.history_sql_ref,
            "expected_history_entry_count": self.expected_history_entry_count,
            "selection_policy": self.selection_policy.to_mapping(),
            "selection_command_ref": self.selection_command_ref,
            "selection_ref": self.selection_ref,
            "capability": self.capability,
            "input_contract_ref": self.input_contract_ref,
            "output_contract_ref": self.output_contract_ref,
            "laboratory_ref": self.laboratory_ref,
            "visit_mode": self.visit_mode,
            "available_laboratory_capabilities": list(
                self.available_laboratory_capabilities
            ),
            "available_execution_boundaries": list(
                self.available_execution_boundaries
            ),
            "observation_event_id": self.observation_event_id,
            "conversation_ref": self.conversation_ref,
            "context_refs": list(self.context_refs),
            "metadata": dict(self.metadata),
            "existing_scheduler_required": True,
            "existing_laboratory_smoke_required": True,
            "new_scheduler_created": False,
            "parallel_orchestrator_created": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthUnapprovedBlockingProof:
    """Pure proof that reject/defer decisions cannot reach durable history."""

    rejected_revision_blocked: bool
    deferred_revision_blocked: bool
    blocked_outcomes: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return (
            self.rejected_revision_blocked
            and self.deferred_revision_blocked
            and self.blocked_outcomes == ("reject", "defer")
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "rejected_revision_blocked": self.rejected_revision_blocked,
            "deferred_revision_blocked": self.deferred_revision_blocked,
            "blocked_outcomes": list(self.blocked_outcomes),
            "valid": self.valid,
            "history_write_performed": False,
            "scheduler_selection_performed": False,
            "laboratory_execution_performed": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthClosedLoopSmokeResult:
    """Correlated evidence that the approved capability-growth loop closed once."""

    schema: str
    command: SpecialistCapabilityGrowthClosedLoopSmokeCommand
    blocking_proof: SpecialistCapabilityGrowthUnapprovedBlockingProof
    decision: SpecialistCapabilityGrowthDecision
    history_result: SpecialistCapabilityGrowthHistoryAppendResult
    selection: SchedulerApprovedSpecialistRevisionSelectionResult
    laboratory_result: ExistingPortableSpecialistLaboratorySmokeResultPort
    observation_publication: SpecialistCapabilityGrowthObservationPublicationReport
    passive_read_model: SpecialistCapabilityGrowthPassiveReadModel
    phase_0285_closed: bool
    issues: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_RESULT_SCHEMA:
            raise SpecialistCapabilityGrowthClosedLoopSmokeError(
                "unsupported specialist capability growth closed-loop result schema"
            )
        if not isinstance(self.command, SpecialistCapabilityGrowthClosedLoopSmokeCommand):
            raise TypeError("command must be a closed-loop smoke command")
        if not isinstance(self.blocking_proof, SpecialistCapabilityGrowthUnapprovedBlockingProof):
            raise TypeError("blocking_proof must be an unapproved blocking proof")
        if not isinstance(self.decision, SpecialistCapabilityGrowthDecision):
            raise TypeError("decision must be SpecialistCapabilityGrowthDecision")
        if not isinstance(self.history_result, SpecialistCapabilityGrowthHistoryAppendResult):
            raise TypeError("history_result must be a history append result")
        if not isinstance(
            self.selection, SchedulerApprovedSpecialistRevisionSelectionResult
        ):
            raise TypeError("selection must be a Scheduler selection result")
        if not isinstance(
            self.laboratory_result,
            ExistingPortableSpecialistLaboratorySmokeResultPort,
        ):
            raise TypeError("laboratory_result must implement the existing smoke result port")
        if not isinstance(
            self.observation_publication,
            SpecialistCapabilityGrowthObservationPublicationReport,
        ):
            raise TypeError("observation_publication must be a publication report")
        if not isinstance(self.passive_read_model, SpecialistCapabilityGrowthPassiveReadModel):
            raise TypeError("passive_read_model must be the r7 passive read model")
        object.__setattr__(self, "issues", tuple(dict.fromkeys(self.issues)))
        if self.phase_0285_closed and (self.issues or not self._required_invariants()):
            raise SpecialistCapabilityGrowthClosedLoopSmokeError(
                "phase_0285_closed requires the complete approved and observed loop"
            )

    def _required_invariants(self) -> bool:
        return all(
            (
                self.blocking_proof.valid,
                self.decision.revision_authorized,
                self.history_result.durable_write_performed,
                self.selection.selection_ref == self.command.selection_ref,
                self.laboratory_result.valid,
                self.laboratory_result.existing_scheduler_used,
                self.laboratory_result.fake_specialist_executed,
                self.laboratory_result.durable_closed_loop_preserved,
                self.observation_publication.published_count == 1,
                self.passive_read_model.valid,
            )
        )

    @property
    def smoke_digest(self) -> str:
        return _digest(self.to_mapping(include_digest=False))

    def to_mapping(self, *, include_digest: bool = True) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "command": self.command.to_mapping(),
            "blocking_proof": self.blocking_proof.to_mapping(),
            "decision": self.decision.to_mapping(),
            "history_result": self.history_result.to_mapping(),
            "selection": self.selection.to_mapping(),
            "laboratory_result": dict(self.laboratory_result.to_mapping()),
            "observation_publication": self.observation_publication.to_mapping(),
            "passive_read_model": self.passive_read_model.to_mapping(),
            "phase_0285_closed": self.phase_0285_closed,
            "issues": list(self.issues),
            "operator_gate_closed": self.decision.revision_authorized,
            "durable_sql_history_recorded": self.history_result.durable_write_performed,
            "scheduler_selection_performed": True,
            "laboratory_execution_performed": self.laboratory_result.valid,
            "eventbus_observation_published": (
                self.observation_publication.published_count == 1
            ),
            "passive_supervisor_read_model_valid": self.passive_read_model.valid,
            "qdrant_authoritative": False,
            "github_mutation_performed": False,
            "new_scheduler_created": False,
            "parallel_orchestrator_created": False,
        }
        if include_digest:
            mapping["smoke_digest"] = self.smoke_digest
        return mapping


def prove_unapproved_specialist_revisions_blocked(
    command: SpecialistCapabilityGrowthClosedLoopSmokeCommand,
) -> SpecialistCapabilityGrowthUnapprovedBlockingProof:
    """Prove reject/defer decisions are rejected before any history-port call."""

    blocked: list[str] = []
    for outcome in ("reject", "defer"):
        decision = command.operator_gate.decide(
            command.proposal,
            command.candidate_revision,
            command.base_lineage,
            outcome=outcome,
            decision_ref=f"decision:0285-r8:{_suffix(command.smoke_ref)}:{outcome}",
            operator_ref=command.operator_ref,
            reason=f"r8 proof for {outcome} outcome",
        )
        try:
            SpecialistCapabilityGrowthHistoryAppendCommand(
                schema=SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_COMMAND_SCHEMA,
                history_ref=command.history_ref,
                entry_ref=(
                    f"history-entry:0285-r8:{_suffix(command.smoke_ref)}:{outcome}"
                ),
                sql_ref=f"sql:0285-r8:{_suffix(command.smoke_ref)}:{outcome}",
                base_lineage=command.base_lineage,
                candidate_revision=command.candidate_revision,
                decision=decision,
                expected_entry_count=command.expected_history_entry_count,
            )
        except SpecialistCapabilityGrowthDurableHistoryError:
            blocked.append(outcome)
    outcomes = tuple(blocked)
    return SpecialistCapabilityGrowthUnapprovedBlockingProof(
        rejected_revision_blocked="reject" in outcomes,
        deferred_revision_blocked="defer" in outcomes,
        blocked_outcomes=outcomes,
    )


async def run_specialist_capability_growth_closed_loop_smoke(
    command: SpecialistCapabilityGrowthClosedLoopSmokeCommand,
    *,
    history_port: SpecialistCapabilityGrowthHistoryPort,
    laboratory_executor: ExistingPortableSpecialistLaboratoryExecutor,
    event_bus: SpecialistCapabilityGrowthObservationEventBusPort,
) -> SpecialistCapabilityGrowthClosedLoopSmokeResult:
    """Execute one approved growth cycle through the existing authorities."""

    if not isinstance(command, SpecialistCapabilityGrowthClosedLoopSmokeCommand):
        raise TypeError("command must be SpecialistCapabilityGrowthClosedLoopSmokeCommand")
    if not isinstance(history_port, SpecialistCapabilityGrowthHistoryPort):
        raise TypeError("history_port must implement SpecialistCapabilityGrowthHistoryPort")
    if history_port.authority_contract != "sql" or history_port.durable is not True:
        raise SpecialistCapabilityGrowthClosedLoopSmokeError(
            "r8 requires a durable SQL-authoritative history port"
        )
    if not callable(laboratory_executor):
        raise TypeError("laboratory_executor must be callable")
    if not isinstance(event_bus, SpecialistCapabilityGrowthObservationEventBusPort):
        raise TypeError("event_bus must implement the existing observation port")

    blocking_proof = prove_unapproved_specialist_revisions_blocked(command)
    if not blocking_proof.valid:
        raise SpecialistCapabilityGrowthClosedLoopSmokeError(
            "reject and defer outcomes must be blocked before persistence"
        )

    decision = command.operator_gate.decide(
        command.proposal,
        command.candidate_revision,
        command.base_lineage,
        outcome="approve",
        decision_ref=command.decision_ref,
        operator_ref=command.operator_ref,
        reason=command.decision_reason,
        metadata=command.metadata,
    )
    append_command = SpecialistCapabilityGrowthHistoryAppendCommand(
        schema=SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_COMMAND_SCHEMA,
        history_ref=command.history_ref,
        entry_ref=command.history_entry_ref,
        sql_ref=command.history_sql_ref,
        base_lineage=command.base_lineage,
        candidate_revision=command.candidate_revision,
        decision=decision,
        expected_entry_count=command.expected_history_entry_count,
        metadata=command.metadata,
    )
    history_result = history_port.append(append_command)
    if (
        history_result.durable_write_performed is not True
        or history_result.adapter_kind == "deterministic_test_memory"
    ):
        raise SpecialistCapabilityGrowthClosedLoopSmokeError(
            "history append must provide durable SQL evidence"
        )

    selection_command = SchedulerApprovedSpecialistRevisionSelectionCommand(
        schema=SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_COMMAND_SCHEMA,
        command_ref=command.selection_command_ref,
        selection_ref=command.selection_ref,
        scheduler_ref=command.selection_policy.scheduler_ref,
        history_result=history_result,
        expected_snapshot_digest_sha256=history_result.snapshot.snapshot_digest,
        specialist_ref=command.proposal.specialist_ref,
        capability=command.capability,
        input_contract_ref=command.input_contract_ref,
        output_contract_ref=command.output_contract_ref,
        laboratory_ref=command.laboratory_ref,
        visit_mode=command.visit_mode,
        available_laboratory_capabilities=command.available_laboratory_capabilities,
        available_execution_boundaries=command.available_execution_boundaries,
        conversation_ref=command.conversation_ref,
        context_refs=command.context_refs,
        metadata=command.metadata,
    )
    selection_event = build_scheduler_approved_specialist_revision_selection_event(
        selection_command,
        source="specialist-capability-growth-closed-loop-smoke-0285-r8",
        correlation_id=command.smoke_ref,
    )
    selection = await SchedulerApprovedSpecialistRevisionSelectionHandler(
        command.selection_policy
    ).handle(selection_event)

    laboratory_result = await laboratory_executor(selection)
    lab_issues = _validate_laboratory_result(selection, laboratory_result)
    if lab_issues:
        raise SpecialistCapabilityGrowthClosedLoopSmokeError("; ".join(lab_issues))

    projection = build_specialist_capability_growth_observation_projection(selection)
    observation_event = build_specialist_capability_growth_observation_event(
        projection,
        event_id=command.observation_event_id,
    )
    await event_bus.publish(observation_event)
    publication = SpecialistCapabilityGrowthObservationPublicationReport(
        schema=SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PUBLICATION_SCHEMA,
        projection=projection,
        event_id=observation_event.id,
        event_type=EventType.SPECIALIST_REVISION_SELECTION_RESULT.name,
        published_count=1,
    )
    read_model = build_specialist_capability_growth_passive_read_model(
        observation_event
    )

    result = SpecialistCapabilityGrowthClosedLoopSmokeResult(
        schema=SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_RESULT_SCHEMA,
        command=command,
        blocking_proof=blocking_proof,
        decision=decision,
        history_result=history_result,
        selection=selection,
        laboratory_result=laboratory_result,
        observation_publication=publication,
        passive_read_model=read_model,
        phase_0285_closed=True,
    )
    return result


def bind_existing_portable_specialist_laboratory_executor(
    *,
    scheduler: object,
    smoke_command_factory: Callable[
        [SchedulerApprovedSpecialistRevisionSelectionResult], object
    ],
    store: object,
    passage_profile: object,
    embedder: object,
    projection_executor: object,
    recall_executor_factory: object,
    event_bus: object | None = None,
) -> ExistingPortableSpecialistLaboratoryExecutor:
    """Bind r8 to the existing 0284-r5 execution path without importing it eagerly."""

    if not callable(smoke_command_factory):
        raise TypeError("smoke_command_factory must be callable")

    async def execute(
        selection: SchedulerApprovedSpecialistRevisionSelectionResult,
    ) -> ExistingPortableSpecialistLaboratorySmokeResultPort:
        from context.specialists_laboratories_existing_chain_smoke_0284 import (
            PortableSpecialistExistingChainSmokeCommand,
            run_portable_specialist_existing_chain_smoke,
        )

        smoke_command = PortableSpecialistExistingChainSmokeCommand(
            descriptor=selection.selected_revision.descriptor,
            smoke=smoke_command_factory(selection),
            specialist_ref=selection.specialist_ref,
            visit_mode=selection.visit_mode,
        )
        return await run_portable_specialist_existing_chain_smoke(
            scheduler,
            smoke_command,
            store=store,
            passage_profile=passage_profile,
            embedder=embedder,
            projection_executor=projection_executor,
            recall_executor_factory=recall_executor_factory,
            event_bus=event_bus,
        )

    return execute


def _validate_laboratory_result(
    selection: SchedulerApprovedSpecialistRevisionSelectionResult,
    result: ExistingPortableSpecialistLaboratorySmokeResultPort,
) -> tuple[str, ...]:
    if not isinstance(result, ExistingPortableSpecialistLaboratorySmokeResultPort):
        return ("laboratory executor did not return the existing r5 result contract",)
    issues = list(result.issues)
    required = {
        "valid": result.valid,
        "portable_identity_preserved": result.portable_identity_preserved,
        "existing_scheduler_path_verified": result.existing_scheduler_path_verified,
        "fake_specialist_executed": result.fake_specialist_executed,
        "message_contract_closed": result.message_contract_closed,
        "durable_closed_loop_preserved": result.durable_closed_loop_preserved,
        "existing_scheduler_used": result.existing_scheduler_used,
    }
    for name, value in required.items():
        if value is not True:
            issues.append(f"laboratory result requires {name}=true")
    forbidden = {
        "scheduler_created": result.scheduler_created,
        "scheduler_modified": result.scheduler_modified,
        "parallel_orchestrator_created": result.parallel_orchestrator_created,
        "parallel_queue_created": result.parallel_queue_created,
        "parallel_eventbus_created": result.parallel_eventbus_created,
        "github_mutation_performed": result.github_mutation_performed,
        "real_specialist_backend_used": result.real_specialist_backend_used,
        "transfer_execution_performed": result.transfer_execution_performed,
    }
    for name, value in forbidden.items():
        if value is not False:
            issues.append(f"laboratory result requires {name}=false")
    if result.provider_ref != selection.laboratory_ref:
        issues.append("laboratory provider_ref must match Scheduler selection")
    if result.visit_status != "completed":
        issues.append("laboratory visit must be completed")
    descriptor = getattr(getattr(result, "command", None), "descriptor", None)
    if getattr(descriptor, "specialist_ref", None) != selection.specialist_ref:
        issues.append("laboratory command must preserve selected specialist_ref")
    if (
        getattr(descriptor, "specialist_version", None)
        != selection.selected_revision.descriptor.specialist_version
    ):
        issues.append("laboratory command must execute the selected revision version")
    return tuple(dict.fromkeys(issues))


def _require_ref(name: str, value: str, prefixes: tuple[str, ...]) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise SpecialistCapabilityGrowthClosedLoopSmokeError(
            f"{name} must be a typed reference"
        )
    if not value.startswith(prefixes):
        raise SpecialistCapabilityGrowthClosedLoopSmokeError(
            f"{name} must start with one of: {', '.join(prefixes)}"
        )


def _non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SpecialistCapabilityGrowthClosedLoopSmokeError(
            f"{name} must be non-empty"
        )


def _strings(name: str, values: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(values))
    if not normalized or not all(isinstance(value, str) and value for value in normalized):
        raise SpecialistCapabilityGrowthClosedLoopSmokeError(
            f"{name} must contain non-empty strings"
        )
    return normalized


def _metadata(values: Sequence[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        _non_empty("metadata key", key)
        _non_empty("metadata value", value)
        normalized[key.strip()] = value.strip()
    return tuple(sorted(normalized.items()))


def _suffix(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:16]


def _digest(mapping: Mapping[str, object]) -> str:
    payload = json.dumps(
        dict(mapping), ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return sha256(payload).hexdigest()


__all__ = (
    "SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_COMMAND_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_RESULT_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_VERSION",
    "ExistingPortableSpecialistLaboratoryExecutor",
    "ExistingPortableSpecialistLaboratorySmokeResultPort",
    "SpecialistCapabilityGrowthClosedLoopSmokeCommand",
    "SpecialistCapabilityGrowthClosedLoopSmokeError",
    "SpecialistCapabilityGrowthClosedLoopSmokeResult",
    "SpecialistCapabilityGrowthUnapprovedBlockingProof",
    "bind_existing_portable_specialist_laboratory_executor",
    "prove_unapproved_specialist_revisions_blocked",
    "run_specialist_capability_growth_closed_loop_smoke",
)
