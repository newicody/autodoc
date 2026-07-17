import asyncio
from types import SimpleNamespace

import pytest

from context.context_revision_sql_authority_0287 import (
    CONTEXT_AUTHORITY_OBJECT_SCHEMA,
    CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
    CONTEXT_REVISION_SCHEMA,
    CONTEXT_SQL_WRITE_RESULT_SCHEMA,
    VECTOR_PROJECTION_METADATA_SCHEMA,
    ContextAuthorityObject,
    ContextRevision,
    ContextRevisionMembership,
    ContextSqlWriteResult,
    VectorProjectionMetadata,
)
from context.love_live_qdrant_projection_probe_0287 import (
    LOVE_LIVE_QDRANT_PROJECTION_RECEIPT_SCHEMA,
    LoveLiveProjectionProbeGate,
    LoveLiveProjectionProbeRequest,
    LoveLiveQdrantProjectionProbeError,
    build_love_live_projection_probe_plan,
    execute_love_live_projection_probe,
    inspect_love_live_projection_probe,
)


class _Store:
    def __init__(self) -> None:
        self.authority_object = _object()
        self.revision = _revision()
        self.projections: dict[str, VectorProjectionMetadata] = {}

    def get_object(self, object_ref: str) -> ContextAuthorityObject | None:
        return self.authority_object if object_ref == self.authority_object.object_ref else None

    def get_revision(self, revision_ref: str) -> ContextRevision | None:
        return self.revision if revision_ref == self.revision.revision_ref else None

    def put_projection(self, item: VectorProjectionMetadata) -> ContextSqlWriteResult:
        existing = self.projections.get(item.projection_ref)
        if existing is not None and existing.to_mapping() != item.to_mapping():
            raise AssertionError("immutable collision")
        self.projections[item.projection_ref] = item
        return ContextSqlWriteResult(
            entity_kind="vector_projection_metadata",
            entity_ref=item.projection_ref,
            inserted=existing is None,
            idempotent_replay=existing is not None,
        )

    def get_projection(self, projection_ref: str) -> VectorProjectionMetadata | None:
        return self.projections.get(projection_ref)


class _Projector:
    def __init__(self) -> None:
        self.calls = 0

    async def project(self, authority_object: ContextAuthorityObject, **kwargs: object) -> object:
        self.calls += 1
        revision = kwargs["revision"]
        projection = VectorProjectionMetadata(
            schema=VECTOR_PROJECTION_METADATA_SCHEMA,
            projection_ref="vector-projection:test",
            source_ref=authority_object.object_ref,
            source_content_digest=authority_object.content_digest,
            embedding_profile_ref="embedding-profile:multilingual-e5-small-passage",
            model_ref="model:multilingual-e5-small",
            model_revision="installed",
            dimension=384,
            normalized=True,
            vector_name="dense_e5_v1",
            collection_name="autodoc_context_e5_384_hybrid_v1",
            point_id="qdrant-point:test",
            projection_state="active",
            projected_at="2026-07-17T20:00:00+02:00",
            metadata={"sparse_vector_name": "sparse_lexical_v1"},
        )
        return SimpleNamespace(projection=projection, revision=revision)


class _Reader:
    def __init__(self, *, digest: str | None = None) -> None:
        self.digest = digest
        self.calls: list[dict[str, str]] = []

    def read_named_reference_point(self, *, collection_name: str, point_id: str) -> object:
        self.calls.append({"collection_name": collection_name, "point_id": point_id})
        return SimpleNamespace(
            point_id=point_id,
            sql_ref="sql:love-analysis:probe",
            source_ref="sql:love-analysis:probe",
            payload={
                "point_id": point_id,
                "sql_ref": "sql:love-analysis:probe",
                "source_ref": "sql:love-analysis:probe",
                "source_content_digest": self.digest or ("sha256:" + "a" * 64),
                "context_revision_ref": "context-revision:love-probe",
                "project_ref": "project:autodoc",
                "valid": True,
            },
        )


