from __future__ import annotations

import pytest

from context.qdrant_canonical_profile_0287 import (
    EMBEDDING_SPACE_PROFILE_SCHEMA,
    QDRANT_COLLECTION_PROFILE_SCHEMA,
    QDRANT_MODEL_MIGRATION_SCHEMA,
    QDRANT_NAMED_VECTOR_SCHEMA,
    QDRANT_POINT_PROJECTION_SCHEMA,
    VECTOR_PROJECTION_METADATA_SCHEMA,
    QdrantCanonicalProfileError,
    QdrantCollectionProfile,
    QdrantNamedVectorProfile,
    QdrantPointProjection,
    build_canonical_payload_indexes,
    build_canonical_profile_report,
    build_named_vector_from_embedding_profile,
    build_point_projection_from_sql_metadata,
    choose_model_migration_strategy,
)

DIGEST = "sha256:" + "a" * 64
MODEL_DIGEST = "sha256:" + "b" * 64


def _embedding_profile(*, model_ref: str = "model:e5-small", revision: str = "1"):
    return {
        "schema": EMBEDDING_SPACE_PROFILE_SCHEMA,
        "profile_ref": f"embedding-profile:{model_ref.split(':', 1)[1]}-{revision}",
        "backend_ref": "openvino:embedding.e5-small",
        "model_ref": model_ref,
        "model_revision": revision,
        "tokenizer_ref": "tokenizer:multilingual-e5-small",
        "pooling": "mean",
        "normalized": True,
        "dimension": 384,
        "distance": "Cosine",
        "role": "passage",
        "collection_name": "autodoc_context",
        "model_artifact_digest": MODEL_DIGEST,
    }


def _collection(
    *,
    vector_name: str = "dense_e5_v1",
    model_ref: str = "model:e5-small",
    revision: str = "1",
    collection_name: str = "autodoc_context",
    profile_ref: str = "qdrant-profile:context-v1",
):
    vector = build_named_vector_from_embedding_profile(
        _embedding_profile(model_ref=model_ref, revision=revision),
        vector_name=vector_name,
    )
    return QdrantCollectionProfile(
        schema=QDRANT_COLLECTION_PROFILE_SCHEMA,
        profile_ref=profile_ref,
        collection_name=collection_name,
        collection_alias="autodoc_context_active",
        point_identity_field="point_id",
        authority_ref_field="sql_ref",
        named_vectors=(vector,),
        payload_indexes=build_canonical_payload_indexes(),
    )


def _projection(*, vector_name: str = "dense_e5_v1"):
    return {
        "schema": VECTOR_PROJECTION_METADATA_SCHEMA,
        "projection_ref": "projection:object-1-e5",
        "source_ref": "context-object:object-1",
        "source_content_digest": DIGEST,
        "embedding_profile_ref": "embedding-profile:e5-small-1",
        "model_ref": "model:e5-small",
        "model_revision": "1",
        "dimension": 384,
        "normalized": True,
        "vector_name": vector_name,
        "collection_name": "autodoc_context",
        "point_id": "object-1",
        "projection_state": "active",
        "projected_at": "2026-07-16T00:00:00Z",
        "metadata": {},
    }


def test_embedding_profile_becomes_named_vector() -> None:
    vector = build_named_vector_from_embedding_profile(
        _embedding_profile(), vector_name="dense_e5_v1"
    )
    assert vector.schema == QDRANT_NAMED_VECTOR_SCHEMA
    assert vector.vector_kind == "dense"
    assert vector.dimension == 384
    assert vector.distance == "Cosine"
    assert vector.normalized is True


def test_collection_requires_canonical_indexes_and_forbids_task_collections() -> None:
    vector = build_named_vector_from_embedding_profile(
        _embedding_profile(), vector_name="dense_e5_v1"
    )
    with pytest.raises(QdrantCanonicalProfileError, match="missing canonical"):
        QdrantCollectionProfile(
            schema=QDRANT_COLLECTION_PROFILE_SCHEMA,
            profile_ref="qdrant-profile:bad",
            collection_name="task_1",
            collection_alias="task_active",
            point_identity_field="point_id",
            authority_ref_field="sql_ref",
            named_vectors=(vector,),
            payload_indexes=(),
        )
    with pytest.raises(QdrantCanonicalProfileError, match="one collection per task"):
        QdrantCollectionProfile(
            schema=QDRANT_COLLECTION_PROFILE_SCHEMA,
            profile_ref="qdrant-profile:bad-task",
            collection_name="task_1",
            collection_alias="task_active",
            point_identity_field="point_id",
            authority_ref_field="sql_ref",
            named_vectors=(vector,),
            payload_indexes=build_canonical_payload_indexes(),
            one_collection_per_task_allowed=True,
        )


