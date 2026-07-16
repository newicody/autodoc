from __future__ import annotations

import hashlib
import sqlite3

import pytest

from context.context_revision_sql_authority_0287 import (
    CONTEXT_AUTHORITY_OBJECT_SCHEMA,
    CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
    CONTEXT_REVISION_SCHEMA,
    ContextAuthorityObject,
    ContextRevision,
    ContextRevisionMembership,
    DbApiContextRevisionAuthorityStore,
)
from context.hybrid_retrieval_sql_rehydration_0287 import (
    DENSE_QUERY_EMBEDDING_SCHEMA,
    HYBRID_CANDIDATE_SCHEMA,
    HYBRID_FILTER_SCHEMA,
    HYBRID_QUERY_SCHEMA,
    HYBRID_RESULT_SCHEMA,
    DenseQueryEmbedding,
    HybridRetrievalCandidate,
    HybridRetrievalError,
    HybridRetrievalFilter,
    HybridRetrievalQuery,
    build_hybrid_retrieval_report,
    build_sparse_lexical_query,
    execute_hybrid_retrieval,
    fuse_hybrid_candidates,
)
from context.qdrant_canonical_profile_0287 import (
    QDRANT_COLLECTION_PROFILE_SCHEMA,
    QDRANT_NAMED_VECTOR_SCHEMA,
    QdrantCollectionProfile,
    QdrantNamedVectorProfile,
    build_canonical_payload_indexes,
)


def _digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _dense_profile() -> QdrantNamedVectorProfile:
    return QdrantNamedVectorProfile(
        schema=QDRANT_NAMED_VECTOR_SCHEMA,
        vector_name="dense_e5_v1",
        vector_kind="dense",
        embedding_profile_ref="embedding-profile:e5-small-v1",
        model_ref="model:e5-small",
        model_revision="1",
        dimension=4,
        distance="Cosine",
        normalized=True,
    )


def _sparse_profile() -> QdrantNamedVectorProfile:
    return QdrantNamedVectorProfile(
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


def _collection(*, include_sparse: bool = True) -> QdrantCollectionProfile:
    vectors = (_dense_profile(),)
    if include_sparse:
        vectors += (_sparse_profile(),)
    return QdrantCollectionProfile(
        schema=QDRANT_COLLECTION_PROFILE_SCHEMA,
        profile_ref="qdrant-profile:hybrid-v1",
        collection_name="autodoc_context",
        collection_alias="autodoc_context_active",
        point_identity_field="point_id",
        authority_ref_field="sql_ref",
        named_vectors=vectors,
        payload_indexes=build_canonical_payload_indexes(),
    )


def _filter() -> HybridRetrievalFilter:
    return HybridRetrievalFilter(
        schema=HYBRID_FILTER_SCHEMA,
        context_revision_ref="context-revision:r1",
        branch_ref="context-branch:main",
        project_ref="project:newicody-autodoc",
        security_scope="scope:local",
        conversation_ref="conversation:issue-7",
        sql_authority_ref="sql-authority:sqlite:test",
        artifact_kinds=("analysis",),
        contribution_kinds=("domain_analysis",),
    )


def _query(*, group_by: str = "document_ref") -> HybridRetrievalQuery:
    return HybridRetrievalQuery(
        schema=HYBRID_QUERY_SCHEMA,
        query_ref="retrieval-query:love-1",
        task_ref="specialist-task:love-analysis",
        query_text="amour confiance confiance réciprocité",
        filter=_filter(),
        dense_candidate_limit=8,
        sparse_candidate_limit=8,
        final_limit=4,
        group_by=group_by,
    )


def _object(object_ref: str, text: str, title: str) -> ContextAuthorityObject:
    return ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref=object_ref,
        object_kind="specialist_output",
        content_schema_ref="missipy.specialist.deep_analysis_contribution.v1",
        content_digest=_digest(text),
        title=title,
        body=text,
        media_type="application/json",
        byte_count=len(text.encode("utf-8")),
        metadata={"authoritative": True},
    )


def _store(
    *,
    second_state: str = "active",
) -> tuple[
    DbApiContextRevisionAuthorityStore,
    ContextAuthorityObject,
    ContextAuthorityObject,
]:
    connection = sqlite3.connect(":memory:")
    store = DbApiContextRevisionAuthorityStore(connection)
    store.initialize_schema()
    first = _object(
        "context-object:love-1",
        "L'affection est présente et la confiance est incertaine.",
        "Analyse affective",
    )
    second = _object(
        "context-object:love-2",
        "La réciprocité doit être clarifiée par un dialogue.",
        "Analyse relationnelle",
    )
    store.put_object(first)
    store.put_object(second)
    revision = ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref="context-revision:r1",
        context_ref="context:love-study",
        parent_revision_refs=(),
        memberships=(
            ContextRevisionMembership(
                schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
                object_ref=first.object_ref,
                state="active",
            ),
            ContextRevisionMembership(
                schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
                object_ref=second.object_ref,
                state=second_state,
            ),
        ),
        validation_status="accepted",
        significance="material",
        evidence_refs=("evidence:issue-7",),
        producer_task_ref="specialist-task:love-analysis",
        producer_specialist_ref="specialist:love-analyst",
        producer_laboratory_ref="laboratory:love-local",
        created_at="2026-07-16T00:00:00Z",
    )
    store.put_revision(revision)
    return store, first, second


