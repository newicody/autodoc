"""Async binding from the two Scheduler-produced love analyses to live projection.

The existing r12 synthesis module remains the authority for deriving SQL
analysis objects, artifacts, revision membership and provenance relations. This
module reuses those helpers, awaits the already-built OpenVINO/E5 + Qdrant
projector for each specialist analysis and persists only projection metadata
back into SQL.

It creates no Scheduler, laboratory provider, OpenVINO runtime, Qdrant client,
SQL store, event loop, manager, queue or parallel orchestrator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from context.context_revision_sql_authority_0287 import (
    CONTEXT_REVISION_SCHEMA,
    ContextArtifactDescriptor,
    ContextAuthorityObject,
    ContextRevision,
    build_context_revision_ref,
)
from context.love_memory_evidence_liaison_synthesis_0287 import (
    LOVE_ANALYSIS_PROJECTION_RECEIPT_SCHEMA,
    LoveAnalysisProjectionReceipt,
    LoveMemoryEvidenceSynthesisCommand,
    LoveMemoryEvidenceSynthesisError,
    _analysis_object,
    _artifact_descriptor,
    _merge_memberships,
    _put_relations,
    _unique_texts,
    _validate_chain,
)
from context.love_study_contracts_0287 import LOVE_STUDIES_LABORATORY_REF
from context.native_love_laboratory_second_specialist_0287 import (
    build_concept_analysis_artifact,
    concept_analysis_from_visit_result,
)

LOVE_SPECIALIST_LIVE_PROJECTION_BINDING_SCHEMA = (
    "missipy.love.specialist_live_projection_binding.v1"
)


class LoveSpecialistLiveProjectionBindingError(RuntimeError):
    """Raised when the two-analysis live projection boundary diverges."""


@runtime_checkable
class AsyncLoveAnalysisProjectionPort(Protocol):
    """Async subset implemented by the installed live E5/Qdrant projector."""

    async def project(
        self,
        authority_object: ContextAuthorityObject,
        *,
        revision: ContextRevision,
        branch_ref: str,
        project_ref: str,
        conversation_ref: str,
        specialist_ref: str,
        laboratory_ref: str,
        security_scope: str,
        projected_at: str | None = None,
    ) -> LoveAnalysisProjectionReceipt:
        """Project one SQL-authoritative specialist analysis."""


@runtime_checkable
class LoveAnalysisAuthorityStore(Protocol):
    """Narrow durable-authority subset shared by SQLite and DB-API stores."""

    def get_revision(self, revision_ref: str) -> ContextRevision | None: ...
    def put_object(self, authority_object: ContextAuthorityObject) -> Any: ...
    def put_artifact(self, artifact: ContextArtifactDescriptor) -> Any: ...
    def put_revision(self, revision: ContextRevision) -> Any: ...
    def put_relation(self, relation: Any) -> Any: ...
    def put_projection(self, projection: Any) -> Any: ...


@dataclass(frozen=True, slots=True)
class LoveSpecialistLiveProjectionBindingResult:
    """Receipt for two SQL objects and two real named-vector projections."""

    schema: str
    command_ref: str
    analysis_revision: ContextRevision
    authority_objects: tuple[ContextAuthorityObject, ContextAuthorityObject]
    artifact_descriptors: tuple[ContextArtifactDescriptor, ContextArtifactDescriptor]
    projection_receipts: tuple[
        LoveAnalysisProjectionReceipt,
        LoveAnalysisProjectionReceipt,
    ]
    specialist_refs: tuple[str, str]
    sql_write_performed: bool = True
    qdrant_projection_performed: bool = True
    scheduler_created: bool = False
    parallel_orchestrator_created: bool = False
    synthesis_performed: bool = False

    def __post_init__(self) -> None:
        if self.schema != LOVE_SPECIALIST_LIVE_PROJECTION_BINDING_SCHEMA:
            raise LoveSpecialistLiveProjectionBindingError(
                "unsupported live projection binding schema"
            )
        if not self.command_ref.startswith("love-synthesis-command:"):
            raise LoveSpecialistLiveProjectionBindingError(
                "command_ref must remain tied to the existing synthesis command"
            )
        if len(set(self.specialist_refs)) != 2:
            raise LoveSpecialistLiveProjectionBindingError(
                "two distinct specialist identities are required"
            )
        object_refs = tuple(item.object_ref for item in self.authority_objects)
        if len(set(object_refs)) != 2:
            raise LoveSpecialistLiveProjectionBindingError(
                "two distinct SQL authority objects are required"
            )
        active_refs = {
            item.object_ref
            for item in self.analysis_revision.memberships
            if item.state == "active"
        }
        if not set(object_refs).issubset(active_refs):
            raise LoveSpecialistLiveProjectionBindingError(
                "both analyses must be active members of the analysis revision"
            )
        projected_refs = tuple(
            item.projection.source_ref for item in self.projection_receipts
        )
        if projected_refs != object_refs:
            raise LoveSpecialistLiveProjectionBindingError(
                "projection receipts must preserve specialist-object order"
            )
        for authority_object, receipt in zip(
            self.authority_objects,
            self.projection_receipts,
        ):
            if receipt.schema != LOVE_ANALYSIS_PROJECTION_RECEIPT_SCHEMA:
                raise LoveSpecialistLiveProjectionBindingError(
                    "unexpected projection receipt schema"
                )
            if receipt.projection.source_content_digest != authority_object.content_digest:
                raise LoveSpecialistLiveProjectionBindingError(
                    "projection digest differs from SQL authority"
                )
        if not self.sql_write_performed or not self.qdrant_projection_performed:
            raise LoveSpecialistLiveProjectionBindingError(
                "SQL and Qdrant evidence are both required"
            )
        if self.scheduler_created or self.parallel_orchestrator_created:
            raise LoveSpecialistLiveProjectionBindingError(
                "runtime orchestration authority changed"
            )
        if self.synthesis_performed:
            raise LoveSpecialistLiveProjectionBindingError(
                "r12 binding must not perform global synthesis"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "command_ref": self.command_ref,
            "analysis_revision": self.analysis_revision.to_mapping(),
            "authority_objects": [item.to_mapping() for item in self.authority_objects],
            "artifact_descriptors": [
                item.to_mapping() for item in self.artifact_descriptors
            ],
            "projection_receipts": [
                item.to_mapping() for item in self.projection_receipts
            ],
            "specialist_refs": list(self.specialist_refs),
            "boundaries": {
                "two_specialists_projected": True,
                "sql_is_authority": True,
                "qdrant_is_projection_only": True,
                "openvino_e5_awaited": True,
                "scheduler_created": self.scheduler_created,
                "parallel_orchestrator_created": self.parallel_orchestrator_created,
                "synthesis_performed": self.synthesis_performed,
                "github_mutation_performed": False,
            },
        }


async def bind_love_specialist_analyses_live(
    command: LoveMemoryEvidenceSynthesisCommand,
    *,
    authority_store: LoveAnalysisAuthorityStore,
    projection_port: AsyncLoveAnalysisProjectionPort,
) -> LoveSpecialistLiveProjectionBindingResult:
    """Persist and project both completed specialist analyses in stable order."""

    if not isinstance(projection_port, AsyncLoveAnalysisProjectionPort):
        raise LoveSpecialistLiveProjectionBindingError(
            "projection_port must expose async project()"
        )

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

    for authority_object in (first_object, second_object):
        authority_store.put_object(authority_object)
    for artifact in (first_artifact, second_artifact):
        authority_store.put_artifact(artifact)

    memberships = _merge_memberships(
        base_revision.memberships,
        (first_object.object_ref, second_object.object_ref),
        (first_artifact.artifact_ref, second_artifact.artifact_ref),
    )
    analysis_revision_ref = build_context_revision_ref(
        context_ref=base_revision.context_ref,
        parent_revision_refs=(base_revision.revision_ref,),
        memberships=memberships,
        validation_status="accepted",
        significance="material",
    )
    analysis_revision = ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref=analysis_revision_ref,
        context_ref=base_revision.context_ref,
        parent_revision_refs=(base_revision.revision_ref,),
        memberships=memberships,
        validation_status="accepted",
        significance="material",
        evidence_refs=_unique_texts(
            first_analysis.evidence_refs + second_analysis.evidence_refs
        ),
        producer_task_ref=command.collaboration.second_execution.request.objective_ref,
        producer_specialist_ref=second_analysis.specialist_ref,
        producer_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        created_at=command.created_at,
        metadata={
            "study_ref": command.study.study_ref,
            "phase": "0287-r7-r15-r3-r12",
            "live_projection_binding": True,
        },
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

    receipts: list[LoveAnalysisProjectionReceipt] = []
    for authority_object, specialist_ref in (
        (first_object, first_analysis.specialist_ref),
        (second_object, second_analysis.specialist_ref),
    ):
        receipt = await projection_port.project(
            authority_object,
            revision=analysis_revision,
            branch_ref=command.branch_ref,
            project_ref=command.project_ref,
            conversation_ref=command.collaboration.conversation.conversation_ref,
            specialist_ref=specialist_ref,
            laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
            security_scope=command.security_scope,
            projected_at=command.created_at,
        )
        if receipt.projection.source_ref != authority_object.object_ref:
            raise LoveSpecialistLiveProjectionBindingError(
                "projection source_ref mismatch"
            )
        if (
            receipt.projection.source_content_digest
            != authority_object.content_digest
        ):
            raise LoveSpecialistLiveProjectionBindingError(
                "projection digest mismatch"
            )
        authority_store.put_projection(receipt.projection)
        receipts.append(receipt)

    return LoveSpecialistLiveProjectionBindingResult(
        schema=LOVE_SPECIALIST_LIVE_PROJECTION_BINDING_SCHEMA,
        command_ref=command.command_ref,
        analysis_revision=analysis_revision,
        authority_objects=(first_object, second_object),
        artifact_descriptors=(first_artifact, second_artifact),
        projection_receipts=(receipts[0], receipts[1]),
        specialist_refs=(
            first_analysis.specialist_ref,
            second_analysis.specialist_ref,
        ),
    )


__all__ = (
    "LOVE_SPECIALIST_LIVE_PROJECTION_BINDING_SCHEMA",
    "AsyncLoveAnalysisProjectionPort",
    "LoveAnalysisAuthorityStore",
    "LoveSpecialistLiveProjectionBindingError",
    "LoveSpecialistLiveProjectionBindingResult",
    "bind_love_specialist_analyses_live",
)