def _object() -> ContextAuthorityObject:
    body = '{"analysis":"projection live"}'
    return ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref="sql:love-analysis:probe",
        object_kind="specialist_analysis",
        content_schema_ref="missipy.love.analysis.v1",
        content_digest="sha256:" + "a" * 64,
        title="Analyse live",
        body=body,
        media_type="application/json",
        byte_count=len(body.encode()),
        metadata={"contribution_kind": "concept_affect_analysis"},
    )


def _revision() -> ContextRevision:
    return ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref="context-revision:love-probe",
        context_ref="context:love-probe",
        parent_revision_refs=(),
        memberships=(
            ContextRevisionMembership(
                schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
                object_ref="sql:love-analysis:probe",
                state="active",
            ),
        ),
        validation_status="accepted",
        significance="material",
        created_at="2026-07-17T20:00:00+02:00",
    )


def _plan():
    request = LoveLiveProjectionProbeRequest(
        object_ref="sql:love-analysis:probe",
        revision_ref="context-revision:love-probe",
        branch_ref="branch:main",
        project_ref="project:autodoc",
        conversation_ref="conversation:love-probe",
        specialist_ref="specialist:love-concept-affect",
        laboratory_ref="laboratory:love-studies",
        security_scope="security-scope:project",
        projected_at="2026-07-17T20:00:00+02:00",
    )
    return build_love_live_projection_probe_plan(
        request,
        collection_name="autodoc_context_e5_384_hybrid_v1",
        dense_vector_name="dense_e5_v1",
        sparse_vector_name="sparse_lexical_v1",
        model_ref="model:multilingual-e5-small",
        model_revision="installed",
    )


def _gate(plan):
    return LoveLiveProjectionProbeGate(
        policy_decision_id="policy:love-probe",
        operator_decision="approve",
        allow_write=True,
        confirm_plan_digest=plan.plan_digest,
    )


def test_preview_reads_sql_only_and_exposes_stable_plan_digest() -> None:
    store = _Store()
    plan = _plan()
    readiness = inspect_love_live_projection_probe(store, plan)
    assert readiness.ready is True
    assert readiness.issues == ()
    assert readiness.boundaries["openvino_constructed"] is False
    assert readiness.boundaries["qdrant_client_constructed"] is False
    assert plan.plan_digest.startswith("sha256:")
    assert plan.to_mapping()["plan_digest"] == plan.plan_digest


def test_execute_projects_one_point_persists_metadata_and_rehydrates_sql() -> None:
    store = _Store()
    projector = _Projector()
    reader = _Reader()
    plan = _plan()
    receipt = asyncio.run(
        execute_love_live_projection_probe(
            store,
            projector,
            reader,
            plan,
            _gate(plan),
        )
    )
    mapping = receipt.to_mapping()
    assert mapping["schema"] == LOVE_LIVE_QDRANT_PROJECTION_RECEIPT_SCHEMA
    assert projector.calls == 1
    assert len(reader.calls) == 1
    assert mapping["checks"]["sql_source_rehydrated"] is True
    assert mapping["checks"]["sql_projection_metadata_rehydrated"] is True
    assert mapping["boundaries"]["qdrant_vectors_serialized"] is False
    assert mapping["boundaries"]["authoritative_body_serialized"] is False
    assert "body" not in mapping["qdrant_payload"]
    assert "vector" not in mapping["qdrant_payload"]


def test_gate_rejects_before_projector_or_reader() -> None:
    store = _Store()
    projector = _Projector()
    reader = _Reader()
    plan = _plan()
    gate = LoveLiveProjectionProbeGate(
        policy_decision_id="policy:love-probe",
        operator_decision="reject",
        allow_write=True,
        confirm_plan_digest=plan.plan_digest,
    )
    with pytest.raises(LoveLiveQdrantProjectionProbeError, match="did not approve"):
        asyncio.run(
            execute_love_live_projection_probe(store, projector, reader, plan, gate)
        )
    assert projector.calls == 0
    assert reader.calls == []


def test_readback_digest_mismatch_fails_closed() -> None:
    store = _Store()
    plan = _plan()
    with pytest.raises(
        LoveLiveQdrantProjectionProbeError,
        match="source_content_digest differs",
    ):
        asyncio.run(
            execute_love_live_projection_probe(
                store,
                _Projector(),
                _Reader(digest="sha256:" + "b" * 64),
                plan,
                _gate(plan),
            )
        )