def _payload(
    item: ContextAuthorityObject,
    *,
    document_ref: str,
    digest: str | None = None,
) -> dict[str, object]:
    return {
        "sql_ref": item.object_ref,
        "source_ref": item.object_ref,
        "source_content_digest": digest or item.content_digest,
        "context_revision_ref": "context-revision:r1",
        "branch_ref": "context-branch:main",
        "project_ref": "project:newicody-autodoc",
        "conversation_ref": "conversation:issue-7",
        "security_scope": "scope:local",
        "sql_authority_ref": "sql-authority:sqlite:test",
        "artifact_kind": "analysis",
        "contribution_kind": "domain_analysis",
        "document_ref": document_ref,
        "valid": True,
        "superseded_by": "",
    }


def _candidate(
    source: str,
    item: ContextAuthorityObject,
    *,
    point: str,
    document_ref: str,
    score: float,
    digest: str | None = None,
) -> HybridRetrievalCandidate:
    return HybridRetrievalCandidate(
        schema=HYBRID_CANDIDATE_SCHEMA,
        source=source,
        point_id=point,
        sql_ref=item.object_ref,
        source_ref=item.object_ref,
        score=score,
        payload=_payload(item, document_ref=document_ref, digest=digest),
    )


class _Embedder:
    def embed_query(
        self,
        query_text: str,
        *,
        query_ref: str,
        vector_name: str,
    ) -> DenseQueryEmbedding:
        assert "amour" in query_text
        return DenseQueryEmbedding(
            schema=DENSE_QUERY_EMBEDDING_SCHEMA,
            query_ref=query_ref,
            vector_name=vector_name,
            model_ref="model:e5-small",
            model_revision="1",
            backend_ref="openvino:embedding.e5-small",
            values=(1.0, 0.0, 0.0, 0.0),
        )


class _Executor:
    def __init__(self, dense, sparse):
        self.dense = dense
        self.sparse = sparse
        self.filters = []

    def search_dense(self, embedding, *, query, collection):
        assert embedding.role == "query"
        assert collection.collection_name == "autodoc_context"
        self.filters.append(query.filter.to_qdrant_filter())
        return self.dense

    def search_sparse(self, sparse_query, *, query, collection):
        assert sparse_query.terms
        assert collection.collection_name == "autodoc_context"
        self.filters.append(query.filter.to_qdrant_filter())
        return self.sparse


def test_sparse_query_is_deterministic_and_weighted() -> None:
    first = build_sparse_lexical_query(
        "Amour confiance confiance",
        query_ref="retrieval-query:1",
    )
    second = build_sparse_lexical_query(
        "Amour confiance confiance",
        query_ref="retrieval-query:1",
    )
    assert first == second
    assert len(first.indices) == 2
    assert pytest.approx(sum(weight * weight for weight in first.weights)) == 1.0


def test_filter_contains_revision_branch_security_and_sql_authority() -> None:
    filter_mapping = _filter().to_qdrant_filter()
    fields = {item["key"] for item in filter_mapping["must"]}
    assert {
        "context_revision_ref",
        "branch_ref",
        "project_ref",
        "security_scope",
        "sql_authority_ref",
        "valid",
    }.issubset(fields)


def test_hybrid_query_requires_distinct_named_vectors() -> None:
    with pytest.raises(HybridRetrievalError, match="must differ"):
        HybridRetrievalQuery(
            schema=HYBRID_QUERY_SCHEMA,
            query_ref="retrieval-query:bad",
            task_ref="specialist-task:bad",
            query_text="amour",
            filter=_filter(),
            dense_vector_name="same",
            sparse_vector_name="same",
        )


def test_fusion_groups_multiple_chunks_from_one_document() -> None:
    _, first, second = _store()
    dense = (
        _candidate(
            "dense",
            first,
            point="point:1",
            document_ref="document:a",
            score=0.9,
        ),
        _candidate(
            "dense",
            second,
            point="point:2",
            document_ref="document:a",
            score=0.8,
        ),
    )
    sparse = (
        _candidate(
            "sparse",
            second,
            point="point:2",
            document_ref="document:a",
            score=2.0,
        ),
    )
    hits = fuse_hybrid_candidates(dense, sparse, query=_query())
    assert len(hits) == 1
    assert hits[0].sql_ref == second.object_ref
    assert hits[0].dense_rank == 2
    assert hits[0].sparse_rank == 1


