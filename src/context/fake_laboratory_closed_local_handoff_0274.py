"""Closed local handoff for fake laboratory deliberation results.

0274-r3 composes existing durable, vector, observation and visual surfaces
around the converged result produced by 0274-r2.

The module:
- persists one immutable ``specialist_output`` record through an injected
  existing SQLContextStore;
- reuses the 0261 SQL -> OpenVINO/E5 path;
- reuses the r9 embedding-space compatibility gate;
- reuses the 0262 embedding -> Qdrant projection path;
- emits fact-only Events to an injected existing EventBus;
- reuses the 0266 PassiveSupervisor read-model;
- reuses the 0236/0237 renderer-neutral visual models;
- builds a local GitHub publication preview that still requires the existing
  publication review/mutation gate.

It creates no Scheduler, queue, EventBus, registry, laboratory orchestrator,
SQL authority, Qdrant authority, renderer or GitHub client.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Any, Callable, Protocol

from contracts.event import Event, EventType
from context.closed_result_frame_eventbus_observation_0265 import (
    ClosedResultFrameObservationFact,
)
from context.fake_laboratory_deliberation_composition_0274 import (
    FakeLaboratoryDeliberationResult,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (
    EmbeddingSpaceProfile,
    attach_profile_to_embedding,
    validate_embedding_against_profile,
)
from context.passive_supervisor_closed_result_frame_observation_0266 import (
    build_passive_supervisor_closed_frame_observation_report,
)
from context.passive_supervisor_visual_layout_model import (
    build_passive_supervisor_visual_layout_model,
)
from context.passive_supervisor_visual_read_model import (
    build_visual_read_model,
)
from context.scheduler_managed_embedding_qdrant_projection_usage_0262 import (
    SchedulerManagedEmbeddingQdrantProjectionRequest,
    run_scheduler_managed_embedding_qdrant_projection_usage,
)
from context.scheduler_managed_sql_ref_openvino_embedding_usage_0261 import (
    SchedulerManagedSqlRefOpenVinoEmbeddingRequest,
    run_scheduler_managed_sql_ref_openvino_embedding_usage,
)
from context.sql_context_store import (
    SqlContextRecord,
    SqlContextStoreWriteResult,
    build_sql_context_record,
)

FAKE_LABORATORY_CLOSED_HANDOFF_COMMAND_SCHEMA = (
    "missipy.laboratory.closed_local_handoff_command.v1"
)
FAKE_LABORATORY_CLOSED_HANDOFF_RESULT_SCHEMA = (
    "missipy.laboratory.closed_local_handoff_result.v1"
)
LABORATORY_GITHUB_PUBLICATION_PREVIEW_SCHEMA = (
    "missipy.laboratory.github_publication_preview.v1"
)
LABORATORY_OBSERVATION_SCHEMA = (
    "missipy.laboratory.closed_local_observation.v1"
)
FAKE_LABORATORY_CLOSED_HANDOFF_VERSION = "0274.r3"

OBSERVATION_SOURCE = "laboratory.closed_local_handoff"
OBSERVATION_DESTINATION = "observability"


class ExistingSqlContextStore(Protocol):
    """Existing SQL authority surface required by this composition."""

    def initialize_schema(self) -> None:
        """Initialize the existing schema."""

    def get_record(self, context_ref: str) -> object | None:
        """Read one durable record."""

    def upsert_record(self, record: SqlContextRecord) -> SqlContextStoreWriteResult:
        """Persist one record through the existing store."""


class ExistingObservationBus(Protocol):
    """Existing EventBus publish surface; no EventBus is constructed here."""

    async def publish(self, event: Event) -> None:
        """Publish one immutable observation fact."""


EmbeddingCallable = Callable[[str, str, str | None, str], Mapping[str, Any]]


class FakeLaboratoryClosedHandoffError(RuntimeError):
    """Raised when the local closure violates an authority boundary."""


@dataclass(frozen=True, slots=True)
class FakeLaboratoryClosedHandoffCommand:
    """Explicit effects allowed for one converged fake laboratory result."""

    execute: bool = False
    policy_decision_id: str = ""
    vector_execute: bool = False
    publish_observations: bool = False
    model_dir: str | None = None
    device: str = "CPU"
    frame_ref: str = "laboratory-frame:0274-r3"
    schema: str = FAKE_LABORATORY_CLOSED_HANDOFF_COMMAND_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != FAKE_LABORATORY_CLOSED_HANDOFF_COMMAND_SCHEMA:
            raise FakeLaboratoryClosedHandoffError(
                "unsupported closed handoff command schema"
            )
        if self.execute and not self.policy_decision_id.strip():
            raise FakeLaboratoryClosedHandoffError(
                "execute requires policy_decision_id"
            )
        if self.vector_execute and not self.execute:
            raise FakeLaboratoryClosedHandoffError(
                "vector_execute requires execute"
            )
        if self.publish_observations and not self.execute:
            raise FakeLaboratoryClosedHandoffError(
                "publish_observations requires execute"
            )
        if not self.frame_ref.startswith("laboratory-frame:"):
            raise FakeLaboratoryClosedHandoffError(
                "frame_ref must start with laboratory-frame:"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "vector_execute": self.vector_execute,
            "publish_observations": self.publish_observations,
            "model_dir": self.model_dir,
            "device": self.device,
            "frame_ref": self.frame_ref,
        }


@dataclass(frozen=True, slots=True)
class LaboratoryGitHubPublicationPreview:
    """Local preview only; it never authorizes a GitHub mutation."""

    preview_ref: str
    target_ref: str
    final_ref: str
    synthesis_ref: str
    sql_ref: str
    title: str
    body: str
    evidence_refs: tuple[str, ...]
    status: str = "pending"
    review_surface: str = "context.github_publication_review"
    publication_gate_required: bool = True
    remote_mutation_allowed: bool = False
    github_mutation_performed: bool = False

    def __post_init__(self) -> None:
        if not self.preview_ref.startswith("github-preview:"):
            raise FakeLaboratoryClosedHandoffError(
                "preview_ref must start with github-preview:"
            )
        if not self.sql_ref.startswith("sql:"):
            raise FakeLaboratoryClosedHandoffError(
                "preview sql_ref must start with sql:"
            )
        if not self.title.strip() or not self.body.strip():
            raise FakeLaboratoryClosedHandoffError(
                "preview title and body must be non-empty"
            )
        if (
            not self.publication_gate_required
            or self.remote_mutation_allowed
            or self.github_mutation_performed
        ):
            raise FakeLaboratoryClosedHandoffError(
                "GitHub preview must remain local and gated"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": LABORATORY_GITHUB_PUBLICATION_PREVIEW_SCHEMA,
            "preview_ref": self.preview_ref,
            "target_ref": self.target_ref,
            "final_ref": self.final_ref,
            "synthesis_ref": self.synthesis_ref,
            "sql_ref": self.sql_ref,
            "title": self.title,
            "body": self.body,
            "evidence_refs": list(self.evidence_refs),
            "status": self.status,
            "review_surface": self.review_surface,
            "publication_gate_required": self.publication_gate_required,
            "remote_mutation_allowed": self.remote_mutation_allowed,
            "github_mutation_performed": self.github_mutation_performed,
        }


@dataclass(frozen=True, slots=True)
class FakeLaboratoryClosedHandoffResult:
    """Complete local closure report for one converged fake deliberation."""

    valid: bool
    issues: tuple[str, ...]
    command: FakeLaboratoryClosedHandoffCommand
    sql_record: Mapping[str, Any]
    sql_write: Mapping[str, Any] = field(default_factory=dict)
    sql_readback: Mapping[str, Any] = field(default_factory=dict)
    embedding: Mapping[str, Any] = field(default_factory=dict)
    compatibility: Mapping[str, Any] = field(default_factory=dict)
    projection: Mapping[str, Any] = field(default_factory=dict)
    observation_facts: tuple[Mapping[str, Any], ...] = ()
    published_event_ids: tuple[str, ...] = ()
    passive_supervisor: Mapping[str, Any] = field(default_factory=dict)
    visual_read_model: Mapping[str, Any] = field(default_factory=dict)
    visual_layout: Mapping[str, Any] = field(default_factory=dict)
    github_preview: Mapping[str, Any] = field(default_factory=dict)
    sql_write_performed: bool = False
    sql_readback_performed: bool = False
    openvino_call_performed: bool = False
    qdrant_write_performed: bool = False
    eventbus_publish_performed: bool = False
    github_mutation_performed: bool = False
    existing_scheduler_used_upstream: bool = True
    scheduler_created: bool = False
    scheduler_modified: bool = False
    parallel_orchestrator_created: bool = False
    parallel_eventbus_created: bool = False
    parallel_registry_created: bool = False
    schema: str = FAKE_LABORATORY_CLOSED_HANDOFF_RESULT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != FAKE_LABORATORY_CLOSED_HANDOFF_RESULT_SCHEMA:
            raise FakeLaboratoryClosedHandoffError(
                "unsupported closed handoff result schema"
            )
        forbidden = (
            self.github_mutation_performed,
            self.scheduler_created,
            self.scheduler_modified,
            self.parallel_orchestrator_created,
            self.parallel_eventbus_created,
            self.parallel_registry_created,
        )
        if any(forbidden):
            raise FakeLaboratoryClosedHandoffError(
                "closed handoff must not claim a parallel authority"
            )
        if self.command.execute and self.valid:
            if not self.sql_write_performed or not self.sql_readback_performed:
                raise FakeLaboratoryClosedHandoffError(
                    "successful execute mode requires SQL write and readback"
                )
        if self.command.vector_execute and self.valid:
            if not self.openvino_call_performed or not self.qdrant_write_performed:
                raise FakeLaboratoryClosedHandoffError(
                    "successful vector execution requires embedding and projection"
                )
        if self.command.publish_observations and self.valid:
            if not self.eventbus_publish_performed:
                raise FakeLaboratoryClosedHandoffError(
                    "successful observation mode requires existing EventBus publish"
                )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "command": self.command.to_mapping(),
            "sql_record": dict(self.sql_record),
            "sql_write": dict(self.sql_write),
            "sql_readback": dict(self.sql_readback),
            "embedding": dict(self.embedding),
            "compatibility": dict(self.compatibility),
            "projection": dict(self.projection),
            "observation_facts": [
                dict(fact) for fact in self.observation_facts
            ],
            "published_event_ids": list(self.published_event_ids),
            "passive_supervisor": dict(self.passive_supervisor),
            "visual_read_model": dict(self.visual_read_model),
            "visual_layout": dict(self.visual_layout),
            "github_preview": dict(self.github_preview),
            "sql_write_performed": self.sql_write_performed,
            "sql_readback_performed": self.sql_readback_performed,
            "openvino_call_performed": self.openvino_call_performed,
            "qdrant_write_performed": self.qdrant_write_performed,
            "eventbus_publish_performed": self.eventbus_publish_performed,
            "github_mutation_performed": self.github_mutation_performed,
            "existing_scheduler_used_upstream": self.existing_scheduler_used_upstream,
            "scheduler_created": self.scheduler_created,
            "scheduler_modified": self.scheduler_modified,
            "parallel_orchestrator_created": self.parallel_orchestrator_created,
            "parallel_eventbus_created": self.parallel_eventbus_created,
            "parallel_registry_created": self.parallel_registry_created,
            "sql_remains_authority": True,
            "qdrant_projection_only": True,
            "eventbus_observation_only": True,
            "passive_supervisor_observation_only": True,
            "vispy_passive": True,
            "publication_gate_required": True,
        }


async def run_fake_laboratory_closed_local_handoff(
    deliberation: FakeLaboratoryDeliberationResult,
    command: FakeLaboratoryClosedHandoffCommand,
    *,
    store: ExistingSqlContextStore | None = None,
    profile: EmbeddingSpaceProfile | None = None,
    embedder: EmbeddingCallable | None = None,
    qdrant_executor: Any | None = None,
    event_bus: ExistingObservationBus | None = None,
) -> FakeLaboratoryClosedHandoffResult:
    """Close one converged fake deliberation through existing local surfaces."""

    issues = list(_validate_deliberation(deliberation))
    if command.execute and store is None:
        issues.append("execute requires an existing SQLContextStore")
    if command.vector_execute and qdrant_executor is None:
        issues.append("vector_execute requires an injected Qdrant executor")
    if command.publish_observations and event_bus is None:
        issues.append("publish_observations requires an existing EventBus")

    sql_record = _build_sql_record(deliberation) if not issues else None
    if sql_record is None:
        return _result(
            issues=issues,
            command=command,
            sql_record={},
        )

    preview = _build_github_preview(deliberation, sql_record.context_ref)
    base_facts = _build_observation_facts(
        deliberation,
        sql_ref=sql_record.context_ref,
        vector_state="pending" if command.vector_execute else "not_requested",
    )
    passive, read_model, layout = _build_passive_visual_models(
        deliberation,
        sql_ref=sql_record.context_ref,
        facts=base_facts,
        qdrant_ref="",
    )

    if issues or not command.execute:
        return _result(
            issues=issues,
            command=command,
            sql_record=sql_record.to_mapping(),
            observation_facts=tuple(fact.to_mapping() for fact in base_facts),
            passive_supervisor=passive,
            visual_read_model=read_model,
            visual_layout=layout,
            github_preview=preview.to_mapping(),
        )

    assert store is not None
    store.initialize_schema()
    existing = store.get_record(sql_record.context_ref)
    if existing is not None:
        existing_mapping = _public_mapping(existing)
        if existing_mapping != sql_record.to_mapping():
            issues.append(
                "immutable SQL specialist_output collision for context_ref"
            )
            return _result(
                issues=issues,
                command=command,
                sql_record=sql_record.to_mapping(),
                sql_readback=existing_mapping,
                observation_facts=tuple(
                    fact.to_mapping() for fact in base_facts
                ),
                passive_supervisor=passive,
                visual_read_model=read_model,
                visual_layout=layout,
                github_preview=preview.to_mapping(),
            )
        write_mapping = {
            "schema": "missipy.sql_context_store.write.v1",
            "context_ref": sql_record.context_ref,
            "inserted": False,
            "replaced": False,
            "idempotent_replay": True,
            "record": sql_record.to_mapping(),
        }
    else:
        write_result = store.upsert_record(sql_record)
        write_mapping = write_result.to_mapping()
        write_mapping["idempotent_replay"] = False

    readback = store.get_record(sql_record.context_ref)
    readback_mapping = _public_mapping(readback)
    if readback_mapping != sql_record.to_mapping():
        issues.append("SQL readback does not match immutable specialist output")

    embedding_mapping: dict[str, Any] = {}
    compatibility_mapping: dict[str, Any] = {}
    projection_mapping: dict[str, Any] = {}
    openvino_called = False
    qdrant_written = False
    qdrant_ref = ""

    if not issues and command.vector_execute:
        effective_profile = profile or EmbeddingSpaceProfile()
        embedding_request = SchedulerManagedSqlRefOpenVinoEmbeddingRequest(
            sql_ref=sql_record.context_ref,
            role=effective_profile.role,
            policy_decision_id=command.policy_decision_id,
            model_dir=command.model_dir,
            device=command.device,
        )
        embedding_result = run_scheduler_managed_sql_ref_openvino_embedding_usage(
            store,
            embedding_request,
            execute=True,
            embedder=embedder,
        )
        embedding_mapping = embedding_result.to_mapping()
        openvino_called = True
        if not embedding_result.valid:
            issues.extend(embedding_result.issues)
        else:
            raw_embedding = _mapping(embedding_mapping.get("embedding"))
            compatibility = validate_embedding_against_profile(
                raw_embedding,
                effective_profile,
                expected_sql_ref=sql_record.context_ref,
            )
            compatibility_mapping = compatibility.to_mapping()
            if not compatibility.compatible:
                issues.extend(compatibility.issues)
            else:
                profiled = attach_profile_to_embedding(
                    raw_embedding,
                    effective_profile,
                )
                profiled_report = dict(embedding_mapping)
                profiled_report["embedding"] = profiled
                projection_result = (
                    run_scheduler_managed_embedding_qdrant_projection_usage(
                        profiled_report,
                        SchedulerManagedEmbeddingQdrantProjectionRequest(
                            policy_decision_id=command.policy_decision_id,
                            collection_name=effective_profile.collection_name,
                            vector_dimension=effective_profile.dimension,
                        ),
                        execute=True,
                        executor=qdrant_executor,
                    )
                )
                projection_mapping = projection_result.to_mapping()
                if not projection_result.valid:
                    issues.extend(projection_result.issues)
                write_result = _mapping(
                    projection_mapping.get("write_result")
                )
                qdrant_written = write_result.get("acknowledged") is True
                if not qdrant_written:
                    issues.append("Qdrant projection was not acknowledged")
                else:
                    qdrant_ref = (
                        "qdrant:"
                        + effective_profile.collection_name
                        + ":"
                        + _digest(sql_record.context_ref)
                    )

    facts = _build_observation_facts(
        deliberation,
        sql_ref=sql_record.context_ref,
        vector_state=(
            "projected"
            if qdrant_written
            else "failed"
            if command.vector_execute and issues
            else "not_requested"
        ),
        qdrant_ref=qdrant_ref,
    )

    published_event_ids: tuple[str, ...] = ()
    if not issues and command.publish_observations:
        assert event_bus is not None
        published: list[str] = []
        for fact in facts:
            event = _fact_to_event(fact)
            await event_bus.publish(event)
            published.append(event.id)
        published_event_ids = tuple(published)

    passive, read_model, layout = _build_passive_visual_models(
        deliberation,
        sql_ref=sql_record.context_ref,
        facts=facts,
        qdrant_ref=qdrant_ref,
    )

    return _result(
        issues=issues,
        command=command,
        sql_record=sql_record.to_mapping(),
        sql_write=write_mapping,
        sql_readback=readback_mapping,
        embedding=embedding_mapping,
        compatibility=compatibility_mapping,
        projection=projection_mapping,
        observation_facts=tuple(fact.to_mapping() for fact in facts),
        published_event_ids=published_event_ids,
        passive_supervisor=passive,
        visual_read_model=read_model,
        visual_layout=layout,
        github_preview=preview.to_mapping(),
        sql_write_performed=not issues,
        sql_readback_performed=not issues,
        openvino_call_performed=openvino_called,
        qdrant_write_performed=qdrant_written,
        eventbus_publish_performed=bool(published_event_ids),
    )


def _validate_deliberation(
    deliberation: FakeLaboratoryDeliberationResult,
) -> tuple[str, ...]:
    issues: list[str] = []
    if not isinstance(deliberation, FakeLaboratoryDeliberationResult):
        return ("deliberation must be FakeLaboratoryDeliberationResult",)
    if not deliberation.publication_ready:
        issues.append("deliberation must be locally publication-ready")
    if deliberation.final_artifact is None:
        issues.append("deliberation must expose FinalArtifactEnvelope")
    if deliberation.final_packet is None:
        issues.append("deliberation must expose FinalSynthesisPacket")
    if deliberation.github_mutation_performed:
        issues.append("upstream deliberation must not mutate GitHub")
    if deliberation.scheduler_created:
        issues.append("upstream deliberation must not create Scheduler")
    return tuple(issues)


def _build_sql_record(
    deliberation: FakeLaboratoryDeliberationResult,
) -> SqlContextRecord:
    final = deliberation.final_artifact
    assert final is not None
    identity = (
        f"{final.final_ref}\0{final.synthesis_ref}\0"
        f"{deliberation.command.context_generation}"
    )
    return build_sql_context_record(
        kind="specialist_output",
        identity=identity,
        title=final.title,
        body=final.body,
        parent_ref=deliberation.command.orientation.sql_context_ref,
        metadata=(
            ("artifact_ref", final.artifact_ref),
            ("final_ref", final.final_ref),
            ("laboratory_ref", "laboratory:local-fake"),
            (
                "publication_gate_required",
                "true",
            ),
            ("real_backend_used", "false"),
            ("source_candidate_ref", deliberation.command.source_candidate_ref),
            ("synthesis_ref", final.synthesis_ref),
            ("target_ref", final.target_ref),
        ),
    )


def _build_github_preview(
    deliberation: FakeLaboratoryDeliberationResult,
    sql_ref: str,
) -> LaboratoryGitHubPublicationPreview:
    final = deliberation.final_artifact
    assert final is not None
    identity = (
        f"{final.final_ref}\0{sql_ref}\0{final.target_ref}\0{final.body}"
    )
    return LaboratoryGitHubPublicationPreview(
        preview_ref=f"github-preview:laboratory:{_digest(identity)}",
        target_ref=final.target_ref,
        final_ref=final.final_ref,
        synthesis_ref=final.synthesis_ref,
        sql_ref=sql_ref,
        title=final.title,
        body=final.body,
        evidence_refs=final.evidence_refs,
    )


def _build_observation_facts(
    deliberation: FakeLaboratoryDeliberationResult,
    *,
    sql_ref: str,
    vector_state: str,
    qdrant_ref: str = "",
) -> tuple[ClosedResultFrameObservationFact, ...]:
    final = deliberation.final_artifact
    assert final is not None
    base = f"event-fact:0274-r3:{_digest(final.final_ref)}"
    facts = [
        ClosedResultFrameObservationFact(
            fact_ref=f"{base}:deliberation",
            fact_kind="laboratory.deliberation.completed",
            payload={
                "frame_ref": deliberation.command.orientation.orientation_ref,
                "sql_ref": sql_ref,
                "laboratory_ref": "laboratory:local-fake",
                "round_ref": deliberation.round.round_ref,
                "synthesis_ref": final.synthesis_ref,
                "specialist_count": len(deliberation.receipts),
                "publication_ready": deliberation.publication_ready,
            },
        ),
        ClosedResultFrameObservationFact(
            fact_ref=f"{base}:sql",
            fact_kind="laboratory.specialist_output.persisted",
            payload={
                "frame_ref": deliberation.command.orientation.orientation_ref,
                "sql_ref": sql_ref,
                "final_ref": final.final_ref,
                "sql_remains_authority": True,
            },
        ),
        ClosedResultFrameObservationFact(
            fact_ref=f"{base}:vector",
            fact_kind="laboratory.vector_projection.state",
            payload={
                "frame_ref": deliberation.command.orientation.orientation_ref,
                "sql_ref": sql_ref,
                "qdrant_ref": qdrant_ref,
                "vector_state": vector_state,
                "qdrant_projection_only": True,
            },
        ),
        ClosedResultFrameObservationFact(
            fact_ref=f"{base}:github",
            fact_kind="laboratory.github_preview.pending",
            payload={
                "frame_ref": deliberation.command.orientation.orientation_ref,
                "sql_ref": sql_ref,
                "target_ref": final.target_ref,
                "publication_gate_required": True,
                "github_mutation_performed": False,
            },
        ),
    ]
    return tuple(facts)


def _fact_to_event(fact: ClosedResultFrameObservationFact) -> Event:
    return Event(
        type=EventType.LABORATORY_VISIT_RESULT,
        source=OBSERVATION_SOURCE,
        dest=OBSERVATION_DESTINATION,
        payload=fact.to_mapping(),
        priority=0,
        correlation_id=fact.fact_ref,
        request=None,
        metadata=MappingProxyType(
            {
                "schema": LABORATORY_OBSERVATION_SCHEMA,
                "observation_only": True,
                "command": False,
                "fact_kind": fact.fact_kind,
            }
        ),
    )


def _build_passive_visual_models(
    deliberation: FakeLaboratoryDeliberationResult,
    *,
    sql_ref: str,
    facts: Sequence[ClosedResultFrameObservationFact],
    qdrant_ref: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    observation_report = {
        "valid": True,
        "eventbus_observation_only": True,
        "events_are_facts_not_commands": True,
        "executes_runtime": False,
        "starts_postgresql": False,
        "starts_openvino": False,
        "starts_qdrant": False,
        "modifies_scheduler_run": False,
        "facts": [fact.to_mapping() for fact in facts],
    }
    passive = build_passive_supervisor_closed_frame_observation_report(
        observation_report,
        source_observation_ref=(
            "laboratory-observation:"
            + _digest(deliberation.command.orientation.orientation_ref)
        ),
    ).to_mapping()
    snapshot = _build_visual_snapshot(
        deliberation,
        sql_ref=sql_ref,
        qdrant_ref=qdrant_ref,
        fact_count=len(facts),
    )
    visual = build_visual_read_model(
        snapshot,
        layout_kind="laboratory-cellular",
    ).to_dict()
    layout = build_passive_supervisor_visual_layout_model(visual)
    return dict(passive), dict(visual), dict(layout)


def _build_visual_snapshot(
    deliberation: FakeLaboratoryDeliberationResult,
    *,
    sql_ref: str,
    qdrant_ref: str,
    fact_count: int,
) -> dict[str, Any]:
    final = deliberation.final_artifact
    assert final is not None
    cells: list[dict[str, Any]] = [
        {
            "cell_id": "laboratory:local-fake",
            "cell_kind": "LABORATORY",
            "state": "completed",
            "health": "healthy",
            "last_event": "laboratory.deliberation.completed",
            "payload": {
                "laboratory_ref": "laboratory:local-fake",
                "sql_ref": sql_ref,
            },
        }
    ]
    for receipt in deliberation.receipts:
        result = receipt.execution.result
        cells.append(
            {
                "cell_id": result.specialist_ref,
                "cell_kind": "SPECIALIST",
                "state": result.status,
                "health": (
                    "healthy" if result.status == "completed" else "degraded"
                ),
                "last_event": "laboratory.specialist.result",
                "payload": {
                    "laboratory_ref": result.laboratory_ref,
                    "specialist_ref": result.specialist_ref,
                    "visit_ref": result.visit_ref,
                    "sql_ref": sql_ref,
                },
            }
        )
    cells.extend(
        (
            {
                "cell_id": deliberation.round.round_ref,
                "cell_kind": "DELIBERATION",
                "state": deliberation.round.convergence_state,
                "health": "healthy",
                "last_event": "laboratory.round.completed",
                "payload": {
                    "laboratory_ref": "laboratory:local-fake",
                    "sql_ref": sql_ref,
                },
            },
            {
                "cell_id": final.synthesis_ref,
                "cell_kind": "SYNTHESIS",
                "state": "ready",
                "health": "healthy",
                "last_event": "laboratory.synthesis.completed",
                "payload": {
                    "synthesis_ref": final.synthesis_ref,
                    "sql_ref": sql_ref,
                },
            },
            {
                "cell_id": final.final_ref,
                "cell_kind": "FINAL_ARTIFACT",
                "state": "pending_review",
                "health": "healthy",
                "last_event": "laboratory.github_preview.pending",
                "payload": {
                    "artifact_ref": final.artifact_ref,
                    "final_ref": final.final_ref,
                    "sql_ref": sql_ref,
                },
            },
            {
                "cell_id": sql_ref,
                "cell_kind": "SQL_STORE",
                "state": "authoritative",
                "health": "healthy",
                "last_event": "laboratory.specialist_output.persisted",
                "payload": {"sql_ref": sql_ref},
            },
        )
    )
    if qdrant_ref:
        cells.append(
            {
                "cell_id": qdrant_ref,
                "cell_kind": "QDRANT_PROJECTION",
                "state": "projected",
                "health": "healthy",
                "last_event": "laboratory.vector_projection.state",
                "payload": {
                    "qdrant_ref": qdrant_ref,
                    "sql_ref": sql_ref,
                },
            }
        )
    return {
        "generated_at": "",
        "event_count": fact_count,
        "cell_count": len(cells),
        "blocked_count": 0,
        "failed_count": 0,
        "stale_count": 0,
        "cells": cells,
    }


def _public_mapping(value: object | None) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_mapping") and callable(value.to_mapping):
        mapped = value.to_mapping()
        if isinstance(mapped, Mapping):
            return dict(mapped)
    return {}


def _result(
    *,
    issues: Sequence[str],
    command: FakeLaboratoryClosedHandoffCommand,
    sql_record: Mapping[str, Any],
    sql_write: Mapping[str, Any] | None = None,
    sql_readback: Mapping[str, Any] | None = None,
    embedding: Mapping[str, Any] | None = None,
    compatibility: Mapping[str, Any] | None = None,
    projection: Mapping[str, Any] | None = None,
    observation_facts: tuple[Mapping[str, Any], ...] = (),
    published_event_ids: tuple[str, ...] = (),
    passive_supervisor: Mapping[str, Any] | None = None,
    visual_read_model: Mapping[str, Any] | None = None,
    visual_layout: Mapping[str, Any] | None = None,
    github_preview: Mapping[str, Any] | None = None,
    sql_write_performed: bool = False,
    sql_readback_performed: bool = False,
    openvino_call_performed: bool = False,
    qdrant_write_performed: bool = False,
    eventbus_publish_performed: bool = False,
) -> FakeLaboratoryClosedHandoffResult:
    normalized = tuple(dict.fromkeys(str(item) for item in issues if str(item)))
    return FakeLaboratoryClosedHandoffResult(
        valid=not normalized,
        issues=normalized,
        command=command,
        sql_record=dict(sql_record),
        sql_write=dict(sql_write or {}),
        sql_readback=dict(sql_readback or {}),
        embedding=dict(embedding or {}),
        compatibility=dict(compatibility or {}),
        projection=dict(projection or {}),
        observation_facts=observation_facts,
        published_event_ids=published_event_ids,
        passive_supervisor=dict(passive_supervisor or {}),
        visual_read_model=dict(visual_read_model or {}),
        visual_layout=dict(visual_layout or {}),
        github_preview=dict(github_preview or {}),
        sql_write_performed=sql_write_performed,
        sql_readback_performed=sql_readback_performed,
        openvino_call_performed=openvino_call_performed,
        qdrant_write_performed=qdrant_write_performed,
        eventbus_publish_performed=eventbus_publish_performed,
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


__all__ = (
    "FAKE_LABORATORY_CLOSED_HANDOFF_COMMAND_SCHEMA",
    "FAKE_LABORATORY_CLOSED_HANDOFF_RESULT_SCHEMA",
    "FAKE_LABORATORY_CLOSED_HANDOFF_VERSION",
    "LABORATORY_GITHUB_PUBLICATION_PREVIEW_SCHEMA",
    "LABORATORY_OBSERVATION_SCHEMA",
    "FakeLaboratoryClosedHandoffCommand",
    "FakeLaboratoryClosedHandoffError",
    "FakeLaboratoryClosedHandoffResult",
    "LaboratoryGitHubPublicationPreview",
    "run_fake_laboratory_closed_local_handoff",
)
