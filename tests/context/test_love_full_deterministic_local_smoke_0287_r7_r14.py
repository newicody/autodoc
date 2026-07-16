from __future__ import annotations

import asyncio
import hashlib
from typing import Any

import pytest

from contracts.event import Event, EventType
from contracts.scheduler import SchedulerContract
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
from context.github_dual_artifact_contract_0275 import (
    GitHubAuthoritativeRequestArtifact,
    GitHubCopilotFirstOpinionAdvisoryArtifact,
    build_dual_artifact_manifest,
    canonical_json_bytes,
)
from context.github_dual_artifact_run_assembly_0281 import (
    GitHubDualArtifactRunMember,
)
from context.hybrid_retrieval_sql_rehydration_0287 import (
    DENSE_QUERY_EMBEDDING_SCHEMA,
    HYBRID_CANDIDATE_SCHEMA,
    DenseQueryEmbedding,
    HybridRetrievalCandidate,
)
from context.love_full_deterministic_local_smoke_0287 import (
    LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_COMMAND_SCHEMA,
    LoveFullDeterministicLocalSmokeCommand,
    LoveFullDeterministicLocalSmokeError,
    run_love_full_deterministic_local_smoke,
)
from context.love_memory_evidence_liaison_synthesis_0287 import (
    LOVE_ANALYSIS_PROJECTION_RECEIPT_SCHEMA,
    LoveAnalysisProjectionReceipt,
)
from context.qdrant_canonical_profile_0287 import (
    QDRANT_COLLECTION_PROFILE_SCHEMA,
    QDRANT_NAMED_VECTOR_SCHEMA,
    QdrantCollectionProfile,
    QdrantNamedVectorProfile,
    build_canonical_payload_indexes,
)
from context.source_candidate import SourceCandidateDecision


class _Dispatcher:
    def __init__(self) -> None:
        self.handlers: dict[EventType, Any] = {}

    def register(self, event_type: EventType, handler: object) -> None:
        self.handlers[event_type] = handler


class _Scheduler(SchedulerContract):
    def __init__(self, dispatcher: _Dispatcher) -> None:
        self.dispatcher = dispatcher
        self.events: list[Event] = []
        self.shutdown_called = False

    async def emit(self, event: Event) -> None:
        self.events.append(event)
        handler = self.dispatcher.handlers[event.type]
        result = await handler.handle(event)
        assert event.request is not None
        assert event.request.reply is not None
        event.request.reply.set_result(result)

    async def shutdown(self) -> None:
        self.shutdown_called = True


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _members() -> tuple[GitHubDualArtifactRunMember, ...]:
    request = GitHubAuthoritativeRequestArtifact(
        origin_frame_id="github-frame:newicody/projects/issues/41",
        ticket_revision_id="github-ticket-revision:r14-41",
        artifact_ref="github-request:newicody/projects:41:r14",
        repository="newicody/projects",
        issue_number=41,
        title="Comprendre les dimensions de cette relation",
        body=(
            "Je l'aime et nous parlons souvent. "
            "Mais j'ai l'impression de faire toujours plus que lui. "
            "Nous évitons de parler d'engagement."
        ),
        issue_url="https://github.com/newicody/projects/issues/41",
        labels=("research",),
    )
    advisory = GitHubCopilotFirstOpinionAdvisoryArtifact(
        origin_frame_id=request.origin_frame_id,
        ticket_revision_id=request.ticket_revision_id,
        artifact_ref="github-advisory:newicody/projects:41:r14",
        request_artifact_ref=request.artifact_ref,
        prompt_digest="a" * 64,
        response_digest="b" * 64,
        concrete_objective="Identifier les dimensions concrètes à étudier.",
        expected_result="Deux analyses attribuées puis une synthèse.",
        provided_constraints=("Ne pas ajouter de fait absent de la demande.",),
        success_criteria=("Conserver les contradictions et incertitudes.",),
    )
    request_bytes = canonical_json_bytes(request.to_mapping())
    advisory_bytes = canonical_json_bytes(advisory.to_mapping())
    manifest = build_dual_artifact_manifest(
        request,
        request_bytes,
        advisory,
        advisory_bytes,
    )
    return (
        GitHubDualArtifactRunMember(
            "autodoc-authoritative-request",
            "authoritative_request.json",
            request_bytes,
        ),
        GitHubDualArtifactRunMember(
            "autodoc-copilot-advisory",
            "copilot_advisory.json",
            advisory_bytes,
        ),
        GitHubDualArtifactRunMember(
            "autodoc-dual-artifact-manifest",
            "dual_artifact_manifest.json",
            canonical_json_bytes(manifest.to_mapping()),
        ),
    )


