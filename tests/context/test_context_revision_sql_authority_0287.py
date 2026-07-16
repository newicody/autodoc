from __future__ import annotations

import hashlib
import sqlite3

import pytest

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
    ContextSqlAuthorityError,
    DbApiContextRevisionAuthorityStore,
    VectorProjectionMetadata,
    build_authority_object_from_sql_context_record,
    build_context_revision_ref,
)
from context.sql_context_store import build_sql_context_record


def _digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _membership(
    object_ref: str,
    state: str = "active",
    replacement_ref: str | None = None,
) -> ContextRevisionMembership:
    return ContextRevisionMembership(
        schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
        object_ref=object_ref,
        state=state,
        replacement_ref=replacement_ref,
    )


def _revision(
    name: str,
    *,
    parents: tuple[str, ...] = (),
    memberships: tuple[ContextRevisionMembership, ...],
    significance: str = "material",
) -> ContextRevision:
    return ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref=f"context-revision:{name}",
        context_ref="context:love-study",
        parent_revision_refs=parents,
        memberships=memberships,
        validation_status="accepted",
        significance=significance,
        evidence_refs=("evidence:issue-7",),
        producer_task_ref="specialist-task:analysis-1",
        producer_specialist_ref="specialist:love-analyst",
        producer_laboratory_ref="laboratory:love-studies-local",
        created_at=f"2026-07-16T00:00:0{name[-1]}Z",
        metadata={"branch": name},
    )


def _object(
    object_ref: str,
    text: str,
    *,
    title: str,
) -> ContextAuthorityObject:
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


def _artifact() -> ContextArtifactDescriptor:
    return ContextArtifactDescriptor(
        schema=CONTEXT_ARTIFACT_DESCRIPTOR_SCHEMA,
        artifact_ref="artifact:love-source-pdf",
        content_schema_ref="application/pdf",
        content_digest=_digest("pdf-bytes"),
        storage_ref="zfs:artifacts/love-source-pdf",
        media_type="application/pdf",
        byte_count=9,
        producer_task_ref="specialist-task:attachment-intake",
        created_at="2026-07-16T00:00:00Z",
        metadata={"filename": "source.pdf"},
    )


def _store() -> tuple[sqlite3.Connection, DbApiContextRevisionAuthorityStore]:
    connection = sqlite3.connect(":memory:")
    store = DbApiContextRevisionAuthorityStore(connection)
    store.initialize_schema()
    return connection, store


def test_legacy_sql_record_bridges_without_changing_v1_store() -> None:
    legacy = build_sql_context_record(
        kind="source",
        identity="issue:7",
        title="Issue 7",
        body="Analyse de l'amour",
        metadata=(("repository", "newicody/projects"),),
    )

    item = build_authority_object_from_sql_context_record(legacy)

    assert item.object_ref == legacy.context_ref
    assert item.content_schema_ref == "missipy.sql_context_store.v1"
    assert item.content_digest.startswith("sha256:")
    assert item.metadata["legacy_metadata"]["repository"] == (
        "newicody/projects"
    )


def test_store_persists_branch_merge_graph_and_rehydrates_bundle() -> None:
    _, store = _store()
    first = _object(
        "sql:specialist-output:first",
        "premiere analyse",
        title="Première analyse",
    )
    second = _object(
        "sql:specialist-output:second",
        "analyse corrigee",
        title="Analyse corrigée",
    )
    artifact = _artifact()
    store.put_object(first)
    store.put_object(second)
    store.put_artifact(artifact)

    root = _revision(
        "r1",
        memberships=(
            _membership(first.object_ref),
            _membership(artifact.artifact_ref),
        ),
    )
    branch_a = _revision(
        "r2a",
        parents=(root.revision_ref,),
        memberships=(
            _membership(
                first.object_ref,
                "superseded",
                second.object_ref,
            ),
            _membership(second.object_ref),
            _membership(artifact.artifact_ref),
        ),
    )
    branch_b = _revision(
        "r2b",
        parents=(root.revision_ref,),
        memberships=(
            _membership(first.object_ref),
            _membership(artifact.artifact_ref),
        ),
        significance="minor",
    )
    merged = _revision(
        "r3",
        parents=(branch_a.revision_ref, branch_b.revision_ref),
        memberships=(
            _membership(second.object_ref),
            _membership(artifact.artifact_ref),
        ),
        significance="critical",
    )
    for revision in (root, branch_a, branch_b, merged):
        result = store.put_revision(revision)
        assert result.inserted is True

    relation = ContextRelation(
        schema=CONTEXT_RELATION_SCHEMA,
        relation_ref="context-relation:analysis-supports-deliverable",
        source_ref=second.object_ref,
        target_ref=artifact.artifact_ref,
        relation_kind="derived_from",
        context_revision_ref=merged.revision_ref,
        evidence_refs=("evidence:issue-7",),
    )
    store.put_relation(relation)

    projection = VectorProjectionMetadata(
        schema=VECTOR_PROJECTION_METADATA_SCHEMA,
        projection_ref="vector-projection:second-analysis-e5",
        source_ref=second.object_ref,
        source_content_digest=second.content_digest,
        embedding_profile_ref="embedding-space:e5-small-passage-v1",
        model_ref="model:multilingual-e5-small",
        model_revision="local-openvino-export",
        dimension=384,
        normalized=True,
        vector_name="dense_e5_v1",
        collection_name="autodoc_context",
        point_id="point-second-analysis",
        projection_state="active",
        projected_at="2026-07-16T00:00:09Z",
        metadata={"distance": "Cosine"},
    )
    store.put_projection(projection)

    bundle = store.read_revision_bundle(merged.revision_ref)

    assert bundle.revision.parent_revision_refs == (
        branch_a.revision_ref,
        branch_b.revision_ref,
    )
    assert tuple(item.object_ref for item in bundle.objects) == (
        second.object_ref,
    )
    assert tuple(item.artifact_ref for item in bundle.artifacts) == (
        artifact.artifact_ref,
    )
    assert tuple(item.relation_ref for item in bundle.relations) == (
        relation.relation_ref,
    )
    assert tuple(item.projection_ref for item in bundle.projections) == (
        projection.projection_ref,
    )
    assert bundle.to_mapping()["vector_values_stored_in_sql"] is False
    assert len(store.list_context_revisions("context:love-study")) == 4


