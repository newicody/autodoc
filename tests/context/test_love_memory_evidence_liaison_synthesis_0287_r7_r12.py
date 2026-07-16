from __future__ import annotations

import hashlib

import pytest

from context.context_revision_sql_authority_0287 import (
    CONTEXT_AUTHORITY_OBJECT_SCHEMA,
    CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
    CONTEXT_REVISION_SCHEMA,
    VECTOR_PROJECTION_METADATA_SCHEMA,
    ContextAuthorityObject,
    ContextRevision,
    ContextRevisionMembership,
    SQLiteContextRevisionAuthorityStore,
    VectorProjectionMetadata,
)
from context.hybrid_retrieval_sql_rehydration_0287 import (
    DENSE_QUERY_EMBEDDING_SCHEMA,
    HYBRID_CANDIDATE_SCHEMA,
    DenseQueryEmbedding,
    HybridRetrievalCandidate,
)
from context.laboratory_framework_contract_0273 import (
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
)
from context.love_memory_evidence_liaison_synthesis_0287 import (
    LOVE_ANALYSIS_PROJECTION_RECEIPT_SCHEMA,
    LOVE_MEMORY_EVIDENCE_SYNTHESIS_COMMAND_SCHEMA,
    LoveAnalysisProjectionReceipt,
    LoveMemoryEvidenceSynthesisCommand,
    LoveMemoryEvidenceSynthesisError,
    run_love_memory_evidence_liaison_synthesis,
)
from context.love_study_contracts_0287 import (
    LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
    LOVE_STUDIES_LABORATORY_REF,
    LOVE_STUDY_REQUEST_CONTRACT_REF,
    LOVE_STUDY_REQUEST_SCHEMA,
    LoveStudyRequest,
)
from context.native_love_laboratory_second_specialist_0287 import (
    InMemoryCollaborativeLoveLaboratoryInputResolver,
    build_completed_collaboration_record,
    build_native_love_collaborative_provider,
    execute_native_love_collaborative_visit,
    prepare_second_specialist_collaboration,
)
from context.qdrant_canonical_profile_0287 import (
    QDRANT_COLLECTION_PROFILE_SCHEMA,
    QDRANT_NAMED_VECTOR_SCHEMA,
    QdrantCollectionProfile,
    QdrantNamedVectorProfile,
    build_canonical_payload_indexes,
)
from context.specialist_multitask_model_0287 import (
    SPECIALIST_TASK_REQUEST_SCHEMA,
    SpecialistTaskRequest,
)


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _collaboration():
    text = (
        "Je l'aime et nous parlons souvent. "
        "Mais j'ai l'impression de faire toujours plus que lui. "
        "Nous évitons de parler d'engagement."
    )
    study = LoveStudyRequest(
        schema=LOVE_STUDY_REQUEST_SCHEMA,
        study_ref="love-study:r12-1",
        source_issue_ref="github-issue:newicody/projects#41",
        objective="Analyser la relation décrite.",
        subject_text=text,
        constraints=("Ne pas produire de diagnostic psychologique.",),
        success_criteria=("Produire deux analyses attribuées.",),
        context_refs=("context-revision:love-r1",),
    )
    task = SpecialistTaskRequest(
        schema=SPECIALIST_TASK_REQUEST_SCHEMA,
        task_ref="specialist-task:love-first-r12",
        plan_ref="specialist-task-plan:love-r12",
        mission_ref="mission:love-study-r12",
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        task_type_ref="task-type:love.concept_analysis",
        capability="love.concept_analysis",
        objective="Analyser les concepts et affects présents.",
        input_contract_ref=LOVE_STUDY_REQUEST_CONTRACT_REF,
        expected_output_contract_ref=LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
        conversation_ref="laboratory-conversation:love-r12",
        return_route_ref="route:love-r12",
        constraints=(),
        success_criteria=("Fournir des constats et preuves.",),
        context_refs=("ctx:love-r12",),
        idempotency_key="idempotency:love-first-r12",
        metadata={"context_revision_ref": "context-revision:love-r1"},
    )
    visit = LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref="laboratory-visit:love-first-r12",
        laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        objective_ref=task.task_ref,
        source_candidate_ref=study.study_ref,
        context_generation=1,
        input_contract_ref=task.input_contract_ref,
        expected_output_contract_ref=task.expected_output_contract_ref,
        resource_budget=LaboratoryResourceBudget(),
        return_route_ref=task.return_route_ref,
        context_refs=task.context_refs,
        origin_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        target_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        conversation_ref=task.conversation_ref,
    )
    resolver = InMemoryCollaborativeLoveLaboratoryInputResolver(
        studies={study.study_ref: study},
        tasks={task.task_ref: task},
    )
    provider = build_native_love_collaborative_provider(resolver)
    first_execution = execute_native_love_collaborative_visit(visit, provider=provider)
    preparation = prepare_second_specialist_collaboration(
        first_visit=visit,
        first_result=first_execution.result,
        second_task_ref="specialist-task:love-second-r12",
        second_visit_ref="laboratory-visit:love-second-r12",
    )
    resolver.register_concept_analysis(
        preparation.first_analysis,
        preparation.first_artifact,
    )
    resolver.register_task(preparation.second_task)
    second_execution = execute_native_love_collaborative_visit(
        preparation.second_visit,
        provider=provider,
    )
    collaboration = build_completed_collaboration_record(
        preparation=preparation,
        first_execution=first_execution,
        second_execution=second_execution,
        first_scheduler_receipt_ref="scheduler-receipt:r12-first",
        second_scheduler_receipt_ref="scheduler-receipt:r12-second",
    )
    return study, collaboration


