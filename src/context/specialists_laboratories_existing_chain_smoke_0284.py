"""Portable-specialist smoke over the existing Scheduler/laboratory chain.

Phase 0284-r5 does not introduce a second execution path.  It calls the
existing 0274 closed-loop smoke exactly once, selects one real Scheduler visit
receipt from that result, and projects the receipt into the portable specialist
and specialist/laboratory message contracts added by 0284-r2/r3.

The deterministic local fake provider remains the executed backend.  A real
specialist backend is not claimed.  Inter-laboratory transfer remains a typed
0284-r4 contract and is not executed while only the local fake laboratory is
registered.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
from typing import Any

from contracts.scheduler import SchedulerContract
from context.fake_laboratory_closed_local_handoff_0274 import (
    ExistingObservationBus,
    ExistingSqlContextStore,
)
from context.fake_laboratory_existing_scheduler_closed_loop_smoke_0274 import (
    EmbeddingCallable,
    FakeLaboratoryClosedLoopSmokeCommand,
    FakeLaboratoryClosedLoopSmokeResult,
    RecallExecutorFactory,
    run_fake_laboratory_existing_scheduler_closed_loop_smoke,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (
    EmbeddingSpaceProfile,
)
from context.portable_specialist_contract_0284 import (
    PortableSpecialistContractError,
    PortableSpecialistDescriptor,
    SpecialistLaboratoryVisitMode,
    validate_portable_specialist_visit_contract,
)
from context.scheduler_deliberation_route_contract import (
    SpecialistDemandFrame,
    SpecialistOpinionFrame,
)
from context.specialist_laboratory_message_contract_0284 import (
    SPECIALIST_LABORATORY_CONVERSATION_SCHEMA,
    SpecialistLaboratoryConversation,
    SpecialistLaboratoryMessageContractError,
    build_specialist_demand_message,
    build_specialist_opinion_message,
    validate_specialist_laboratory_conversation,
)

PORTABLE_SPECIALIST_EXISTING_CHAIN_SMOKE_VERSION = "0284.r5"
PORTABLE_SPECIALIST_EXISTING_CHAIN_SMOKE_COMMAND_SCHEMA = (
    "missipy.specialist.existing_chain_smoke_command.v1"
)
PORTABLE_SPECIALIST_EXISTING_CHAIN_SMOKE_RESULT_SCHEMA = (
    "missipy.specialist.existing_chain_smoke_result.v1"
)

_LOCAL_FAKE_LABORATORY_REF = "laboratory:local-fake"
_DEMAND_CONTRACT_REF = "contract:missipy.specialist.demand.v1"
_RESULT_CONTRACT_REF = "contract:missipy.laboratory.visit_result.v1"
_EXPECTED_SCHEDULER_PATH = (
    "Scheduler.emit()",
    "PolicyEngine.decide()",
    "PriorityQueue",
    "Scheduler.run()",
    "Dispatcher",
    "LaboratoryVisitRequestHandler",
    "LaboratoryProvider.execute()",
)


class PortableSpecialistExistingChainSmokeError(RuntimeError):
    """Raised when the portable smoke would violate the existing chain."""


@dataclass(frozen=True, slots=True)
class PortableSpecialistExistingChainSmokeCommand:
    """One portable specialist selected inside the existing 0274 smoke."""

    descriptor: PortableSpecialistDescriptor
    smoke: FakeLaboratoryClosedLoopSmokeCommand
    specialist_ref: str
    visit_mode: SpecialistLaboratoryVisitMode = "resident"
    schema: str = PORTABLE_SPECIALIST_EXISTING_CHAIN_SMOKE_COMMAND_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != PORTABLE_SPECIALIST_EXISTING_CHAIN_SMOKE_COMMAND_SCHEMA:
            raise PortableSpecialistExistingChainSmokeError(
                "unsupported portable specialist smoke command schema"
            )
        if not isinstance(self.descriptor, PortableSpecialistDescriptor):
            raise PortableSpecialistExistingChainSmokeError(
                "descriptor must be PortableSpecialistDescriptor"
            )
        if not isinstance(self.smoke, FakeLaboratoryClosedLoopSmokeCommand):
            raise PortableSpecialistExistingChainSmokeError(
                "smoke must be FakeLaboratoryClosedLoopSmokeCommand"
            )
        if self.specialist_ref != self.descriptor.specialist_ref:
            raise PortableSpecialistExistingChainSmokeError(
                "specialist_ref must match portable descriptor"
            )
        requested = self.smoke.deliberation.orientation.requested_specialist_refs
        if self.specialist_ref not in requested:
            raise PortableSpecialistExistingChainSmokeError(
                "portable specialist must be requested by deliberation orientation"
            )
        if self.descriptor.availability != "ready":
            raise PortableSpecialistExistingChainSmokeError(
                "portable specialist must be ready for the functional smoke"
            )
        issues = validate_portable_specialist_visit_contract(
            self.descriptor,
            specialist_ref=self.specialist_ref,
            laboratory_ref=_LOCAL_FAKE_LABORATORY_REF,
            input_contract_ref=_DEMAND_CONTRACT_REF,
            output_contract_ref=_RESULT_CONTRACT_REF,
            visit_mode=self.visit_mode,
        )
        if issues:
            raise PortableSpecialistExistingChainSmokeError("; ".join(issues))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "descriptor": self.descriptor.to_mapping(),
            "smoke": self.smoke.to_mapping(),
            "specialist_ref": self.specialist_ref,
            "visit_mode": self.visit_mode,
            "existing_scheduler_required": True,
            "scheduler_created": False,
            "parallel_orchestrator_created": False,
        }


@dataclass(frozen=True, slots=True)
class PortableSpecialistExistingChainSmokeResult:
    """Observable proof that one portable fake specialist used the real chain."""

    valid: bool
    issues: tuple[str, ...]
    command: PortableSpecialistExistingChainSmokeCommand
    existing_smoke: FakeLaboratoryClosedLoopSmokeResult
    conversation: SpecialistLaboratoryConversation | None = None
    visit_ref: str = ""
    provider_ref: str = ""
    visit_status: str = ""
    portable_identity_preserved: bool = False
    existing_scheduler_path_verified: bool = False
    fake_specialist_executed: bool = False
    message_contract_closed: bool = False
    durable_closed_loop_preserved: bool = False
    transfer_contract_available: bool = True
    transfer_execution_performed: bool = False
    existing_scheduler_used: bool = True
    scheduler_created: bool = False
    scheduler_modified: bool = False
    parallel_orchestrator_created: bool = False
    parallel_queue_created: bool = False
    parallel_eventbus_created: bool = False
    github_mutation_performed: bool = False
    real_specialist_backend_used: bool = False
    schema: str = PORTABLE_SPECIALIST_EXISTING_CHAIN_SMOKE_RESULT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != PORTABLE_SPECIALIST_EXISTING_CHAIN_SMOKE_RESULT_SCHEMA:
            raise PortableSpecialistExistingChainSmokeError(
                "unsupported portable specialist smoke result schema"
            )
        forbidden = (
            not self.existing_scheduler_used,
            self.scheduler_created,
            self.scheduler_modified,
            self.parallel_orchestrator_created,
            self.parallel_queue_created,
            self.parallel_eventbus_created,
            self.github_mutation_performed,
            self.real_specialist_backend_used,
            self.transfer_execution_performed,
        )
        if any(forbidden):
            raise PortableSpecialistExistingChainSmokeError(
                "r5 must preserve the fake single-Scheduler boundary"
            )
        if self.valid:
            required = (
                self.conversation is not None,
                self.portable_identity_preserved,
                self.existing_scheduler_path_verified,
                self.fake_specialist_executed,
                self.message_contract_closed,
                self.durable_closed_loop_preserved,
            )
            if not all(required):
                raise PortableSpecialistExistingChainSmokeError(
                    "valid r5 result requires the complete portable fake path"
                )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "command": self.command.to_mapping(),
            "existing_smoke": self.existing_smoke.to_mapping(),
            "conversation": (
                None if self.conversation is None else self.conversation.to_mapping()
            ),
            "visit_ref": self.visit_ref,
            "provider_ref": self.provider_ref,
            "visit_status": self.visit_status,
            "portable_identity_preserved": self.portable_identity_preserved,
            "existing_scheduler_path_verified": (
                self.existing_scheduler_path_verified
            ),
            "fake_specialist_executed": self.fake_specialist_executed,
            "message_contract_closed": self.message_contract_closed,
            "durable_closed_loop_preserved": self.durable_closed_loop_preserved,
            "transfer_contract_available": self.transfer_contract_available,
            "transfer_execution_performed": self.transfer_execution_performed,
            "existing_scheduler_used": self.existing_scheduler_used,
            "scheduler_created": self.scheduler_created,
            "scheduler_modified": self.scheduler_modified,
            "parallel_orchestrator_created": self.parallel_orchestrator_created,
            "parallel_queue_created": self.parallel_queue_created,
            "parallel_eventbus_created": self.parallel_eventbus_created,
            "github_mutation_performed": self.github_mutation_performed,
            "real_specialist_backend_used": self.real_specialist_backend_used,
            "live_path_status": "transition",
            "sql_remains_authority": True,
            "qdrant_projection_recall_only": True,
            "eventbus_observation_only": True,
        }


@dataclass(frozen=True, slots=True)
class _VisitRequestProjection:
    visit_ref: str
    laboratory_ref: str
    specialist_ref: str
    objective_ref: str
    input_contract_ref: str
    expected_output_contract_ref: str
    return_route_ref: str
    context_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    origin_laboratory_ref: str | None
    target_laboratory_ref: str | None
    conversation_ref: str | None


@dataclass(frozen=True, slots=True)
class _VisitResultProjection:
    visit_ref: str
    laboratory_ref: str
    specialist_ref: str
    status: str
    output_contract_ref: str
    machine_result: Mapping[str, Any]
    human_representation: str
    confidence: float
    evidence_refs: tuple[str, ...]
    requested_context_refs: tuple[str, ...]
    requested_laboratory_refs: tuple[str, ...]
    conversation_ref: str | None


async def run_portable_specialist_existing_chain_smoke(
    scheduler: SchedulerContract,
    command: PortableSpecialistExistingChainSmokeCommand,
    *,
    store: ExistingSqlContextStore,
    passage_profile: EmbeddingSpaceProfile,
    embedder: EmbeddingCallable,
    projection_executor: Any,
    recall_executor_factory: RecallExecutorFactory,
    event_bus: ExistingObservationBus | None = None,
) -> PortableSpecialistExistingChainSmokeResult:
    """Run one portable specialist through the existing closed-loop smoke."""

    if not isinstance(scheduler, SchedulerContract):
        raise TypeError("scheduler must implement SchedulerContract")
    if not isinstance(command, PortableSpecialistExistingChainSmokeCommand):
        raise TypeError("command must be PortableSpecialistExistingChainSmokeCommand")

    existing = await run_fake_laboratory_existing_scheduler_closed_loop_smoke(
        scheduler,
        command.smoke,
        store=store,
        passage_profile=passage_profile,
        embedder=embedder,
        projection_executor=projection_executor,
        recall_executor_factory=recall_executor_factory,
        event_bus=event_bus,
    )
    issues = list(existing.issues)
    if not existing.valid:
        return _result(command=command, existing=existing, issues=issues)

    try:
        receipt = _select_mapping(
            existing.deliberation,
            collection_key="receipts",
            specialist_ref=command.specialist_ref,
            nested_path=("execution", "request", "specialist_ref"),
        )
        opinion = _select_mapping(
            existing.deliberation,
            collection_key="opinions",
            specialist_ref=command.specialist_ref,
            nested_path=("specialist_ref",),
        )
        execution = _mapping_at(receipt, "execution")
        request = _request_projection(_mapping_at(execution, "request"))
        visit_result = _result_projection(_mapping_at(execution, "result"))
        demand_frame = _build_demand_frame(request)
        opinion_frame = _build_opinion_frame(
            request=request,
            opinion=opinion,
            demand_frame=demand_frame,
        )
        demand_message = build_specialist_demand_message(
            command.descriptor,
            request,
            demand_frame,
            visit_mode=command.visit_mode,
        )
        opinion_message = build_specialist_opinion_message(
            command.descriptor,
            request,
            visit_result,
            opinion_frame,
            demand_message=demand_message,
        )
        conversation = SpecialistLaboratoryConversation(
            schema=SPECIALIST_LABORATORY_CONVERSATION_SCHEMA,
            conversation_ref=demand_message.conversation_ref,
            visit_ref=request.visit_ref,
            specialist_ref=request.specialist_ref,
            messages=(demand_message, opinion_message),
        )
    except (
        KeyError,
        TypeError,
        ValueError,
        PortableSpecialistContractError,
        SpecialistLaboratoryMessageContractError,
        PortableSpecialistExistingChainSmokeError,
    ) as exc:
        issues.append(f"portable specialist projection failed: {exc}")
        return _result(command=command, existing=existing, issues=issues)

    conversation_issues = validate_specialist_laboratory_conversation(conversation)
    issues.extend(conversation_issues)
    scheduler_path = tuple(_strings(receipt.get("scheduler_path", ())))
    identity_preserved = (
        request.specialist_ref
        == visit_result.specialist_ref
        == conversation.specialist_ref
        == command.descriptor.specialist_ref
    )
    scheduler_path_verified = scheduler_path == _EXPECTED_SCHEDULER_PATH
    fake_executed = (
        receipt.get("provider_ref") == _LOCAL_FAKE_LABORATORY_REF
        and visit_result.status == "completed"
        and _mapping_at(execution, "result").get("publication_allowed") is False
    )
    message_closed = not conversation_issues and len(conversation.messages) == 2
    durable_preserved = (
        existing.closed_loop_complete
        and existing.sql_replay_verified
        and existing.specialist_output_verified
        and bool(existing.sql_ref)
    )
    if not identity_preserved:
        issues.append("portable specialist identity changed across the existing path")
    if not scheduler_path_verified:
        issues.append("existing Scheduler path does not match the canonical chain")
    if not fake_executed:
        issues.append("deterministic fake specialist visit was not completed")
    if not message_closed:
        issues.append("specialist/laboratory conversation did not close")
    if not durable_preserved:
        issues.append("existing durable SQL/Qdrant closure was not preserved")

    return _result(
        command=command,
        existing=existing,
        issues=issues,
        conversation=conversation,
        visit_ref=request.visit_ref,
        provider_ref=str(receipt.get("provider_ref", "")),
        visit_status=visit_result.status,
        portable_identity_preserved=identity_preserved,
        existing_scheduler_path_verified=scheduler_path_verified,
        fake_specialist_executed=fake_executed,
        message_contract_closed=message_closed,
        durable_closed_loop_preserved=durable_preserved,
    )


def _build_demand_frame(request: _VisitRequestProjection) -> SpecialistDemandFrame:
    suffix = _stable_suffix(request.visit_ref)
    return SpecialistDemandFrame(
        frame_ref=f"route-frame:demand-{suffix}",
        route_ref=f"route:portable-specialist/{suffix}/demand",
        cycle_command_ref=f"command:portable-specialist-cycle-{suffix}",
        round_command_ref=f"command:portable-specialist-round-{suffix}",
        specialist_ref=request.specialist_ref,
        request_text=(
            "Execute the bounded laboratory objective " + request.objective_ref
        ),
        context_refs=request.context_refs,
        expected_output="laboratory_visit_result",
        depth="standard",
    )


def _build_opinion_frame(
    *,
    request: _VisitRequestProjection,
    opinion: Mapping[str, Any],
    demand_frame: SpecialistDemandFrame,
) -> SpecialistOpinionFrame:
    suffix = _stable_suffix(request.visit_ref + "|opinion")
    return SpecialistOpinionFrame(
        frame_ref=f"route-frame:opinion-{suffix}",
        route_ref=f"route:portable-specialist/{suffix}/opinion",
        demand_frame_ref=demand_frame.frame_ref,
        specialist_ref=request.specialist_ref,
        opinion_ref=_string_at(opinion, "opinion_ref"),
        stance=_string_at(opinion, "stance"),
        summary=_string_at(opinion, "summary"),
        context_delta_refs=tuple(_strings(opinion.get("context_delta_refs", ()))),
        observation_fact_refs=tuple(
            _strings(opinion.get("bus_observation_refs", ()))
        ),
    )


def _request_projection(mapping: Mapping[str, Any]) -> _VisitRequestProjection:
    return _VisitRequestProjection(
        visit_ref=_string_at(mapping, "visit_ref"),
        laboratory_ref=_string_at(mapping, "laboratory_ref"),
        specialist_ref=_string_at(mapping, "specialist_ref"),
        objective_ref=_string_at(mapping, "objective_ref"),
        input_contract_ref=_string_at(mapping, "input_contract_ref"),
        expected_output_contract_ref=_string_at(
            mapping, "expected_output_contract_ref"
        ),
        return_route_ref=_string_at(mapping, "return_route_ref"),
        context_refs=tuple(_strings(mapping.get("context_refs", ()))),
        evidence_refs=tuple(_strings(mapping.get("evidence_refs", ()))),
        origin_laboratory_ref=_optional_string(mapping.get("origin_laboratory_ref")),
        target_laboratory_ref=_optional_string(mapping.get("target_laboratory_ref")),
        conversation_ref=_optional_string(mapping.get("conversation_ref")),
    )


def _result_projection(mapping: Mapping[str, Any]) -> _VisitResultProjection:
    confidence = mapping.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise PortableSpecialistExistingChainSmokeError(
            "visit result confidence must be numeric"
        )
    machine_result = mapping.get("machine_result")
    if not isinstance(machine_result, Mapping):
        raise PortableSpecialistExistingChainSmokeError(
            "visit result machine_result must be a mapping"
        )
    return _VisitResultProjection(
        visit_ref=_string_at(mapping, "visit_ref"),
        laboratory_ref=_string_at(mapping, "laboratory_ref"),
        specialist_ref=_string_at(mapping, "specialist_ref"),
        status=_string_at(mapping, "status"),
        output_contract_ref=_string_at(mapping, "output_contract_ref"),
        machine_result=machine_result,
        human_representation=_string_at(mapping, "human_representation"),
        confidence=float(confidence),
        evidence_refs=tuple(_strings(mapping.get("evidence_refs", ()))),
        requested_context_refs=tuple(
            _strings(mapping.get("requested_context_refs", ()))
        ),
        requested_laboratory_refs=tuple(
            _strings(mapping.get("requested_laboratory_refs", ()))
        ),
        conversation_ref=_optional_string(mapping.get("conversation_ref")),
    )


def _select_mapping(
    root: Mapping[str, Any],
    *,
    collection_key: str,
    specialist_ref: str,
    nested_path: tuple[str, ...],
) -> Mapping[str, Any]:
    values = root.get(collection_key)
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise PortableSpecialistExistingChainSmokeError(
            f"{collection_key} must be a sequence"
        )
    for value in values:
        if not isinstance(value, Mapping):
            continue
        current: Any = value
        for key in nested_path:
            if not isinstance(current, Mapping):
                current = None
                break
            current = current.get(key)
        if current == specialist_ref:
            return value
    raise PortableSpecialistExistingChainSmokeError(
        f"no {collection_key} entry for {specialist_ref}"
    )


def _mapping_at(mapping: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, Mapping):
        raise PortableSpecialistExistingChainSmokeError(
            f"{key} must be a mapping"
        )
    return value


def _string_at(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise PortableSpecialistExistingChainSmokeError(
            f"{key} must be a non-empty string"
        )
    return value


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise PortableSpecialistExistingChainSmokeError(
            "optional reference must be a non-empty string"
        )
    return value


def _strings(values: object) -> tuple[str, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise PortableSpecialistExistingChainSmokeError(
            "reference collection must be a sequence"
        )
    normalized = tuple(values)
    if not all(isinstance(value, str) and value for value in normalized):
        raise PortableSpecialistExistingChainSmokeError(
            "reference collection must contain non-empty strings"
        )
    return normalized


def _stable_suffix(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _result(
    *,
    command: PortableSpecialistExistingChainSmokeCommand,
    existing: FakeLaboratoryClosedLoopSmokeResult,
    issues: Sequence[str],
    conversation: SpecialistLaboratoryConversation | None = None,
    visit_ref: str = "",
    provider_ref: str = "",
    visit_status: str = "",
    portable_identity_preserved: bool = False,
    existing_scheduler_path_verified: bool = False,
    fake_specialist_executed: bool = False,
    message_contract_closed: bool = False,
    durable_closed_loop_preserved: bool = False,
) -> PortableSpecialistExistingChainSmokeResult:
    normalized = tuple(dict.fromkeys(str(issue) for issue in issues if str(issue)))
    return PortableSpecialistExistingChainSmokeResult(
        valid=not normalized,
        issues=normalized,
        command=command,
        existing_smoke=existing,
        conversation=conversation,
        visit_ref=visit_ref,
        provider_ref=provider_ref,
        visit_status=visit_status,
        portable_identity_preserved=portable_identity_preserved,
        existing_scheduler_path_verified=existing_scheduler_path_verified,
        fake_specialist_executed=fake_specialist_executed,
        message_contract_closed=message_contract_closed,
        durable_closed_loop_preserved=durable_closed_loop_preserved,
    )


__all__ = (
    "PORTABLE_SPECIALIST_EXISTING_CHAIN_SMOKE_COMMAND_SCHEMA",
    "PORTABLE_SPECIALIST_EXISTING_CHAIN_SMOKE_RESULT_SCHEMA",
    "PORTABLE_SPECIALIST_EXISTING_CHAIN_SMOKE_VERSION",
    "PortableSpecialistExistingChainSmokeCommand",
    "PortableSpecialistExistingChainSmokeError",
    "PortableSpecialistExistingChainSmokeResult",
    "run_portable_specialist_existing_chain_smoke",
)
