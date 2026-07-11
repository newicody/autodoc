"""Fake laboratory deliberation composition for phase 0274-r2.

This module composes the existing server-oriented deliberation contracts,
specialist liaison synthesis, the 0274-r1 existing-Scheduler visit path and the
0273-r3 deterministic fake provider.

It does not create or start a Scheduler, queue, EventBus, registry, laboratory
manager or laboratory-local orchestrator.  The caller supplies the one already
running platform Scheduler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re

from contracts.scheduler import SchedulerContract
from context.laboratory_framework_contract_0273 import (
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
)
from context.scheduler_laboratory_visit_binding_0274 import (
    LaboratorySchedulerVisitReceipt,
    submit_laboratory_visit,
)
from context.server_oriented_deliberation_cycle import (
    DeliberationRound,
    FinalArtifactEnvelope,
    RefinedSpecialistDemand,
    ServerOrientation,
    SpecialistBusStatistics,
    SpecialistPreliminaryOpinion,
    build_bus_statistics_from_rounds,
    build_deliberation_round,
    build_refined_demands_from_opinions,
    build_specialist_preliminary_opinion,
)
from context.specialist_liaison_synthesis import (
    FinalSynthesisPacket,
    SpecialistLiaisonSynthesis,
    SpecialistOutputFragment,
    build_final_synthesis_packet,
    build_specialist_liaison_synthesis,
)

FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA = (
    "missipy.laboratory.fake_deliberation_command.v1"
)
FAKE_LABORATORY_DELIBERATION_RESULT_SCHEMA = (
    "missipy.laboratory.fake_deliberation_result.v1"
)
FAKE_LABORATORY_DELIBERATION_VERSION = "0274.r2"

_ALLOWED_SCENARIOS = frozenset(
    {"completed", "needs_context", "needs_specialist", "rejected", "failed"}
)
_FOLLOWUP_STANCES = frozenset(
    {
        "risky",
        "better_alternative",
        "needs_context",
        "needs_specialist",
        "analysis_signal",
    }
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_ALLOWED_ARTIFACT_PREFIXES = ("artifact:", "github:")
_ALLOWED_TARGET_PREFIXES = ("github:", "artifact:", "local:", "publication:")


class FakeLaboratoryDeliberationError(RuntimeError):
    """Raised when the bounded fake deliberation cannot be composed."""


@dataclass(frozen=True, slots=True)
class FakeLaboratoryDeliberationCommand:
    """One bounded local deliberation command for the fake laboratory."""

    orientation: ServerOrientation
    artifact_ref: str
    source_candidate_ref: str
    target_ref: str
    context_generation: int
    resource_budget: LaboratoryResourceBudget
    scenario_by_specialist: tuple[tuple[str, str], ...] = field(
        default_factory=tuple
    )
    priority: int = 0
    schema: str = FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA:
            raise FakeLaboratoryDeliberationError(
                "unsupported fake laboratory deliberation command schema"
            )
        if not isinstance(self.orientation, ServerOrientation):
            raise FakeLaboratoryDeliberationError(
                "orientation must be a ServerOrientation"
            )
        _require_typed_ref(
            "artifact_ref",
            self.artifact_ref,
            required_prefixes=_ALLOWED_ARTIFACT_PREFIXES,
        )
        _require_typed_ref("source_candidate_ref", self.source_candidate_ref)
        _require_typed_ref(
            "target_ref",
            self.target_ref,
            required_prefixes=_ALLOWED_TARGET_PREFIXES,
        )
        if isinstance(self.context_generation, bool) or not isinstance(
            self.context_generation, int
        ):
            raise FakeLaboratoryDeliberationError(
                "context_generation must be an integer"
            )
        if self.context_generation < 0:
            raise FakeLaboratoryDeliberationError(
                "context_generation must be >= 0"
            )
        if not isinstance(self.resource_budget, LaboratoryResourceBudget):
            raise FakeLaboratoryDeliberationError(
                "resource_budget must be LaboratoryResourceBudget"
            )
        if self.resource_budget.allow_network:
            raise FakeLaboratoryDeliberationError(
                "fake deliberation requires a network-closed budget"
            )
        if self.resource_budget.max_external_calls != 0:
            raise FakeLaboratoryDeliberationError(
                "fake deliberation refuses external calls"
            )
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise FakeLaboratoryDeliberationError("priority must be an integer")

        requested = set(self.orientation.requested_specialist_refs)
        normalized: list[tuple[str, str]] = []
        seen: set[str] = set()
        for specialist_ref, scenario in self.scenario_by_specialist:
            _require_typed_ref(
                "scenario specialist_ref",
                specialist_ref,
                required_prefixes=("specialist:", "llm:"),
            )
            if specialist_ref not in requested:
                raise FakeLaboratoryDeliberationError(
                    "scenario specialist_ref must be requested by orientation"
                )
            if specialist_ref in seen:
                raise FakeLaboratoryDeliberationError(
                    "scenario specialist_ref must be unique"
                )
            if scenario not in _ALLOWED_SCENARIOS:
                raise FakeLaboratoryDeliberationError(
                    f"unsupported fake scenario: {scenario}"
                )
            normalized.append((specialist_ref, scenario))
            seen.add(specialist_ref)
        object.__setattr__(self, "scenario_by_specialist", tuple(normalized))

    def scenario_for(self, specialist_ref: str) -> str:
        return dict(self.scenario_by_specialist).get(
            specialist_ref,
            "completed",
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "orientation": self.orientation.to_mapping(),
            "artifact_ref": self.artifact_ref,
            "source_candidate_ref": self.source_candidate_ref,
            "target_ref": self.target_ref,
            "context_generation": self.context_generation,
            "resource_budget": self.resource_budget.to_mapping(),
            "scenario_by_specialist": [
                {
                    "specialist_ref": specialist_ref,
                    "scenario": scenario,
                }
                for specialist_ref, scenario in self.scenario_by_specialist
            ],
            "priority": self.priority,
            "scheduler_created": False,
            "scheduler_run_owned": False,
            "parallel_orchestrator_created": False,
            "publication_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class FakeLaboratoryDeliberationResult:
    """Closed local deliberation result built around Scheduler visit receipts."""

    command: FakeLaboratoryDeliberationCommand
    receipts: tuple[LaboratorySchedulerVisitReceipt, ...]
    opinions: tuple[SpecialistPreliminaryOpinion, ...]
    refined_demands: tuple[RefinedSpecialistDemand, ...]
    round: DeliberationRound
    fragments: tuple[SpecialistOutputFragment, ...]
    synthesis: SpecialistLiaisonSynthesis
    bus_statistics: SpecialistBusStatistics
    final_packet: FinalSynthesisPacket | None
    final_artifact: FinalArtifactEnvelope | None
    publication_ready: bool
    schema: str = FAKE_LABORATORY_DELIBERATION_RESULT_SCHEMA
    existing_scheduler_used: bool = True
    scheduler_created: bool = False
    scheduler_run_owned: bool = False
    parallel_orchestrator_created: bool = False
    parallel_queue_created: bool = False
    parallel_eventbus_created: bool = False
    parallel_registry_created: bool = False
    sql_write_performed: bool = False
    qdrant_projection_performed: bool = False
    github_mutation_performed: bool = False

    def __post_init__(self) -> None:
        if self.schema != FAKE_LABORATORY_DELIBERATION_RESULT_SCHEMA:
            raise FakeLaboratoryDeliberationError(
                "unsupported fake laboratory deliberation result schema"
            )
        specialist_count = len(
            self.command.orientation.requested_specialist_refs
        )
        if not self.receipts or len(self.receipts) != specialist_count:
            raise FakeLaboratoryDeliberationError(
                "one Scheduler receipt is required per requested specialist"
            )
        if len(self.opinions) != specialist_count:
            raise FakeLaboratoryDeliberationError(
                "one preliminary opinion is required per specialist"
            )
        if len(self.fragments) != specialist_count:
            raise FakeLaboratoryDeliberationError(
                "one liaison fragment is required per specialist"
            )
        if self.round.orientation != self.command.orientation:
            raise FakeLaboratoryDeliberationError(
                "round orientation must match command orientation"
            )
        if self.round.opinions != self.opinions:
            raise FakeLaboratoryDeliberationError(
                "round opinions must match composed opinions"
            )
        if self.round.refined_demands != self.refined_demands:
            raise FakeLaboratoryDeliberationError(
                "round demands must match composed demands"
            )
        ready = (
            all(
                receipt.execution.result.status == "completed"
                for receipt in self.receipts
            )
            and self.round.convergence_state == "ready_for_final_synthesis"
            and not self.round.needs_next_round
        )
        if self.publication_ready != ready:
            raise FakeLaboratoryDeliberationError(
                "publication_ready must reflect completed converged visits"
            )
        if self.publication_ready:
            if self.final_packet is None or self.final_artifact is None:
                raise FakeLaboratoryDeliberationError(
                    "publication-ready result requires final local artifacts"
                )
        elif self.final_packet is not None or self.final_artifact is not None:
            raise FakeLaboratoryDeliberationError(
                "non-ready deliberation must not expose final artifacts"
            )
        forbidden = (
            not self.existing_scheduler_used,
            self.scheduler_created,
            self.scheduler_run_owned,
            self.parallel_orchestrator_created,
            self.parallel_queue_created,
            self.parallel_eventbus_created,
            self.parallel_registry_created,
            self.sql_write_performed,
            self.qdrant_projection_performed,
            self.github_mutation_performed,
        )
        if any(forbidden):
            raise FakeLaboratoryDeliberationError(
                "r2 must not claim a parallel authority or external effect"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "command": self.command.to_mapping(),
            "receipt_refs": [
                receipt.event_id for receipt in self.receipts
            ],
            "receipts": [
                receipt.to_mapping() for receipt in self.receipts
            ],
            "opinion_refs": [
                opinion.opinion_ref for opinion in self.opinions
            ],
            "opinions": [
                opinion.to_mapping() for opinion in self.opinions
            ],
            "refined_demand_refs": [
                demand.demand_ref for demand in self.refined_demands
            ],
            "refined_demands": [
                demand.to_mapping() for demand in self.refined_demands
            ],
            "round": self.round.to_mapping(),
            "fragments": [
                fragment.to_mapping() for fragment in self.fragments
            ],
            "synthesis": self.synthesis.to_mapping(),
            "bus_statistics": self.bus_statistics.to_mapping(),
            "final_packet": (
                None
                if self.final_packet is None
                else self.final_packet.to_mapping()
            ),
            "final_artifact": (
                None
                if self.final_artifact is None
                else self.final_artifact.to_mapping()
            ),
            "publication_ready": self.publication_ready,
            "publication_gate_required": True,
            "existing_scheduler_used": self.existing_scheduler_used,
            "scheduler_created": self.scheduler_created,
            "scheduler_run_owned": self.scheduler_run_owned,
            "parallel_orchestrator_created": (
                self.parallel_orchestrator_created
            ),
            "parallel_queue_created": self.parallel_queue_created,
            "parallel_eventbus_created": self.parallel_eventbus_created,
            "parallel_registry_created": self.parallel_registry_created,
            "sql_write_performed": self.sql_write_performed,
            "qdrant_projection_performed": (
                self.qdrant_projection_performed
            ),
            "github_mutation_performed": self.github_mutation_performed,
        }


async def run_fake_laboratory_deliberation(
    scheduler: SchedulerContract,
    command: FakeLaboratoryDeliberationCommand,
    *,
    timeout_per_visit: float | None = None,
) -> FakeLaboratoryDeliberationResult:
    """Compose one bounded fake deliberation through the existing Scheduler."""

    if not isinstance(scheduler, SchedulerContract):
        raise TypeError("scheduler must implement SchedulerContract")
    if not isinstance(command, FakeLaboratoryDeliberationCommand):
        raise TypeError(
            "command must be FakeLaboratoryDeliberationCommand"
        )

    receipts: list[LaboratorySchedulerVisitReceipt] = []
    opinions: list[SpecialistPreliminaryOpinion] = []
    fragments: list[SpecialistOutputFragment] = []

    for index, specialist_ref in enumerate(
        command.orientation.requested_specialist_refs
    ):
        scenario = command.scenario_for(specialist_ref)
        visit_request = _build_visit_request(
            command=command,
            specialist_ref=specialist_ref,
            specialist_index=index,
            scenario=scenario,
        )
        receipt = await submit_laboratory_visit(
            scheduler,
            visit_request,
            priority=command.priority,
            timeout=timeout_per_visit,
            source="laboratory.deliberation_composition",
        )
        receipts.append(receipt)
        opinions.append(
            _opinion_from_receipt(
                command=command,
                receipt=receipt,
            )
        )
        fragments.append(
            _fragment_from_receipt(
                command=command,
                receipt=receipt,
            )
        )

    opinion_tuple = tuple(opinions)
    all_demands = build_refined_demands_from_opinions(
        orientation=command.orientation,
        opinions=opinion_tuple,
        round_index=0,
    )
    followup_opinion_refs = {
        opinion.opinion_ref
        for opinion in opinion_tuple
        if opinion.stance in _FOLLOWUP_STANCES
    }
    refined_demands = tuple(
        demand
        for demand in all_demands
        if any(
            ref in followup_opinion_refs
            for ref in demand.source_opinion_refs
        )
    )
    round_ = build_deliberation_round(
        orientation=command.orientation,
        opinions=opinion_tuple,
        refined_demands=refined_demands,
        round_index=0,
    )
    fragment_tuple = tuple(fragments)
    synthesis = build_specialist_liaison_synthesis(
        request_ref=command.source_candidate_ref,
        title=f"Synthèse laboratoire — {command.orientation.title}",
        fragments=fragment_tuple,
    )
    bus_statistics = build_bus_statistics_from_rounds((round_,))

    publication_ready = (
        all(
            receipt.execution.result.status == "completed"
            for receipt in receipts
        )
        and round_.convergence_state == "ready_for_final_synthesis"
        and not round_.needs_next_round
    )
    final_packet: FinalSynthesisPacket | None = None
    final_artifact: FinalArtifactEnvelope | None = None
    if publication_ready:
        final_packet = build_final_synthesis_packet(
            synthesis=synthesis,
            target_ref=command.target_ref,
            mark_ready=True,
        )
        final_artifact = _build_final_artifact(
            command=command,
            packet=final_packet,
        )

    return FakeLaboratoryDeliberationResult(
        command=command,
        receipts=tuple(receipts),
        opinions=opinion_tuple,
        refined_demands=refined_demands,
        round=round_,
        fragments=fragment_tuple,
        synthesis=synthesis,
        bus_statistics=bus_statistics,
        final_packet=final_packet,
        final_artifact=final_artifact,
        publication_ready=publication_ready,
    )


def _build_visit_request(
    *,
    command: FakeLaboratoryDeliberationCommand,
    specialist_ref: str,
    specialist_index: int,
    scenario: str,
) -> LaboratoryVisitRequest:
    identity = (
        f"{command.orientation.orientation_ref}\0"
        f"{specialist_ref}\0{specialist_index}\0"
        f"{command.context_generation}"
    )
    short = _digest(identity)
    context_refs = _unique(
        (
            command.orientation.sql_context_ref,
            *command.orientation.context_refs,
        )
    )
    evidence_refs = _unique((command.artifact_ref,))
    return LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref=f"laboratory-visit:deliberation:{short}",
        laboratory_ref="laboratory:local-fake",
        specialist_ref=specialist_ref,
        objective_ref=command.orientation.orientation_ref,
        source_candidate_ref=command.source_candidate_ref,
        context_generation=command.context_generation,
        input_contract_ref="contract:missipy.specialist.demand.v1",
        expected_output_contract_ref=(
            "contract:missipy.laboratory.visit_result.v1"
        ),
        resource_budget=command.resource_budget,
        return_route_ref=f"route:laboratory/deliberation/{short}/result",
        context_refs=context_refs,
        evidence_refs=evidence_refs,
        metadata=(
            ("fake_scenario", scenario),
            ("deliberation_round", "0"),
            ("specialist_index", str(specialist_index)),
        ),
    )


def _opinion_from_receipt(
    *,
    command: FakeLaboratoryDeliberationCommand,
    receipt: LaboratorySchedulerVisitReceipt,
) -> SpecialistPreliminaryOpinion:
    result = receipt.execution.result
    stance, recommendation = _stance_and_recommendation(result.status)
    bus_ref = (
        "bus:laboratory-visit-observation:"
        + _digest(result.visit_ref)
    )
    return build_specialist_preliminary_opinion(
        orientation=command.orientation,
        specialist_ref=result.specialist_ref,
        stance=stance,
        summary=result.human_representation,
        recommendation=recommendation,
        evidence_refs=(
            result.evidence_refs
            or (command.orientation.sql_context_ref,)
        ),
        requested_context_refs=result.requested_context_refs,
        proposed_specialist_refs=result.requested_specialist_refs,
        review_request_refs=result.requested_specialist_refs,
        bus_observation_refs=(bus_ref,),
        confidence=result.confidence,
    )


def _fragment_from_receipt(
    *,
    command: FakeLaboratoryDeliberationCommand,
    receipt: LaboratorySchedulerVisitReceipt,
) -> SpecialistOutputFragment:
    result = receipt.execution.result
    identity = (
        f"{result.visit_ref}\0{result.status}\0"
        f"{result.specialist_ref}"
    )
    short = _digest(identity)
    return SpecialistOutputFragment(
        fragment_ref=f"specialist-fragment:laboratory:{short}",
        result_ref=f"specialist:laboratory-result:{short}",
        output_kind="laboratory_analysis",
        title=f"Résultat {result.specialist_ref}",
        body=result.human_representation,
        evidence_refs=(
            result.evidence_refs
            or (command.orientation.sql_context_ref,)
        ),
        context_delta_refs=result.requested_context_refs,
        review_request_refs=result.requested_specialist_refs,
        validation_refs=(),
        payload_ref=result.visit_ref,
        depth="audit" if result.status != "completed" else "standard",
        metadata=(
            ("laboratory_ref", result.laboratory_ref),
            ("visit_ref", result.visit_ref),
            ("status", result.status),
            ("real_backend_used", "false"),
        ),
    )


def _build_final_artifact(
    *,
    command: FakeLaboratoryDeliberationCommand,
    packet: FinalSynthesisPacket,
) -> FinalArtifactEnvelope:
    identity = (
        f"{command.artifact_ref}\0{packet.synthesis.synthesis_ref}\0"
        f"{command.target_ref}\0{packet.body}"
    )
    return FinalArtifactEnvelope(
        final_ref=f"artifact-final:laboratory:{_digest(identity)}",
        target_ref=command.target_ref,
        artifact_ref=command.artifact_ref,
        synthesis_ref=packet.synthesis.synthesis_ref,
        title=packet.title,
        body=packet.body,
        evidence_refs=packet.evidence_refs,
        context_influence_refs=packet.context_influence_refs,
        validation_refs=packet.validation_refs,
    )


def _stance_and_recommendation(status: str) -> tuple[str, str]:
    if status == "completed":
        return (
            "possible",
            "Conserver ce résultat pour la liaison et la synthèse locales.",
        )
    if status == "needs_context":
        return (
            "needs_context",
            "Réhydrater le contexte demandé avant une nouvelle ronde.",
        )
    if status == "needs_specialist":
        return (
            "needs_specialist",
            "Soumettre une demande typée au spécialiste proposé.",
        )
    if status == "rejected":
        return (
            "impossible",
            "Conserver le rejet comme signal local et ne pas publier.",
        )
    return (
        "risky",
        "Examiner l'échec et relancer seulement après décision de policy.",
    )


def _require_typed_ref(
    name: str,
    value: str,
    *,
    required_prefixes: tuple[str, ...] | None = None,
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.match(value):
        raise FakeLaboratoryDeliberationError(
            f"{name} must be a typed reference"
        )
    if required_prefixes is not None and not value.startswith(
        required_prefixes
    ):
        raise FakeLaboratoryDeliberationError(
            f"{name} must start with one of: "
            + ", ".join(required_prefixes)
        )


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


__all__ = (
    "FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA",
    "FAKE_LABORATORY_DELIBERATION_RESULT_SCHEMA",
    "FAKE_LABORATORY_DELIBERATION_VERSION",
    "FakeLaboratoryDeliberationCommand",
    "FakeLaboratoryDeliberationError",
    "FakeLaboratoryDeliberationResult",
    "run_fake_laboratory_deliberation",
)