def _store() -> SQLiteContextRevisionAuthorityStore:
    store = SQLiteContextRevisionAuthorityStore()
    store.initialize_schema()
    source = ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref="sql:love-source:r12",
        object_kind="research_source",
        content_schema_ref="missipy.love.study_request.v1",
        content_digest=_sha("source-r12"),
        title="Source de l'étude",
        body="source-r12",
        media_type="text/plain",
        byte_count=10,
    )
    store.put_object(source)
    store.put_revision(
        ContextRevision(
            schema=CONTEXT_REVISION_SCHEMA,
            revision_ref="context-revision:love-r1",
            context_ref="context:love-study-r12",
            parent_revision_refs=(),
            memberships=(
                ContextRevisionMembership(
                    schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
                    object_ref=source.object_ref,
                    state="active",
                ),
            ),
            validation_status="accepted",
            significance="material",
            evidence_refs=("ctx:love-r12",),
            created_at="2026-07-16T00:00:00Z",
        )
    )
    return store


def _collection() -> QdrantCollectionProfile:
    dense = QdrantNamedVectorProfile(
        schema=QDRANT_NAMED_VECTOR_SCHEMA,
        vector_name="dense_e5_v1",
        vector_kind="dense",
        embedding_profile_ref="embedding-profile:e5-small-v1",
        model_ref="model:e5-small",
        model_revision="1",
        dimension=384,
        distance="Cosine",
        normalized=True,
    )
    sparse = QdrantNamedVectorProfile(
        schema=QDRANT_NAMED_VECTOR_SCHEMA,
        vector_name="sparse_lexical_v1",
        vector_kind="sparse",
        embedding_profile_ref="embedding-profile:sparse-lexical-v1",
        model_ref="model:sparse-lexical",
        model_revision="1",
        dimension=None,
        distance=None,
        normalized=None,
        hnsw_enabled=False,
    )
    return QdrantCollectionProfile(
        schema=QDRANT_COLLECTION_PROFILE_SCHEMA,
        profile_ref="qdrant-profile:love-r12",
        collection_name="autodoc_context",
        collection_alias="autodoc_context_active",
        point_identity_field="point_id",
        authority_ref_field="sql_ref",
        named_vectors=(dense, sparse),
        payload_indexes=build_canonical_payload_indexes(),
    )