def test_end_to_end_hybrid_search_rehydrates_sql_authority() -> None:
    store, first, second = _store()
    dense = (
        _candidate(
            "dense",
            first,
            point="point:1",
            document_ref="document:a",
            score=0.92,
        ),
        _candidate(
            "dense",
            second,
            point="point:2",
            document_ref="document:b",
            score=0.81,
        ),
    )
    sparse = (
        _candidate(
            "sparse",
            second,
            point="point:2",
            document_ref="document:b",
            score=3.2,
        ),
    )
    executor = _Executor(dense, sparse)
    result = execute_hybrid_retrieval(
        _query(),
        collection=_collection(),
        embedder=_Embedder(),
        executor=executor,
        authority_store=store,
    )
    assert result.schema == HYBRID_RESULT_SCHEMA
    assert tuple(item.sql_ref for item in result.items) == (
        second.object_ref,
        first.object_ref,
    )
    assert result.items[0].body == second.body
    assert len(executor.filters) == 2
    mapping = result.to_mapping()
    assert mapping["boundaries"]["sql_is_authority"] is True
    assert "values" not in mapping["dense_embedding"]
    assert mapping["query"]["query_text_serialized"] is False


def test_candidate_scope_mismatch_fails_closed() -> None:
    _, first, _ = _store()
    candidate = _candidate(
        "dense",
        first,
        point="point:1",
        document_ref="document:a",
        score=0.9,
    )
    payload = dict(candidate.payload)
    payload["branch_ref"] = "context-branch:other"
    bad = HybridRetrievalCandidate(
        schema=HYBRID_CANDIDATE_SCHEMA,
        source="dense",
        point_id=candidate.point_id,
        sql_ref=candidate.sql_ref,
        source_ref=candidate.source_ref,
        score=candidate.score,
        payload=payload,
    )
    with pytest.raises(HybridRetrievalError, match="branch_ref"):
        fuse_hybrid_candidates((bad,), (), query=_query(group_by="none"))


def test_digest_mismatch_is_rejected_before_content_is_used() -> None:
    store, first, _ = _store()
    candidate = _candidate(
        "dense",
        first,
        point="point:1",
        document_ref="document:a",
        score=0.9,
        digest="sha256:" + "0" * 64,
    )
    with pytest.raises(HybridRetrievalError, match="digest"):
        execute_hybrid_retrieval(
            _query(group_by="none"),
            collection=_collection(),
            embedder=_Embedder(),
            executor=_Executor((candidate,), ()),
            authority_store=store,
        )


def test_inactive_revision_member_is_rejected() -> None:
    store, _, second = _store(second_state="invalidated")
    candidate = _candidate(
        "dense",
        second,
        point="point:2",
        document_ref="document:b",
        score=0.9,
    )
    with pytest.raises(HybridRetrievalError, match="not active"):
        execute_hybrid_retrieval(
            _query(group_by="none"),
            collection=_collection(),
            embedder=_Embedder(),
            executor=_Executor((candidate,), ()),
            authority_store=store,
        )


def test_collection_must_expose_sparse_named_vector() -> None:
    store, first, _ = _store()
    candidate = _candidate(
        "dense",
        first,
        point="point:1",
        document_ref="document:a",
        score=0.9,
    )
    with pytest.raises(HybridRetrievalError, match="lacks named vector"):
        execute_hybrid_retrieval(
            _query(group_by="none"),
            collection=_collection(include_sparse=False),
            embedder=_Embedder(),
            executor=_Executor((candidate,), ()),
            authority_store=store,
        )


def test_report_is_reference_oriented_and_has_no_qdrant_write() -> None:
    store, first, _ = _store()
    candidate = _candidate(
        "dense",
        first,
        point="point:1",
        document_ref="document:a",
        score=0.9,
    )
    result = execute_hybrid_retrieval(
        _query(group_by="none"),
        collection=_collection(),
        embedder=_Embedder(),
        executor=_Executor((candidate,), ()),
        authority_store=store,
    )
    report = build_hybrid_retrieval_report(result)
    assert report["selected_sql_refs"] == [first.object_ref]
    assert report["boundaries"]["qdrant_write_performed"] is False
    assert report["boundaries"]["control_proxy_modified"] is False


def test_candidate_requires_authority_digest_in_payload() -> None:
    _, first, _ = _store()
    payload = _payload(first, document_ref="document:a")
    payload.pop("source_content_digest")
    candidate = HybridRetrievalCandidate(
        schema=HYBRID_CANDIDATE_SCHEMA,
        source="dense",
        point_id="point:missing-digest",
        sql_ref=first.object_ref,
        source_ref=first.object_ref,
        score=0.9,
        payload=payload,
    )
    with pytest.raises(HybridRetrievalError, match="source_content_digest"):
        fuse_hybrid_candidates(
            (candidate,),
            (),
            query=_query(group_by="none"),
        )


def test_duplicate_point_in_one_retrieval_path_is_rejected() -> None:
    _, first, _ = _store()
    candidate = _candidate(
        "dense",
        first,
        point="point:duplicate",
        document_ref="document:a",
        score=0.9,
    )
    with pytest.raises(HybridRetrievalError, match="duplicate point"):
        fuse_hybrid_candidates(
            (candidate, candidate),
            (),
            query=_query(group_by="none"),
        )
