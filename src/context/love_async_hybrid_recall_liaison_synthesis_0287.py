"""Async hybrid recall and liaison synthesis after the r12 live binding.

The two specialist analyses are already SQL-authoritative and already projected
when this unit starts. The function below performs no projection. It awaits the
existing E5 ``query:`` adapter through the existing async hybrid retrieval
entry point, verifies that both SQL references were rehydrated and delegates
mutualization/final synthesis to the shared existing finalizer.

It creates no Scheduler, laboratory, OpenVINO runtime, Qdrant client, SQL store,
event loop, task, queue or publication side effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from context.hybrid_retrieval_sql_rehydration_0287 import (
    HYBRID_FILTER_SCHEMA,
    HYBRID_QUERY_SCHEMA,
    HybridRetrievalFilter,
    HybridRetrievalQuery,
)
from context.love_async_hybrid_retrieval_execution_0287 import (
    AsyncDenseQueryEmbedder,
    LoveAsyncHybridRetrievalExecutionResult,
    execute_love_async_hybrid_retrieval,
)
from context.love_memory_evidence_liaison_synthesis_0287 import (
    LOVE_MEMORY_EVIDENCE_SYNTHESIS_RESULT_SCHEMA,
    LoveMemoryEvidenceSynthesisCommand,
    LoveMemoryEvidenceSynthesisError,
    LoveMemoryEvidenceSynthesisResult,
    _digest_ref,
    _validate_chain,
    finalize_love_memory_evidence_liaison_synthesis,
)
from context.love_specialist_live_projection_binding_0287 import (
    LoveSpecialistLiveProjectionBindingResult,
)
from context.love_study_contracts_0287 import LOVE_STUDIES_LABORATORY_REF
from context.native_love_laboratory_second_specialist_0287 import (
    concept_analysis_from_visit_result,
)
from context.qdrant_canonical_profile_0287 import QdrantCollectionProfile

LOVE_ASYNC_HYBRID_RECALL_LIAISON_SYNTHESIS_SCHEMA = (
    "missipy.love.async_hybrid_recall_liaison_synthesis.v1"
)


class LoveAsyncHybridRecallLiaisonSynthesisError(RuntimeError):
    """Raised when the live recall/synthesis continuation diverges."""


class AsyncHybridExecutor(Protocol):
    """Marker for the injected existing Qdrant hybrid-query port."""

    def search_dense(self, *args: Any, **kwargs: Any) -> Any: ...
    def search_sparse(self, *args: Any, **kwargs: Any) -> Any: ...


class LoveSynthesisAuthorityStore(Protocol):
    """Narrow SQL authority surface used by retrieval and final persistence."""

    def get_object(self, object_ref: str) -> Any: ...
    def get_artifact(self, artifact_ref: str) -> Any: ...
    def get_revision(self, revision_ref: str) -> Any: ...
    def put_object(self, value: Any) -> Any: ...
    def put_artifact(self, value: Any) -> Any: ...
    def put_revision(self, value: Any) -> Any: ...


@dataclass(frozen=True, slots=True)
class LoveAsyncHybridRecallLiaisonSynthesisResult:
    """Final synthesis plus evidence that async query recall was used."""

    schema: str
    binding: LoveSpecialistLiveProjectionBindingResult
    retrieval_execution: LoveAsyncHybridRetrievalExecutionResult
    synthesis: LoveMemoryEvidenceSynthesisResult
    analysis_reprojected: bool = False
    scheduler_created: bool = False
    publication_performed: bool = False

    def __post_init__(self) -> None:
        if self.schema != LOVE_ASYNC_HYBRID_RECALL_LIAISON_SYNTHESIS_SCHEMA:
            raise LoveAsyncHybridRecallLiaisonSynthesisError(
                "unsupported async recall/synthesis schema"
            )
        if self.synthesis.schema != LOVE_MEMORY_EVIDENCE_SYNTHESIS_RESULT_SCHEMA:
            raise LoveAsyncHybridRecallLiaisonSynthesisError(
                "unexpected final synthesis result schema"
            )
        if self.binding.command_ref != self.synthesis.command_ref:
            raise LoveAsyncHybridRecallLiaisonSynthesisError(
                "binding and synthesis command references differ"
            )
        if (
            self.binding.analysis_revision.revision_ref
            != self.synthesis.analysis_revision.revision_ref
        ):
            raise LoveAsyncHybridRecallLiaisonSynthesisError(
                "analysis revision changed during recall"
            )
        if self.synthesis.projection_receipts != self.binding.projection_receipts:
            raise LoveAsyncHybridRecallLiaisonSynthesisError(
                "existing projection receipts were not preserved"
            )
        if self.synthesis.retrieval != self.retrieval_execution.retrieval:
            raise LoveAsyncHybridRecallLiaisonSynthesisError(
                "synthesis did not use the async retrieval result"
            )
        if self.analysis_reprojected:
            raise LoveAsyncHybridRecallLiaisonSynthesisError(
                "r13 must not project analyses a second time"
            )
        if self.scheduler_created or self.publication_performed:
            raise LoveAsyncHybridRecallLiaisonSynthesisError(
                "runtime or publication authority changed"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "binding": self.binding.to_mapping(),
            "retrieval_execution": self.retrieval_execution.to_mapping(),
            "synthesis": self.synthesis.to_mapping(),
            "boundaries": {
                "existing_r12_binding_reused": True,
                "analysis_reprojected": self.analysis_reprojected,
                "async_query_embedding_awaited": True,
                "hybrid_dense_sparse_recall": True,
                "sql_rehydration_required": True,
                "scheduler_created": self.scheduler_created,
                "publication_performed": self.publication_performed,
            },
        }


async def run_love_async_hybrid_recall_liaison_synthesis(
    command: LoveMemoryEvidenceSynthesisCommand,
    *,
    binding: LoveSpecialistLiveProjectionBindingResult,
    collection: QdrantCollectionProfile,
    embedder: AsyncDenseQueryEmbedder,
    executor: AsyncHybridExecutor,
    authority_store: LoveSynthesisAuthorityStore,
) -> LoveAsyncHybridRecallLiaisonSynthesisResult:
    """Recall both projected analyses and finalize the liaison synthesis."""

    if binding.command_ref != command.command_ref:
        raise LoveAsyncHybridRecallLiaisonSynthesisError(
            "binding belongs to another synthesis command"
        )
    if binding.synthesis_performed:
        raise LoveAsyncHybridRecallLiaisonSynthesisError(
            "binding already claims global synthesis"
        )

    first_analysis = concept_analysis_from_visit_result(
        command.collaboration.first_execution.result
    )
    second_analysis = command.collaboration.second_analysis
    _validate_chain(command, first_analysis, second_analysis)

    first_object, second_object = binding.authority_objects
    first_artifact, second_artifact = binding.artifact_descriptors
    retrieval_filter = HybridRetrievalFilter(
        schema=HYBRID_FILTER_SCHEMA,
        context_revision_ref=binding.analysis_revision.revision_ref,
        branch_ref=command.branch_ref,
        project_ref=command.project_ref,
        security_scope=command.security_scope,
        conversation_ref=command.collaboration.conversation.conversation_ref,
        laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        artifact_kinds=("specialist_analysis",),
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
    retrieval_execution = await execute_love_async_hybrid_retrieval(
        retrieval_query,
        collection=collection,
        embedder=embedder,
        executor=executor,
        authority_store=authority_store,
    )
    expected_refs = {first_object.object_ref, second_object.object_ref}
    recalled_refs = {item.sql_ref for item in retrieval_execution.retrieval.items}
    if recalled_refs != expected_refs:
        raise LoveMemoryEvidenceSynthesisError(
            "async hybrid recall did not rehydrate both specialist analyses"
        )

    synthesis = finalize_love_memory_evidence_liaison_synthesis(
        command,
        authority_store=authority_store,
        first_analysis=first_analysis,
        second_analysis=second_analysis,
        analysis_revision=binding.analysis_revision,
        first_object=first_object,
        second_object=second_object,
        first_artifact=first_artifact,
        second_artifact=second_artifact,
        projection_receipts=binding.projection_receipts,
        retrieval=retrieval_execution.retrieval,
    )
    return LoveAsyncHybridRecallLiaisonSynthesisResult(
        schema=LOVE_ASYNC_HYBRID_RECALL_LIAISON_SYNTHESIS_SCHEMA,
        binding=binding,
        retrieval_execution=retrieval_execution,
        synthesis=synthesis,
    )


__all__ = (
    "LOVE_ASYNC_HYBRID_RECALL_LIAISON_SYNTHESIS_SCHEMA",
    "AsyncHybridExecutor",
    "LoveAsyncHybridRecallLiaisonSynthesisError",
    "LoveAsyncHybridRecallLiaisonSynthesisResult",
    "LoveSynthesisAuthorityStore",
    "run_love_async_hybrid_recall_liaison_synthesis",
)
