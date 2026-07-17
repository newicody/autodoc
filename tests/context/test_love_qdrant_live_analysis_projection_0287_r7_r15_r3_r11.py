import asyncio
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from context.context_revision_sql_authority_0287 import (
    CONTEXT_AUTHORITY_OBJECT_SCHEMA,
    CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
    CONTEXT_REVISION_SCHEMA,
    ContextAuthorityObject,
    ContextRevision,
    ContextRevisionMembership,
)
from context.hybrid_retrieval_sql_rehydration_0287 import build_sparse_lexical_query
from context.love_qdrant_live_analysis_projection_0287 import (
    LoveQdrantLiveAnalysisProjection,
    LoveQdrantLiveAnalysisProjectionError,
)


@dataclass(frozen=True)
class _Receipt:
    schema: str
    projection: object
    openvino_e5_used: bool
    qdrant_write_performed: bool
    qdrant_returns_references_only: bool
    sql_remains_authority: bool

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "projection": self.projection.to_mapping(),
            "openvino_e5_used": self.openvino_e5_used,
            "qdrant_write_performed": self.qdrant_write_performed,
            "qdrant_returns_references_only": self.qdrant_returns_references_only,
            "sql_remains_authority": self.sql_remains_authority,
        }


class _Pipeline:
    def __init__(self) -> None:
        self.texts: list[str] = []

    async def embed_text(self, text: str) -> object:
        self.texts.append(text)
        vector = SimpleNamespace(
            values=(1.0,) + (0.0,) * 383,
            dimension=384,
            normalized=True,
        )
        return SimpleNamespace(vector=vector)


class _Writer:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def upsert_named_hybrid_point(self, **kwargs: object) -> object:
        self.calls.append(dict(kwargs))
        return SimpleNamespace(
            acknowledged=True,
            point_id=kwargs["point_id"],
        )


def _object() -> ContextAuthorityObject:
    body = '{"concepts":["attachement"],"affects":["confiance"]}'
    return ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref="sql:love-analysis:test",
        object_kind="specialist_analysis",
        content_schema_ref="missipy.love.analysis.v1",
        content_digest="sha256:" + "b" * 64,
        title="Analyse conceptuelle",
        body=body,
        media_type="application/json",
        byte_count=len(body.encode()),
        metadata={"contribution_kind": "concept_affect_analysis"},
    )


def _revision(*, state: str = "active") -> ContextRevision:
    return ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref="context-revision:analysis-test",
        context_ref="context:love-study-test",
        parent_revision_refs=(),
        memberships=(
            ContextRevisionMembership(
                schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
                object_ref="sql:love-analysis:test",
                state=state,
            ),
        ),
        validation_status="accepted",
        significance="material",
        created_at="2026-07-17T18:00:00+02:00",
    )


def _project(adapter: LoveQdrantLiveAnalysisProjection, **overrides: object) -> object:
    values = {
        "revision": _revision(),
        "branch_ref": "branch:main",
        "project_ref": "project:autodoc",
        "conversation_ref": "conversation:love-test",
        "specialist_ref": "specialist:love-concept-affect",
        "laboratory_ref": "laboratory:love-studies",
        "security_scope": "security-scope:project",
        "projected_at": "2026-07-17T18:00:00+02:00",
    }
    values.update(overrides)
    return asyncio.run(adapter.project(_object(), **values))


def test_projects_passage_dense_and_same_sparse_lexical_scheme() -> None:
    pipeline = _Pipeline()
    writer = _Writer()
    adapter = LoveQdrantLiveAnalysisProjection(
        pipeline=pipeline,
        writer=writer,
        receipt_factory=_Receipt,
    )

    receipt = _project(adapter)

    assert pipeline.texts[0].startswith("passage: Analyse conceptuelle")
    call = writer.calls[0]
    plain = pipeline.texts[0].removeprefix("passage: ")
    expected_sparse = build_sparse_lexical_query(
        plain,
        query_ref=receipt.projection.projection_ref,
        vector_name="sparse_lexical_v1",
    )
    assert call["sparse_indices"] == expected_sparse.indices
    assert call["sparse_values"] == expected_sparse.weights
    assert call["dense_values"] == (1.0,) + (0.0,) * 383
    assert receipt.projection.dimension == 384
    assert receipt.projection.normalized is True


def test_qdrant_payload_contains_references_but_not_sql_body() -> None:
    writer = _Writer()
    adapter = LoveQdrantLiveAnalysisProjection(
        pipeline=_Pipeline(),
        writer=writer,
        receipt_factory=_Receipt,
    )

    receipt = _project(adapter)
    payload = writer.calls[0]["payload"]
    mapping = receipt.to_mapping()

    assert payload["sql_ref"] == "sql:love-analysis:test"
    assert payload["source_content_digest"] == "sha256:" + "b" * 64
    assert "body" not in payload
    assert "content" not in payload
    assert mapping["projection"]["vector_values_stored"] is False
    assert "raw_vector" not in mapping["projection"]["metadata"]


def test_passage_prefix_is_not_duplicated() -> None:
    pipeline = _Pipeline()
    adapter = LoveQdrantLiveAnalysisProjection(
        pipeline=pipeline,
        writer=_Writer(),
        receipt_factory=_Receipt,
    )
    authority = _object()
    prefixed = ContextAuthorityObject(
        schema=authority.schema,
        object_ref=authority.object_ref,
        object_kind=authority.object_kind,
        content_schema_ref=authority.content_schema_ref,
        content_digest=authority.content_digest,
        title="passage: Analyse conceptuelle",
        body=authority.body,
        media_type=authority.media_type,
        byte_count=authority.byte_count,
        metadata=authority.metadata,
    )
    asyncio.run(
        adapter.project(
            prefixed,
            revision=_revision(),
            branch_ref="branch:main",
            project_ref="project:autodoc",
            conversation_ref="conversation:love-test",
            specialist_ref="specialist:love-concept-affect",
            laboratory_ref="laboratory:love-studies",
            security_scope="security-scope:project",
        )
    )
    assert pipeline.texts[0].count("passage:") == 1


def test_inactive_revision_membership_fails_before_embedding() -> None:
    pipeline = _Pipeline()
    writer = _Writer()
    adapter = LoveQdrantLiveAnalysisProjection(
        pipeline=pipeline,
        writer=writer,
        receipt_factory=_Receipt,
    )
    with pytest.raises(
        LoveQdrantLiveAnalysisProjectionError,
        match="active member",
    ):
        _project(adapter, revision=_revision(state="invalidated"))
    assert pipeline.texts == []
    assert writer.calls == []