def test_sql_metadata_builds_reference_only_point() -> None:
    point = build_point_projection_from_sql_metadata(
        _projection(),
        collection=_collection(),
        context_revision_ref="context-revision:r1",
        branch_ref="context-branch:main",
        project_ref="project:newicody-autodoc",
        conversation_ref="conversation:issue-1",
        artifact_kind="context",
        contribution_kind="source",
        specialist_ref="specialist:love-analyst",
        laboratory_ref="laboratory:love-local",
    )
    assert point.schema == QDRANT_POINT_PROJECTION_SCHEMA
    payload = point.qdrant_payload()
    assert payload["sql_ref"] == "context-object:object-1"
    assert payload["context_revision_ref"] == "context-revision:r1"
    assert "content" not in payload
    assert "vector" not in payload
    assert "local_path" not in payload


def test_projection_must_match_collection_named_vector() -> None:
    payload = _projection()
    payload["model_revision"] = "2"
    with pytest.raises(QdrantCanonicalProfileError, match="model_revision"):
        build_point_projection_from_sql_metadata(
            payload,
            collection=_collection(),
            context_revision_ref="context-revision:r1",
            branch_ref="context-branch:main",
            project_ref="project:newicody-autodoc",
            conversation_ref="conversation:issue-1",
            artifact_kind="context",
            contribution_kind="source",
        )


def test_raw_content_is_rejected_from_payload_metadata() -> None:
    point = QdrantPointProjection(
        schema=QDRANT_POINT_PROJECTION_SCHEMA,
        point_id="object-1",
        collection_profile_ref="qdrant-profile:context-v1",
        vector_name="dense_e5_v1",
        source_ref="context-object:object-1",
        source_content_digest=DIGEST,
        projection_ref="projection:object-1-e5",
        context_revision_ref="context-revision:r1",
        branch_ref="context-branch:main",
        project_ref="project:newicody-autodoc",
        conversation_ref="conversation:issue-1",
        artifact_kind="context",
        contribution_kind="source",
        metadata={"content": "forbidden"},
    )
    with pytest.raises(QdrantCanonicalProfileError, match="forbidden"):
        point.qdrant_payload()


def test_same_collection_uses_named_vector_migration() -> None:
    source = _collection()
    target = _collection(
        vector_name="dense_e5_v2",
        model_ref="model:e5-small-v2",
        revision="2",
        profile_ref="qdrant-profile:context-v2",
    )
    plan = choose_model_migration_strategy(
        source,
        target,
        source_vector_name="dense_e5_v1",
        target_vector_name="dense_e5_v2",
        migration_ref="migration:e5-v1-v2",
    )
    assert plan.schema == QDRANT_MODEL_MIGRATION_SCHEMA
    assert plan.strategy == "named_vector"
    assert plan.alias_swap_required is False
    assert plan.operator_approval_required is True


def test_different_collection_uses_alias_swap() -> None:
    source = _collection()
    target = _collection(
        vector_name="dense_e5_v2",
        model_ref="model:e5-small-v2",
        revision="2",
        collection_name="autodoc_context_v2",
        profile_ref="qdrant-profile:context-v2",
    )
    plan = choose_model_migration_strategy(
        source,
        target,
        source_vector_name="dense_e5_v1",
        target_vector_name="dense_e5_v2",
        migration_ref="migration:e5-alias-swap",
    )
    assert plan.strategy == "alias_swap"
    assert plan.alias_swap_required is True


def test_profile_report_is_inspection_only_and_deterministic() -> None:
    collection = _collection()
    first = build_canonical_profile_report(collection)
    second = build_canonical_profile_report(collection)
    assert first == second
    assert first["boundaries"]["sql_remains_authority"] is True
    assert first["boundaries"]["qdrant_write_performed"] is False
    assert first["boundaries"]["control_proxy_modified"] is False
    assert first["profile_digest"].startswith("sha256:")
