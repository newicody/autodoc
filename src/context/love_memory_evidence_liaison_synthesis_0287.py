"""SQL memory, reference-only recall and liaison synthesis for love studies.

This r12 composition closes the local two-specialist chain without creating a
new Scheduler, inference backend, Qdrant client or synthesis engine.  The two
r11 analyses are persisted as SQL authority objects, projected through an
injected OpenVINO/E5 + Qdrant port, selected through the existing hybrid
retrieval boundary, rehydrated from SQL and normalized through the existing
SpecialistLiaisonSynthesis / FinalSynthesisPacket contracts.

The current prototype has two specialists in one concrete laboratory.  The
multi-laboratory evidence pipeline remains deliberately ineligible until a
second distinct laboratory contributes evidence; local convergence,
contradiction, uncertainty and provenance are preserved instead of falsely
claiming multi-laboratory validation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

from context.context_revision_sql_authority_0287 import (
    CONTEXT_ARTIFACT_DESCRIPTOR_SCHEMA,
    CONTEXT_AUTHORITY_OBJECT_SCHEMA,
    CONTEXT_RELATION_SCHEMA,
    CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
    CONTEXT_REVISION_SCHEMA,
    VECTOR_PROJECTION_METADATA_SCHEMA,
    ContextArtifactDescriptor,
    ContextAuthorityObject,
    ContextRelation,
    ContextRevision,
    ContextRevisionMembership,
    SQLiteContextRevisionAuthorityStore,
    VectorProjectionMetadata,
    build_context_revision_ref,
)
from context.hybrid_retrieval_sql_rehydration_0287 import (
    HYBRID_FILTER_SCHEMA,
    HYBRID_QUERY_SCHEMA,
    HybridRetrievalFilter,
    HybridRetrievalQuery,
    HybridRetrievalResult,
    execute_hybrid_retrieval,
)
from context.love_study_contracts_0287 import (
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
    LOVE_STUDIES_LABORATORY_REF,
    LOVE_STUDY_RESULT_SCHEMA,
    LoveConceptAffectAnalysis,
    LoveRelationalDynamicsAnalysis,
    LoveStudyRequest,
    LoveStudyResult,
)
from context.native_love_laboratory_second_specialist_0287 import (
    NativeLoveCollaborationRecord,
    build_concept_analysis_artifact,
    concept_analysis_from_visit_result,
)
from context.qdrant_canonical_profile_0287 import QdrantCollectionProfile
from context.server_oriented_deliberation_cycle import FinalArtifactEnvelope
from context.specialist_liaison_synthesis import (
    FinalSynthesisPacket,
    SpecialistLiaisonSynthesis,
    SpecialistOutputFragment,
    build_final_synthesis_packet,
    build_specialist_liaison_synthesis,
)

LOVE_MEMORY_EVIDENCE_SYNTHESIS_VERSION = "0287.r7.r12"
LOVE_ANALYSIS_PROJECTION_RECEIPT_SCHEMA = (
    "missipy.love.analysis_projection_receipt.v1"
)
LOVE_EVIDENCE_MUTUALIZATION_SCHEMA = "missipy.love.evidence_mutualization.v1"
LOVE_MEMORY_EVIDENCE_SYNTHESIS_COMMAND_SCHEMA = (
    "missipy.love.memory_evidence_synthesis_command.v1"
)
LOVE_MEMORY_EVIDENCE_SYNTHESIS_RESULT_SCHEMA = (
    "missipy.love.memory_evidence_synthesis_result.v1"
)

_SHA256_PREFIX = "sha256:"


class LoveMemoryEvidenceSynthesisError(RuntimeError):
    """Raised when persistence, recall or synthesis boundaries diverge."""


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(text: str) -> str:
    return _SHA256_PREFIX + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _digest_ref(prefix: str, *parts: str) -> str:
    material = "\0".join(parts)
    return prefix + hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _unique_texts(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.strip() for item in values if item.strip()))


@dataclass(frozen=True, slots=True)
class LoveAnalysisProjectionReceipt:
    """Proof that one SQL authority object was projected through real ports."""

    schema: str
    projection: VectorProjectionMetadata
    openvino_e5_used: bool
    qdrant_write_performed: bool
    qdrant_returns_references_only: bool = True
    sql_remains_authority: bool = True

    def __post_init__(self) -> None:
        if self.schema != LOVE_ANALYSIS_PROJECTION_RECEIPT_SCHEMA:
            raise LoveMemoryEvidenceSynthesisError("unsupported projection receipt schema")
        if self.projection.schema != VECTOR_PROJECTION_METADATA_SCHEMA:
            raise LoveMemoryEvidenceSynthesisError("unexpected projection metadata schema")
        if not self.openvino_e5_used or not self.qdrant_write_performed:
            raise LoveMemoryEvidenceSynthesisError("real E5 projection proof is required")
        if not self.qdrant_returns_references_only or not self.sql_remains_authority:
            raise LoveMemoryEvidenceSynthesisError("projection authority boundaries changed")
        if self.projection.vector_name != "dense_e5_v1":
            raise LoveMemoryEvidenceSynthesisError("love analysis must use dense_e5_v1")
        if self.projection.dimension != 384 or not self.projection.normalized:
            raise LoveMemoryEvidenceSynthesisError("E5 projection must be normalized 384-d")
        if self.projection.projection_state != "active":
            raise LoveMemoryEvidenceSynthesisError("projection must be active")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "projection": self.projection.to_mapping(),
            "openvino_e5_used": self.openvino_e5_used,
            "qdrant_write_performed": self.qdrant_write_performed,
            "qdrant_returns_references_only": self.qdrant_returns_references_only,
            "sql_remains_authority": self.sql_remains_authority,
        }


@runtime_checkable
class LoveAnalysisProjectionPort(Protocol):
    """Injected existing-runtime projection surface; no backend is created here."""

    def project(
        self,
        authority_object: ContextAuthorityObject,
        *,
        revision: ContextRevision,
        branch_ref: str,
        project_ref: str,
        conversation_ref: str,
        specialist_ref: str,
        laboratory_ref: str,
    ) -> LoveAnalysisProjectionReceipt:
        """Project one SQL object and return exact readback metadata."""


@dataclass(frozen=True, slots=True)
class LoveEvidenceMutualization:
    """Local two-specialist evidence comparison before liaison synthesis."""

    schema: str
    mutualization_ref: str
    study_ref: str
    analysis_refs: tuple[str, str]
    convergences: tuple[str, ...]
    contradictions: tuple[str, ...]
    uncertainties: tuple[str, ...]
    recommendations: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    distinct_specialist_count: int = 2
    distinct_laboratory_count: int = 1
    multi_laboratory_pipeline_eligible: bool = False
    multi_laboratory_aggregation_performed: bool = False

    def __post_init__(self) -> None:
        if self.schema != LOVE_EVIDENCE_MUTUALIZATION_SCHEMA:
            raise LoveMemoryEvidenceSynthesisError("unsupported mutualization schema")
        if len(set(self.analysis_refs)) != 2:
            raise LoveMemoryEvidenceSynthesisError("two distinct analyses are required")
        if self.distinct_specialist_count != 2:
            raise LoveMemoryEvidenceSynthesisError("two specialists are required")
        if self.distinct_laboratory_count != 1:
            raise LoveMemoryEvidenceSynthesisError("r12 currently has one laboratory")
        if self.multi_laboratory_pipeline_eligible:
            raise LoveMemoryEvidenceSynthesisError("one laboratory is not multi-laboratory")
        if self.multi_laboratory_aggregation_performed:
            raise LoveMemoryEvidenceSynthesisError("multi-laboratory aggregation is deferred")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "mutualization_ref": self.mutualization_ref,
            "study_ref": self.study_ref,
            "analysis_refs": list(self.analysis_refs),
            "convergences": list(self.convergences),
            "contradictions": list(self.contradictions),
            "uncertainties": list(self.uncertainties),
            "recommendations": list(self.recommendations),
            "evidence_refs": list(self.evidence_refs),
            "distinct_specialist_count": self.distinct_specialist_count,
            "distinct_laboratory_count": self.distinct_laboratory_count,
            "multi_laboratory_pipeline_eligible": self.multi_laboratory_pipeline_eligible,
            "multi_laboratory_aggregation_performed": (
                self.multi_laboratory_aggregation_performed
            ),
        }


@dataclass(frozen=True, slots=True)
class LoveMemoryEvidenceSynthesisCommand:
    """Bounded command for SQL persistence, recall and existing liaison synthesis."""

    schema: str
    command_ref: str
    study: LoveStudyRequest
    collaboration: NativeLoveCollaborationRecord
    base_revision_ref: str
    branch_ref: str
    project_ref: str
    security_scope: str
    target_ref: str
    artifact_storage_ref: str
    created_at: str
    query_text: str = ""

    def __post_init__(self) -> None:
        if self.schema != LOVE_MEMORY_EVIDENCE_SYNTHESIS_COMMAND_SCHEMA:
            raise LoveMemoryEvidenceSynthesisError("unsupported command schema")
        if not self.command_ref.startswith("love-synthesis-command:"):
            raise LoveMemoryEvidenceSynthesisError("command_ref must be typed")
        if not self.base_revision_ref.startswith("context-revision:"):
            raise LoveMemoryEvidenceSynthesisError("base_revision_ref must be typed")
        for name in ("branch_ref", "project_ref", "security_scope", "target_ref"):
            if ":" not in getattr(self, name):
                raise LoveMemoryEvidenceSynthesisError(f"{name} must be typed")
        if not self.artifact_storage_ref.startswith("storage:"):
            raise LoveMemoryEvidenceSynthesisError("artifact_storage_ref must be typed")
        if not self.created_at.strip():
            raise LoveMemoryEvidenceSynthesisError("created_at must be non-empty")
        if self.collaboration.global_synthesis_created:
            raise LoveMemoryEvidenceSynthesisError("collaboration is already synthesized")
        if len(self.collaboration.scheduler_receipt_refs) != 2:
            raise LoveMemoryEvidenceSynthesisError("two Scheduler receipts are required")

    @property
    def effective_query_text(self) -> str:
        return self.query_text.strip() or " ".join(
            (self.study.objective, self.study.subject_text)
        )


@dataclass(frozen=True, slots=True)
class LoveMemoryEvidenceSynthesisResult:
    """Complete local r12 closure with durable provenance and no publication."""

    schema: str
    command_ref: str
    analysis_revision: ContextRevision
    synthesis_revision: ContextRevision
    authority_objects: tuple[ContextAuthorityObject, ...]
    artifact_descriptors: tuple[ContextArtifactDescriptor, ...]
    projection_receipts: tuple[LoveAnalysisProjectionReceipt, ...]
    retrieval: HybridRetrievalResult
    mutualization: LoveEvidenceMutualization
    fragments: tuple[SpecialistOutputFragment, ...]
    synthesis: SpecialistLiaisonSynthesis
    final_packet: FinalSynthesisPacket
    final_envelope: FinalArtifactEnvelope
    study_result: LoveStudyResult
    sql_write_performed: bool = True
    qdrant_projection_performed: bool = True
    scheduler_modified: bool = False
    control_proxy_modified: bool = False
    github_mutation_performed: bool = False

    def __post_init__(self) -> None:
        if self.schema != LOVE_MEMORY_EVIDENCE_SYNTHESIS_RESULT_SCHEMA:
            raise LoveMemoryEvidenceSynthesisError("unsupported result schema")
        if len(self.authority_objects) != 3:
            raise LoveMemoryEvidenceSynthesisError("two analyses and one synthesis object required")
        if len(self.artifact_descriptors) != 3:
            raise LoveMemoryEvidenceSynthesisError("three artifact descriptors required")
        if len(self.projection_receipts) != 2:
            raise LoveMemoryEvidenceSynthesisError("two projection receipts required")
        if set(item.sql_ref for item in self.retrieval.items) != {
            self.authority_objects[0].object_ref,
            self.authority_objects[1].object_ref,
        }:
            raise LoveMemoryEvidenceSynthesisError("hybrid recall must rehydrate both analyses")
        if not self.synthesis.final_publication_ready:
            raise LoveMemoryEvidenceSynthesisError("final packet must mark synthesis ready")
        if self.study_result.status != "synthesized":
            raise LoveMemoryEvidenceSynthesisError("study result must be synthesized")
        if self.scheduler_modified or self.control_proxy_modified:
            raise LoveMemoryEvidenceSynthesisError("runtime authority boundaries changed")
        if self.github_mutation_performed:
            raise LoveMemoryEvidenceSynthesisError("r12 must not publish to GitHub")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "command_ref": self.command_ref,
            "analysis_revision": self.analysis_revision.to_mapping(),
            "synthesis_revision": self.synthesis_revision.to_mapping(),
            "authority_objects": [item.to_mapping() for item in self.authority_objects],
            "artifact_descriptors": [
                item.to_mapping() for item in self.artifact_descriptors
            ],
            "projection_receipts": [item.to_mapping() for item in self.projection_receipts],
            "retrieval": self.retrieval.to_mapping(),
            "mutualization": self.mutualization.to_mapping(),
            "fragments": [item.to_mapping() for item in self.fragments],
            "synthesis": self.synthesis.to_mapping(),
            "final_packet": self.final_packet.to_mapping(),
            "final_envelope": self.final_envelope.to_mapping(),
            "study_result": self.study_result.to_mapping(),
            "boundaries": {
                "sql_is_authority": True,
                "qdrant_is_projection_only": True,
                "openvino_e5_reused": True,
                "multi_laboratory_pipeline_deferred": True,
                "scheduler_modified": self.scheduler_modified,
                "control_proxy_modified": self.control_proxy_modified,
                "github_mutation_performed": self.github_mutation_performed,
            },
        }


def run_love_memory_evidence_liaison_synthesis(
    command: LoveMemoryEvidenceSynthesisCommand,
    *,
    authority_store: SQLiteContextRevisionAuthorityStore,
    projection_port: LoveAnalysisProjectionPort,
    collection: QdrantCollectionProfile,
    embedder: Any,
    executor: Any,
) -> LoveMemoryEvidenceSynthesisResult:
    """Persist, project, recall and synthesize the completed r11 collaboration."""

    first_analysis = concept_analysis_from_visit_result(
        command.collaboration.first_execution.result
    )
    second_analysis = command.collaboration.second_analysis
    _validate_chain(command, first_analysis, second_analysis)
    base_revision = authority_store.get_revision(command.base_revision_ref)
    if base_revision is None:
        raise LoveMemoryEvidenceSynthesisError("base context revision is absent")

    first_object = _analysis_object(first_analysis, "Concepts et affects")
    second_object = _analysis_object(second_analysis, "Dynamiques relationnelles")
    first_artifact = _artifact_descriptor(
        build_concept_analysis_artifact(
            first_analysis,
            producer_visit_ref=command.collaboration.first_execution.request.visit_ref,
        ),
        created_at=command.created_at,
    )
    second_artifact = _artifact_descriptor(
        command.collaboration.second_artifact,
        created_at=command.created_at,
    )
    authority_store.put_object(first_object)
    authority_store.put_object(second_object)
    authority_store.put_artifact(first_artifact)
    authority_store.put_artifact(second_artifact)

    analysis_memberships = _merge_memberships(
        base_revision.memberships,
        (first_object.object_ref, second_object.object_ref),
        (first_artifact.artifact_ref, second_artifact.artifact_ref),
    )
    analysis_revision_ref = build_context_revision_ref(
        context_ref=base_revision.context_ref,
        parent_revision_refs=(base_revision.revision_ref,),
        memberships=analysis_memberships,
        validation_status="accepted",
        significance="material",
    )
    analysis_revision = ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref=analysis_revision_ref,
        context_ref=base_revision.context_ref,
        parent_revision_refs=(base_revision.revision_ref,),
        memberships=analysis_memberships,
        validation_status="accepted",
        significance="material",
        evidence_refs=_unique_texts(
            first_analysis.evidence_refs + second_analysis.evidence_refs
        ),
        producer_task_ref=command.collaboration.second_execution.request.objective_ref,
        producer_specialist_ref=second_analysis.specialist_ref,
        producer_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        created_at=command.created_at,
        metadata={"study_ref": command.study.study_ref, "phase": "0287-r7-r12"},
    )
    authority_store.put_revision(analysis_revision)
    _put_relations(
        authority_store,
        command=command,
        revision=analysis_revision,
        first_object=first_object,
        second_object=second_object,
        first_artifact=first_artifact,
        second_artifact=second_artifact,
    )

    projection_receipts = tuple(
        projection_port.project(
            item,
            revision=analysis_revision,
            branch_ref=command.branch_ref,
            project_ref=command.project_ref,
            conversation_ref=command.collaboration.conversation.conversation_ref,
            specialist_ref=specialist_ref,
            laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        )
        for item, specialist_ref in (
            (first_object, first_analysis.specialist_ref),
            (second_object, second_analysis.specialist_ref),
        )
    )
    for item, receipt in zip((first_object, second_object), projection_receipts):
        if receipt.projection.source_ref != item.object_ref:
            raise LoveMemoryEvidenceSynthesisError("projection source_ref mismatch")
        if receipt.projection.source_content_digest != item.content_digest:
            raise LoveMemoryEvidenceSynthesisError("projection digest mismatch")
        authority_store.put_projection(receipt.projection)

    retrieval_filter = HybridRetrievalFilter(
        schema=HYBRID_FILTER_SCHEMA,
        context_revision_ref=analysis_revision.revision_ref,
        branch_ref=command.branch_ref,
        project_ref=command.project_ref,
        security_scope=command.security_scope,
        conversation_ref=command.collaboration.conversation.conversation_ref,
        laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        sql_authority_ref="sql-authority:context-revision",
        contribution_kinds=("domain_analysis",),
    )
    retrieval_query = HybridRetrievalQuery(
        schema=HYBRID_QUERY_SCHEMA,
        query_ref=_digest_ref("retrieval-query:", command.command_ref),
        task_ref=command.collaboration.second_execution.request.objective_ref,
        query_text=command.effective_query_text,
        filter=retrieval_filter,
        final_limit=2,
        group_by="source_ref",
    )
    retrieval = execute_hybrid_retrieval(
        retrieval_query,
        collection=collection,
        embedder=embedder,
        executor=executor,
        authority_store=authority_store,
    )
    expected_refs = {first_object.object_ref, second_object.object_ref}
    if {item.sql_ref for item in retrieval.items} != expected_refs:
        raise LoveMemoryEvidenceSynthesisError("hybrid recall did not rehydrate both analyses")

    mutualization = _mutualize(first_analysis, second_analysis)
    fragments = _build_fragments(
        first_analysis,
        second_analysis,
        mutualization,
        first_object=first_object,
        second_object=second_object,
        first_artifact=first_artifact,
        second_artifact=second_artifact,
    )
    synthesis = build_specialist_liaison_synthesis(
        request_ref=command.study.study_ref,
        title="Étude mutualisée de la relation",
        fragments=fragments,
    )
    final_packet = build_final_synthesis_packet(
        synthesis=synthesis,
        target_ref=command.target_ref,
        mark_ready=True,
    )
    final_artifact = _final_artifact_descriptor(
        final_packet,
        storage_ref=command.artifact_storage_ref,
        created_at=command.created_at,
    )
    synthesis_object = _synthesis_object(final_packet)
    authority_store.put_object(synthesis_object)
    authority_store.put_artifact(final_artifact)

    synthesis_memberships = _merge_memberships(
        analysis_revision.memberships,
        (synthesis_object.object_ref,),
        (final_artifact.artifact_ref,),
    )
    synthesis_revision_ref = build_context_revision_ref(
        context_ref=analysis_revision.context_ref,
        parent_revision_refs=(analysis_revision.revision_ref,),
        memberships=synthesis_memberships,
        validation_status="accepted",
        significance="material",
    )
    synthesis_revision = ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref=synthesis_revision_ref,
        context_ref=analysis_revision.context_ref,
        parent_revision_refs=(analysis_revision.revision_ref,),
        memberships=synthesis_memberships,
        validation_status="accepted",
        significance="material",
        evidence_refs=final_packet.evidence_refs,
        producer_task_ref=command.collaboration.second_execution.request.objective_ref,
        producer_specialist_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        producer_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        created_at=command.created_at,
        metadata={"liaison_synthesis_ref": synthesis.synthesis_ref},
    )
    authority_store.put_revision(synthesis_revision)

    final_envelope = FinalArtifactEnvelope(
        final_ref=_digest_ref("artifact-final:", final_packet.packet_ref),
        target_ref=command.target_ref,
        artifact_ref=final_artifact.artifact_ref,
        synthesis_ref=synthesis.synthesis_ref,
        title=final_packet.title,
        body=final_packet.body,
        evidence_refs=final_packet.evidence_refs,
        context_influence_refs=final_packet.context_influence_refs,
        validation_refs=final_packet.validation_refs,
    )
    liaison_alias = _digest_ref(
        "specialist-liaison-synthesis:", synthesis.synthesis_ref
    )
    study_result = LoveStudyResult(
        schema=LOVE_STUDY_RESULT_SCHEMA,
        result_ref=_digest_ref("love-study-result:", final_artifact.content_digest),
        study_ref=command.study.study_ref,
        status="synthesized",
        context_revision_ref=synthesis_revision.revision_ref,
        concept_affect_analysis_ref=first_analysis.analysis_ref,
        relational_dynamics_analysis_ref=second_analysis.analysis_ref,
        unresolved_points=mutualization.uncertainties,
        liaison_synthesis_ref=liaison_alias,
        final_artifact_ref=final_artifact.artifact_ref,
    )
    return LoveMemoryEvidenceSynthesisResult(
        schema=LOVE_MEMORY_EVIDENCE_SYNTHESIS_RESULT_SCHEMA,
        command_ref=command.command_ref,
        analysis_revision=analysis_revision,
        synthesis_revision=synthesis_revision,
        authority_objects=(first_object, second_object, synthesis_object),
        artifact_descriptors=(first_artifact, second_artifact, final_artifact),
        projection_receipts=projection_receipts,
        retrieval=retrieval,
        mutualization=mutualization,
        fragments=fragments,
        synthesis=final_packet.synthesis,
        final_packet=final_packet,
        final_envelope=final_envelope,
        study_result=study_result,
    )


def _validate_chain(
    command: LoveMemoryEvidenceSynthesisCommand,
    first: LoveConceptAffectAnalysis,
    second: LoveRelationalDynamicsAnalysis,
) -> None:
    if first.study_ref != command.study.study_ref or second.study_ref != command.study.study_ref:
        raise LoveMemoryEvidenceSynthesisError("analysis study_ref mismatch")
    if first.context_revision_ref != command.base_revision_ref:
        raise LoveMemoryEvidenceSynthesisError("first analysis context revision mismatch")
    if second.context_revision_ref != command.base_revision_ref:
        raise LoveMemoryEvidenceSynthesisError("second analysis context revision mismatch")
    if first.specialist_ref != LOVE_CONCEPT_AFFECT_SPECIALIST_REF:
        raise LoveMemoryEvidenceSynthesisError("unexpected first specialist")
    if second.specialist_ref != LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF:
        raise LoveMemoryEvidenceSynthesisError("unexpected second specialist")
    if second.source_analysis_refs != (first.analysis_ref,):
        raise LoveMemoryEvidenceSynthesisError("second analysis provenance mismatch")
    if command.collaboration.conversation.closed is not True:
        raise LoveMemoryEvidenceSynthesisError("specialist conversation must be closed")


def _analysis_object(
    analysis: LoveConceptAffectAnalysis | LoveRelationalDynamicsAnalysis,
    title: str,
) -> ContextAuthorityObject:
    body = _canonical_json(analysis.to_mapping())
    return ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref=_digest_ref("sql:love-analysis:", analysis.analysis_ref),
        object_kind="specialist_analysis",
        content_schema_ref=analysis.schema,
        content_digest=_sha256_text(body),
        title=title,
        body=body,
        media_type="application/json",
        byte_count=len(body.encode("utf-8")),
        metadata={
            "analysis_ref": analysis.analysis_ref,
            "study_ref": analysis.study_ref,
            "specialist_ref": analysis.specialist_ref,
            "laboratory_ref": LOVE_STUDIES_LABORATORY_REF,
            "contribution_kind": analysis.contribution_kind,
        },
    )


def _artifact_descriptor(artifact: Any, *, created_at: str) -> ContextArtifactDescriptor:
    return ContextArtifactDescriptor(
        schema=CONTEXT_ARTIFACT_DESCRIPTOR_SCHEMA,
        artifact_ref=artifact.artifact_ref,
        content_schema_ref=artifact.artifact_schema,
        content_digest=_SHA256_PREFIX + artifact.content_sha256,
        storage_ref=artifact.storage_ref,
        media_type=artifact.media_type,
        byte_count=artifact.byte_count,
        producer_specialist_ref=artifact.producer_ref,
        producer_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        created_at=created_at,
        metadata={"producer_visit_ref": artifact.producer_visit_ref},
    )


def _merge_memberships(
    existing: Sequence[ContextRevisionMembership],
    object_refs: Sequence[str],
    artifact_refs: Sequence[str],
) -> tuple[ContextRevisionMembership, ...]:
    by_ref = {item.object_ref: item for item in existing}
    for ref in tuple(object_refs) + tuple(artifact_refs):
        by_ref[ref] = ContextRevisionMembership(
            schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
            object_ref=ref,
            state="active",
        )
    return tuple(by_ref[key] for key in sorted(by_ref))


def _put_relations(
    store: SQLiteContextRevisionAuthorityStore,
    *,
    command: LoveMemoryEvidenceSynthesisCommand,
    revision: ContextRevision,
    first_object: ContextAuthorityObject,
    second_object: ContextAuthorityObject,
    first_artifact: ContextArtifactDescriptor,
    second_artifact: ContextArtifactDescriptor,
) -> None:
    relations = (
        (command.study.study_ref, first_object.object_ref, "produces"),
        (first_object.object_ref, second_object.object_ref, "influences"),
        (first_object.object_ref, first_artifact.artifact_ref, "materializes"),
        (second_object.object_ref, second_artifact.artifact_ref, "materializes"),
    )
    for source_ref, target_ref, kind in relations:
        relation = ContextRelation(
            schema=CONTEXT_RELATION_SCHEMA,
            relation_ref=_digest_ref("context-relation:", source_ref, target_ref, kind),
            source_ref=source_ref,
            target_ref=target_ref,
            relation_kind=kind,
            context_revision_ref=revision.revision_ref,
            evidence_refs=(),
        )
        store.put_relation(relation)


def _mutualize(
    first: LoveConceptAffectAnalysis,
    second: LoveRelationalDynamicsAnalysis,
) -> LoveEvidenceMutualization:
    first_dimensions = set(first.concepts) | set(first.affects)
    second_dimensions = set(second.dynamics)
    convergences = tuple(sorted(first_dimensions.intersection(second_dimensions)))
    contradictions = _unique_texts(first.contradictions + second.contradictions)
    uncertainties = _unique_texts(first.uncertainties + second.uncertainties)
    recommendations = _unique_texts(first.recommendations + second.recommendations)
    evidence_refs = _unique_texts(first.evidence_refs + second.evidence_refs)
    ref = _digest_ref(
        "love-evidence-mutualization:", first.analysis_ref, second.analysis_ref
    )
    return LoveEvidenceMutualization(
        schema=LOVE_EVIDENCE_MUTUALIZATION_SCHEMA,
        mutualization_ref=ref,
        study_ref=first.study_ref,
        analysis_refs=(first.analysis_ref, second.analysis_ref),
        convergences=convergences,
        contradictions=contradictions,
        uncertainties=uncertainties,
        recommendations=recommendations,
        evidence_refs=evidence_refs,
    )


def _analysis_body(
    heading: str,
    findings: Sequence[Any],
    uncertainties: Sequence[str],
    contradictions: Sequence[str],
    recommendations: Sequence[str],
) -> str:
    lines = [heading]
    lines.extend(f"- {item.statement}" for item in findings)
    if contradictions:
        lines.append("\nContradictions :")
        lines.extend(f"- {item}" for item in contradictions)
    if uncertainties:
        lines.append("\nIncertitudes :")
        lines.extend(f"- {item}" for item in uncertainties)
    if recommendations:
        lines.append("\nRecommandations :")
        lines.extend(f"- {item}" for item in recommendations)
    return "\n".join(lines)


def _build_fragments(
    first: LoveConceptAffectAnalysis,
    second: LoveRelationalDynamicsAnalysis,
    mutualization: LoveEvidenceMutualization,
    *,
    first_object: ContextAuthorityObject,
    second_object: ContextAuthorityObject,
    first_artifact: ContextArtifactDescriptor,
    second_artifact: ContextArtifactDescriptor,
) -> tuple[SpecialistOutputFragment, ...]:
    first_fragment = SpecialistOutputFragment(
        fragment_ref=_digest_ref("specialist-fragment:", first.analysis_ref),
        result_ref="specialist:" + first.specialist_ref.removeprefix("specialist:"),
        output_kind="domain_analysis",
        title="Analyse des concepts et affects",
        body=_analysis_body(
            "Constats du premier spécialiste :",
            first.findings,
            first.uncertainties,
            first.contradictions,
            first.recommendations,
        ),
        evidence_refs=first.evidence_refs,
        context_delta_refs=(first_object.object_ref,),
        validation_refs=(first_artifact.artifact_ref,),
        payload_ref=first_object.object_ref,
        depth="deep",
    )
    second_fragment = SpecialistOutputFragment(
        fragment_ref=_digest_ref("specialist-fragment:", second.analysis_ref),
        result_ref="specialist:" + second.specialist_ref.removeprefix("specialist:"),
        output_kind="domain_analysis",
        title="Analyse des dynamiques relationnelles",
        body=_analysis_body(
            "Constats du second spécialiste :",
            second.findings,
            second.uncertainties,
            second.contradictions,
            second.recommendations,
        ),
        evidence_refs=second.evidence_refs,
        context_delta_refs=(second_object.object_ref,),
        validation_refs=(second_artifact.artifact_ref,),
        payload_ref=second_object.object_ref,
        depth="deep",
    )
    mutual_body = "\n".join(
        (
            "Mutualisation locale des deux analyses.",
            "Convergences : " + (", ".join(mutualization.convergences) or "aucune explicite"),
            "Contradictions : " + (
                "; ".join(mutualization.contradictions) or "aucune explicite"
            ),
            "Incertitudes : " + (
                "; ".join(mutualization.uncertainties) or "aucune explicite"
            ),
            "La validation multi-laboratoires est différée : un seul laboratoire a contribué.",
        )
    )
    mutual_fragment = SpecialistOutputFragment(
        fragment_ref=_digest_ref(
            "specialist-fragment:", mutualization.mutualization_ref
        ),
        result_ref="ctx-result:love-evidence-mutualization",
        output_kind="evidence_mutualization",
        title="Mutualisation et limites",
        body=mutual_body,
        evidence_refs=mutualization.evidence_refs,
        context_delta_refs=(first_object.object_ref, second_object.object_ref),
        validation_refs=(first_artifact.artifact_ref, second_artifact.artifact_ref),
        payload_ref=mutualization.mutualization_ref,
        depth="audit",
    )
    return (first_fragment, second_fragment, mutual_fragment)


def _synthesis_object(packet: FinalSynthesisPacket) -> ContextAuthorityObject:
    body = packet.body
    return ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref=_digest_ref("sql:love-synthesis:", packet.packet_ref),
        object_kind="liaison_synthesis",
        content_schema_ref="missipy.specialist.final_synthesis_packet.v1",
        content_digest=_sha256_text(body),
        title=packet.title,
        body=body,
        media_type="text/markdown",
        byte_count=len(body.encode("utf-8")),
        metadata={"synthesis_ref": packet.synthesis.synthesis_ref},
    )


def _final_artifact_descriptor(
    packet: FinalSynthesisPacket,
    *,
    storage_ref: str,
    created_at: str,
) -> ContextArtifactDescriptor:
    digest = _sha256_text(packet.body)
    return ContextArtifactDescriptor(
        schema=CONTEXT_ARTIFACT_DESCRIPTOR_SCHEMA,
        artifact_ref=_digest_ref("artifact:love-study-final:", digest),
        content_schema_ref="missipy.love.study_deliverable.v1",
        content_digest=digest,
        storage_ref=storage_ref,
        media_type="text/markdown",
        byte_count=len(packet.body.encode("utf-8")),
        producer_task_ref=None,
        producer_specialist_ref=None,
        producer_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        created_at=created_at,
        metadata={"packet_ref": packet.packet_ref},
    )


__all__ = (
    "LOVE_ANALYSIS_PROJECTION_RECEIPT_SCHEMA",
    "LOVE_EVIDENCE_MUTUALIZATION_SCHEMA",
    "LOVE_MEMORY_EVIDENCE_SYNTHESIS_COMMAND_SCHEMA",
    "LOVE_MEMORY_EVIDENCE_SYNTHESIS_RESULT_SCHEMA",
    "LOVE_MEMORY_EVIDENCE_SYNTHESIS_VERSION",
    "LoveAnalysisProjectionPort",
    "LoveAnalysisProjectionReceipt",
    "LoveEvidenceMutualization",
    "LoveMemoryEvidenceSynthesisCommand",
    "LoveMemoryEvidenceSynthesisError",
    "LoveMemoryEvidenceSynthesisResult",
    "run_love_memory_evidence_liaison_synthesis",
)