def _store() -> SQLiteContextRevisionAuthorityStore:
    store = SQLiteContextRevisionAuthorityStore()
    store.initialize_schema()
    source = ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref="sql:love-source:r14",
        object_kind="research_source",
        content_schema_ref="missipy.github.authoritative_request.v1",
        content_digest=_sha("source-r14"),
        title="Source de l'étude r14",
        body="source-r14",
        media_type="text/plain",
        byte_count=10,
    )
    store.put_object(source)
    store.put_revision(
        ContextRevision(
            schema=CONTEXT_REVISION_SCHEMA,
            revision_ref="context-revision:love-r14-base",
            context_ref="context:love-study-r14",
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
            evidence_refs=("evidence:issue:41",),
            created_at="2026-07-16T20:00:00Z",
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
        profile_ref="qdrant-profile:love-r14",
        collection_name="autodoc_context",
        collection_alias="autodoc_context_active",
        point_identity_field="point_id",
        authority_ref_field="sql_ref",
        named_vectors=(dense, sparse),
        payload_indexes=build_canonical_payload_indexes(),
    )


class _ProjectionPort:
    def __init__(self) -> None:
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
        projection = VectorProjectionMetadata(
            schema=VECTOR_PROJECTION_METADATA_SCHEMA,
            projection_ref=(
                "qdrant-projection:" + authority_object.object_ref.split(":")[-1]
            ),
            source_ref=authority_object.object_ref,
            source_content_digest=authority_object.content_digest,
            embedding_profile_ref="embedding-profile:e5-small-v1",
            model_ref="model:e5-small",
            model_revision="1",
            dimension=384,
            normalized=True,
            vector_name="dense_e5_v1",
            collection_name="autodoc_context",
            point_id="point-" + authority_object.object_ref.split(":")[-1],
            projection_state="active",
            projected_at="2026-07-16T20:00:00Z",
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
    def __init__(self, projection_port: _ProjectionPort) -> None:
        self.projection_port = projection_port

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

    def search_dense(self, embedding, *, query, collection):
        return tuple(
            self._candidate("dense", item, query, rank)
            for rank, item in enumerate(self.projection_port.objects, 1)
        )

    def search_sparse(self, sparse_query, *, query, collection):
        return tuple(
            self._candidate("sparse", item, query, rank)
            for rank, item in enumerate(reversed(self.projection_port.objects), 1)
        )


def _command(**changes: object) -> LoveFullDeterministicLocalSmokeCommand:
    values: dict[str, object] = {
        "schema": LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_COMMAND_SCHEMA,
        "repository": "newicody/projects",
        "run_id": "r14-local-41",
        "members": _members(),
        "operator_decision": SourceCandidateDecision(
            action="promote",
            reason="Local deterministic proof approved.",
        ),
        "conversation_ref": "laboratory-conversation:love-r14-41",
        "return_route_ref": "route:github-issue-41",
        "context_generation": 4,
        "base_revision_ref": "context-revision:love-r14-base",
        "branch_ref": "context-branch:main",
        "project_ref": "project:newicody-projects",
        "security_scope": "scope:local",
        "artifact_storage_ref": "storage:zfs:love-r14-final",
        "created_at": "2026-07-16T20:00:00Z",
        "policy_decision_id": "policy:love-r14-local-proof",
        "project_item_id": "PVTI_love41",
        "project_field_ref": "PVTF_status",
        "project_field_name": "Status",
        "project_status_value": "Terminé",
        "context_refs": ("ctx:operator-approved:41",),
        "evidence_refs": ("evidence:issue:41",),
    }
    values.update(changes)
    return LoveFullDeterministicLocalSmokeCommand(**values)


def _run(command: LoveFullDeterministicLocalSmokeCommand | None = None):
    dispatcher = _Dispatcher()
    scheduler = _Scheduler(dispatcher)
    projection = _ProjectionPort()
    result = asyncio.run(
        run_love_full_deterministic_local_smoke(
            command or _command(),
            scheduler=scheduler,
            dispatcher=dispatcher,
            authority_store=_store(),
            projection_port=projection,
            collection=_collection(),
            embedder=_Embedder(),
            executor=_Executor(projection),
        )
    )
    return result, scheduler


def test_full_local_chain_closes_r14_without_remote_mutation() -> None:
    result, scheduler = _run()

    assert result.run_assembly["recognized_member_count"] == 3
    assert result.work_package["request_authoritative"] is True
    assert result.work_package["advisory_used_as_hint_only"] is True
    assert result.decided_candidate.status == "promoted"
    assert len(scheduler.events) == 2
    assert all(event.dest == "scheduler" for event in scheduler.events)
    assert result.collaboration.conversation.closed is True
    assert result.synthesis_result.study_result.status == "synthesized"
    assert len(result.synthesis_result.retrieval.items) == 2
    assert result.publication_plan.action == "create_and_project"
    assert result.readback.action == "confirmed"
    boundaries = result.to_mapping()["boundaries"]
    assert boundaries["sql_is_authority"] is True
    assert boundaries["qdrant_is_projection_only"] is True
    assert boundaries["openvino_e5_384_reused"] is True
    assert boundaries["remote_mutation_performed"] is False


def test_proof_digest_is_deterministic_despite_scheduler_event_ids() -> None:
    first, first_scheduler = _run()
    second, second_scheduler = _run()

    assert first.proof_digest == second.proof_digest
    assert first.proof_ref == second.proof_ref
    assert first.stage_refs == second.stage_refs
    assert first.first_receipt.event_id != second.first_receipt.event_id
    assert len(first_scheduler.events) == len(second_scheduler.events) == 2


def test_authoritative_request_not_copilot_text_drives_study() -> None:
    result, _ = _run()

    assert result.study.objective == "Comprendre les dimensions de cette relation"
    assert result.study.subject_text.startswith("Je l'aime")
    assert "Identifier les dimensions concrètes" not in result.study.subject_text
    assert result.first_task.metadata["request_authoritative"] is True
    assert result.first_task.metadata["advisory_used_as_hint_only"] is True


def test_operator_gate_rejects_non_execution_decision() -> None:
    with pytest.raises(
        LoveFullDeterministicLocalSmokeError,
        match="promote or merge",
    ):
        _command(
            operator_decision=SourceCandidateDecision(
                action="inspect",
                reason="Not approved yet.",
            )
        )


def test_three_artifacts_are_mandatory_and_tamper_fails_closed() -> None:
    with pytest.raises(
        LoveFullDeterministicLocalSmokeError,
        match="exactly the request, advisory and manifest",
    ):
        _command(members=_members()[:2])

    members = list(_members())
    first = members[0]
    members[0] = GitHubDualArtifactRunMember(
        first.artifact_name,
        first.filename,
        first.content + b" ",
    )
    with pytest.raises(
        LoveFullDeterministicLocalSmokeError,
        match="artifact assembly failed",
    ):
        _run(_command(members=tuple(members)))



def test_visit_refs_follow_existing_laboratory_contract_prefixes() -> None:
    result, _ = _run()

    assert result.first_task.return_route_ref == "route:github-issue-41"
    assert result.first_task.context_refs == (
        "ctx:love-study-" + result.study.study_ref.rsplit("-", 1)[-1],
    )
    assert result.first_visit.return_route_ref.startswith(("route:", "specialist-path:"))
    assert all(ref.startswith("ctx:") for ref in result.first_visit.context_refs)
    assert result.decided_candidate.candidate_id not in result.study.context_refs


def test_invalid_visit_boundary_refs_fail_before_execution() -> None:
    with pytest.raises(
        LoveFullDeterministicLocalSmokeError,
        match="return_route_ref must start",
    ):
        _command(return_route_ref="return-route:github-issue-41")

    with pytest.raises(
        LoveFullDeterministicLocalSmokeError,
        match="existing love-study context prefix",
    ):
        _command(context_refs=("context:operator-approved:41",))

def test_remote_mutation_flag_is_rejected_before_execution() -> None:
    with pytest.raises(
        LoveFullDeterministicLocalSmokeError,
        match="remote mutation must remain disabled",
    ):
        _command(remote_mutation_allowed=True)