def test_immutable_writes_are_idempotent_and_collisions_fail_closed() -> None:
    _, store = _store()
    item = _object(
        "sql:specialist-output:stable",
        "contenu stable",
        title="Stable",
    )

    first = store.put_object(item)
    replay = store.put_object(item)

    assert first.inserted is True
    assert replay.inserted is False
    assert replay.idempotent_replay is True

    changed = _object(
        item.object_ref,
        "contenu different",
        title="Stable",
    )
    with pytest.raises(ContextSqlAuthorityError, match="collision"):
        store.put_object(changed)


def test_revision_requires_known_parents_and_known_members() -> None:
    _, store = _store()
    unknown_member = _revision(
        "missing-member",
        memberships=(_membership("sql:missing:object"),),
    )
    with pytest.raises(ContextSqlAuthorityError, match="unknown SQL authority"):
        store.put_revision(unknown_member)

    item = _object(
        "sql:specialist-output:known",
        "known",
        title="Known",
    )
    store.put_object(item)
    unknown_parent = _revision(
        "missing-parent",
        parents=("context-revision:unknown",),
        memberships=(_membership(item.object_ref),),
    )
    with pytest.raises(ContextSqlAuthorityError, match="unknown parent"):
        store.put_revision(unknown_parent)


def test_projection_metadata_matches_sql_digest_and_contains_no_vector() -> None:
    connection, store = _store()
    item = _object(
        "sql:specialist-output:projection",
        "projection source",
        title="Projection",
    )
    store.put_object(item)

    with pytest.raises(ContextSqlAuthorityError, match="source digest"):
        store.put_projection(
            VectorProjectionMetadata(
                schema=VECTOR_PROJECTION_METADATA_SCHEMA,
                projection_ref="vector-projection:wrong-digest",
                source_ref=item.object_ref,
                source_content_digest=_digest("wrong"),
                embedding_profile_ref="embedding-space:e5",
                model_ref="model:e5",
                model_revision="rev-1",
                dimension=384,
                normalized=True,
                vector_name="dense_e5_v1",
                collection_name="autodoc_context",
                point_id="point-1",
                projection_state="active",
            )
        )

    with pytest.raises(ContextSqlAuthorityError, match="vector values"):
        VectorProjectionMetadata(
            schema=VECTOR_PROJECTION_METADATA_SCHEMA,
            projection_ref="vector-projection:raw-vector",
            source_ref=item.object_ref,
            source_content_digest=item.content_digest,
            embedding_profile_ref="embedding-space:e5",
            model_ref="model:e5",
            model_revision="rev-1",
            dimension=384,
            normalized=True,
            vector_name="dense_e5_v1",
            collection_name="autodoc_context",
            point_id="point-2",
            projection_state="active",
            metadata={"vector": [0.0, 1.0]},
        )

    columns = {
        str(row[1])
        for row in connection.execute(
            "PRAGMA table_info(context_vector_projections)"
        ).fetchall()
    }
    assert "vector" not in columns
    assert "values" not in columns
    assert "embedding" not in columns
    assert "payload_json" in columns


def test_revision_reference_builder_is_deterministic() -> None:
    memberships = (_membership("sql:source:one"),)

    first = build_context_revision_ref(
        context_ref="context:one",
        parent_revision_refs=(),
        memberships=memberships,
        validation_status="accepted",
        significance="material",
    )
    second = build_context_revision_ref(
        context_ref="context:one",
        parent_revision_refs=(),
        memberships=memberships,
        validation_status="accepted",
        significance="material",
    )

    assert first == second
    assert first.startswith("context-revision:")