class _ProjectionPort:
    def __init__(self, *, bad_digest: bool = False) -> None:
        self.bad_digest = bad_digest
        self.objects = []

    def project(
        self,
        authority_object,
        *,
        revision,
        branch_ref,
        project_ref,
        conversation_ref,
        specialist_ref,
        laboratory_ref,
    ):
        self.objects.append(authority_object)
        digest = "sha256:" + "0" * 64 if self.bad_digest else authority_object.content_digest
        projection = VectorProjectionMetadata(
            schema=VECTOR_PROJECTION_METADATA_SCHEMA,
            projection_ref="qdrant-projection:" + authority_object.object_ref.split(":")[-1],
            source_ref=authority_object.object_ref,
            source_content_digest=digest,
            embedding_profile_ref="embedding-profile:e5-small-v1",
            model_ref="model:e5-small",
            model_revision="1",
            dimension=384,
            normalized=True,
            vector_name="dense_e5_v1",
            collection_name="autodoc_context",
            point_id="point-" + authority_object.object_ref.split(":")[-1],
            projection_state="active",
            projected_at="2026-07-16T00:00:00Z",
            metadata={
                "branch_ref": branch_ref,
                "project_ref": project_ref,
                "conversation_ref": conversation_ref,
                "specialist_ref": specialist_ref,
                "laboratory_ref": laboratory_ref,
                "context_revision_ref": revision.revision_ref,
            },
        )
        return LoveAnalysisProjectionReceipt(
            schema=LOVE_ANALYSIS_PROJECTION_RECEIPT_SCHEMA,
            projection=projection,
            openvino_e5_used=True,
            qdrant_write_performed=True,
        )


class _Embedder:
    def embed_query(self, query_text, *, query_ref, vector_name):
        assert "relation" in query_text.lower()
        return DenseQueryEmbedding(
            schema=DENSE_QUERY_EMBEDDING_SCHEMA,
            query_ref=query_ref,
            vector_name=vector_name,
            model_ref="model:e5-small",
            model_revision="1",
            backend_ref="openvino:embedding.e5-small",
            values=(1.0,) + (0.0,) * 383,
        )


class _Executor:
    def __init__(self, projection_port: _ProjectionPort, *, omit_second: bool = False):
        self.projection_port = projection_port
        self.omit_second = omit_second

    def _candidate(self, source, item, query, rank):
        metadata = dict(item.metadata)
        payload = {
            "sql_ref": item.object_ref,
            "source_ref": item.object_ref,
            "source_content_digest": item.content_digest,
            "context_revision_ref": query.filter.context_revision_ref,
            "branch_ref": query.filter.branch_ref,
            "project_ref": query.filter.project_ref,
            "conversation_ref": query.filter.conversation_ref,
            "security_scope": query.filter.security_scope,
            "sql_authority_ref": query.filter.sql_authority_ref,
            "artifact_kind": "analysis",
            "contribution_kind": "domain_analysis",
            "specialist_ref": metadata["specialist_ref"],
            "laboratory_ref": metadata["laboratory_ref"],
            "document_ref": item.object_ref,
            "valid": True,
            "superseded_by": "",
        }
        return HybridRetrievalCandidate(
            schema=HYBRID_CANDIDATE_SCHEMA,
            source=source,
            point_id="point-" + item.object_ref.split(":")[-1],
            sql_ref=item.object_ref,
            source_ref=item.object_ref,
            score=1.0 - rank / 10.0,
            payload=payload,
        )

    def _items(self):
        items = self.projection_port.objects
        return items[:1] if self.omit_second else items

    def search_dense(self, embedding, *, query, collection):
        return tuple(
            self._candidate("dense", item, query, rank)
            for rank, item in enumerate(self._items(), 1)
        )

    def search_sparse(self, sparse_query, *, query, collection):
        return tuple(
            self._candidate("sparse", item, query, rank)
            for rank, item in enumerate(reversed(self._items()), 1)
        )


def _command(study, collaboration):
    return LoveMemoryEvidenceSynthesisCommand(
        schema=LOVE_MEMORY_EVIDENCE_SYNTHESIS_COMMAND_SCHEMA,
        command_ref="love-synthesis-command:r12-1",
        study=study,
        collaboration=collaboration,
        base_revision_ref="context-revision:love-r1",
        branch_ref="context-branch:main",
        project_ref="project:newicody-projects",
        security_scope="scope:local",
        target_ref="github:issue:newicody/projects#41",
        artifact_storage_ref="storage:zfs:love-r12-final",
        created_at="2026-07-16T00:00:00Z",
    )


def test_full_memory_recall_and_liaison_synthesis_closes_r12() -> None:
    study, collaboration = _collaboration()
    store = _store()
    projection = _ProjectionPort()
    result = run_love_memory_evidence_liaison_synthesis(
        _command(study, collaboration),
        authority_store=store,
        projection_port=projection,
        collection=_collection(),
        embedder=_Embedder(),
        executor=_Executor(projection),
    )

    assert len(result.retrieval.items) == 2
    assert result.study_result.status == "synthesized"
    assert result.final_packet.synthesis.final_publication_ready is True
    assert result.final_envelope.artifact_ref.startswith("artifact:")
    assert store.get_revision(result.synthesis_revision.revision_ref) == (
        result.synthesis_revision
    )
    assert all(store.get_object(item.object_ref) == item for item in result.authority_objects)


def test_one_laboratory_does_not_claim_multi_laboratory_validation() -> None:
    study, collaboration = _collaboration()
    store = _store()
    projection = _ProjectionPort()
    result = run_love_memory_evidence_liaison_synthesis(
        _command(study, collaboration),
        authority_store=store,
        projection_port=projection,
        collection=_collection(),
        embedder=_Embedder(),
        executor=_Executor(projection),
    )

    assert result.mutualization.distinct_specialist_count == 2
    assert result.mutualization.distinct_laboratory_count == 1
    assert result.mutualization.multi_laboratory_pipeline_eligible is False
    assert result.mutualization.multi_laboratory_aggregation_performed is False
    assert "différée" in result.fragments[-1].body


def test_projection_digest_mismatch_fails_closed() -> None:
    study, collaboration = _collaboration()
    store = _store()
    projection = _ProjectionPort(bad_digest=True)

    with pytest.raises(LoveMemoryEvidenceSynthesisError, match="digest mismatch"):
        run_love_memory_evidence_liaison_synthesis(
            _command(study, collaboration),
            authority_store=store,
            projection_port=projection,
            collection=_collection(),
            embedder=_Embedder(),
            executor=_Executor(projection),
        )


def test_recall_must_rehydrate_both_specialist_analyses() -> None:
    study, collaboration = _collaboration()
    store = _store()
    projection = _ProjectionPort()

    with pytest.raises(LoveMemoryEvidenceSynthesisError, match="both analyses"):
        run_love_memory_evidence_liaison_synthesis(
            _command(study, collaboration),
            authority_store=store,
            projection_port=projection,
            collection=_collection(),
            embedder=_Embedder(),
            executor=_Executor(projection, omit_second=True),
        )


def test_identical_replay_is_idempotent_in_sql() -> None:
    study, collaboration = _collaboration()
    store = _store()
    first_projection = _ProjectionPort()
    first = run_love_memory_evidence_liaison_synthesis(
        _command(study, collaboration),
        authority_store=store,
        projection_port=first_projection,
        collection=_collection(),
        embedder=_Embedder(),
        executor=_Executor(first_projection),
    )
    second_projection = _ProjectionPort()
    second = run_love_memory_evidence_liaison_synthesis(
        _command(study, collaboration),
        authority_store=store,
        projection_port=second_projection,
        collection=_collection(),
        embedder=_Embedder(),
        executor=_Executor(second_projection),
    )

    assert first.analysis_revision.revision_ref == second.analysis_revision.revision_ref
    assert first.synthesis_revision.revision_ref == second.synthesis_revision.revision_ref
    assert first.final_envelope == second.final_envelope


def test_r12_has_no_scheduler_control_proxy_or_github_side_effect() -> None:
    study, collaboration = _collaboration()
    store = _store()
    projection = _ProjectionPort()
    result = run_love_memory_evidence_liaison_synthesis(
        _command(study, collaboration),
        authority_store=store,
        projection_port=projection,
        collection=_collection(),
        embedder=_Embedder(),
        executor=_Executor(projection),
    )
    mapping = result.to_mapping()["boundaries"]

    assert mapping["scheduler_modified"] is False
    assert mapping["control_proxy_modified"] is False
    assert mapping["github_mutation_performed"] is False
    assert mapping["sql_is_authority"] is True
    assert mapping["qdrant_is_projection_only"] is True
