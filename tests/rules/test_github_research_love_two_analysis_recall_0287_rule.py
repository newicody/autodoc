from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import context.github_research_love_two_analysis_recall_0287 as module
from context.github_research_love_sql_persistence_0287 import (
    RECEIPT_SCHEMA as SQL_RECEIPT_SCHEMA,
    RESULT_SCHEMA as SQL_RESULT_SCHEMA,
)
from context.github_research_love_two_analysis_recall_0287 import (
    GitHubResearchLoveTwoAnalysisRecallCommand,
    build_github_research_love_two_analysis_recall_plan,
    recall_github_research_love_analyses,
)
from context.github_research_love_two_qdrant_projections_0287 import (
    PLAN_SCHEMA as PROJECTION_PLAN_SCHEMA,
    RECEIPT_SCHEMA as PROJECTION_RECEIPT_SCHEMA,
    RESULT_SCHEMA as PROJECTION_RESULT_SCHEMA,
)
from context.hybrid_retrieval_sql_rehydration_0287 import (
    HYBRID_HIT_SCHEMA,
    REHYDRATED_AUTHORITY_ITEM_SCHEMA,
    HybridRetrievalHit,
    RehydratedAuthorityItem,
)


def _sql_result() -> dict[str, object]:
    return {
        "schema": SQL_RESULT_SCHEMA,
        "valid": True,
        "status": "persisted",
        "plan": {
            "plan_digest": "sha256:" + "1" * 64,
        },
        "receipt": {
            "schema": SQL_RECEIPT_SCHEMA,
            "work_package_ref": "research-work-package:test",
            "first_object_ref": "context-object:first",
            "second_object_ref": "context-object:second",
            "revision_ref": "context-revision:pair",
            "readback_verified": True,
        },
    }


def _projection_member(object_ref: str, plan_digit: str) -> tuple[dict, dict]:
    request = {
        "object_ref": object_ref,
        "revision_ref": "context-revision:pair",
        "branch_ref": "branch:github-research",
        "project_ref": "project:github-research",
        "conversation_ref": "conversation:github-research",
        "specialist_ref": (
            "specialist:first"
            if object_ref.endswith("first")
            else "specialist:second"
        ),
        "laboratory_ref": "laboratory:love-studies-local",
        "security_scope": "security:research-local",
    }
    plan = {
        "request": request,
        "collection_name": "autodoc-love",
        "dense_vector_name": "dense_e5_v1",
        "sparse_vector_name": "sparse_lexical_v1",
        "dimension": 384,
        "plan_digest": "sha256:" + plan_digit * 64,
    }
    receipt = {
        "plan_digest": plan["plan_digest"],
        "object_ref": object_ref,
        "revision_ref": "context-revision:pair",
        "qdrant_payload": {
            "point_id": f"point:{object_ref.rsplit(':', 1)[-1]}",
            "sql_ref": object_ref,
            "source_ref": object_ref,
            "source_content_digest": "sha256:" + "a" * 64,
            "context_revision_ref": "context-revision:pair",
        },
    }
    return plan, receipt


def _projection_result() -> dict[str, object]:
    first_plan, first_receipt = _projection_member(
        "context-object:first",
        "2",
    )
    second_plan, second_receipt = _projection_member(
        "context-object:second",
        "3",
    )
    return {
        "schema": PROJECTION_RESULT_SCHEMA,
        "valid": True,
        "status": "projected",
        "plan": {
            "schema": PROJECTION_PLAN_SCHEMA,
            "first": first_plan,
            "second": second_plan,
        },
        "receipt": {
            "schema": PROJECTION_RECEIPT_SCHEMA,
            "pair_plan_digest": "sha256:" + "4" * 64,
            "first": first_receipt,
            "second": second_receipt,
        },
    }


def _ports() -> SimpleNamespace:
    return SimpleNamespace(
        collection=SimpleNamespace(collection_name="autodoc-love"),
        embedder=object(),
        executor=object(),
        authority_store=object(),
    )


def _command() -> GitHubResearchLoveTwoAnalysisRecallCommand:
    return GitHubResearchLoveTwoAnalysisRecallCommand(
        runtime_ports=_ports(),  # type: ignore[arg-type]
        sql_persistence=_sql_result(),
        two_projections=_projection_result(),
        query_text=(
            "Mettre en relation les concepts, affects, réciprocités, "
            "limites et tensions relevés par les deux spécialistes."
        ),
    )


def test_plan_reuses_projection_scope_and_requires_exact_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    plan = build_github_research_love_two_analysis_recall_plan(_command())

    assert plan.expected_sql_refs == (
        "context-object:first",
        "context-object:second",
    )
    assert plan.query.final_limit == 2
    assert plan.query.group_by == "source_ref"
    assert plan.query.filter.context_revision_ref == "context-revision:pair"
    assert plan.query.dense_vector_name == "dense_e5_v1"
    assert plan.query.sparse_vector_name == "sparse_lexical_v1"
    assert plan.to_mapping()["boundaries"]["global_synthesis_created"] is False


@pytest.mark.asyncio
async def test_recall_uses_existing_async_hybrid_execution_and_keeps_bodies_in_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ports = _ports()
    command = _command()
    object.__setattr__(command, "runtime_ports", ports)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    plan = build_github_research_love_two_analysis_recall_plan(command)
    items = (
        RehydratedAuthorityItem(
            schema=REHYDRATED_AUTHORITY_ITEM_SCHEMA,
            sql_ref="context-object:first",
            authority_kind="context_object",
            content_digest="sha256:" + "a" * 64,
            title="Première analyse",
            body='{"analysis":"first"}',
            storage_ref="",
            media_type="application/json",
        ),
        RehydratedAuthorityItem(
            schema=REHYDRATED_AUTHORITY_ITEM_SCHEMA,
            sql_ref="context-object:second",
            authority_kind="context_object",
            content_digest="sha256:" + "b" * 64,
            title="Seconde analyse",
            body='{"analysis":"second"}',
            storage_ref="",
            media_type="application/json",
        ),
    )
    hits = tuple(
        HybridRetrievalHit(
            schema=HYBRID_HIT_SCHEMA,
            point_id=f"point:{index}",
            sql_ref=item.sql_ref,
            source_ref=item.sql_ref,
            group_ref=item.sql_ref,
            fused_score=0.03 - index * 0.001,
            dense_rank=index + 1,
            sparse_rank=index + 1,
            dense_score=0.9 - index * 0.1,
            sparse_score=0.8 - index * 0.1,
            payload={"sql_ref": item.sql_ref},
        )
        for index, item in enumerate(items)
    )
    captured: dict[str, object] = {}

    async def fake_execute(query, **kwargs):
        captured["query"] = query
        captured.update(kwargs)
        return SimpleNamespace(
            retrieval=SimpleNamespace(items=items, hits=hits),
            receipt=SimpleNamespace(
                to_mapping=lambda: {
                    "embedding_dimension": 384,
                    "raw_vector_serialized": False,
                }
            ),
        )

    monkeypatch.setattr(
        module,
        "execute_love_async_hybrid_retrieval",
        fake_execute,
    )

    result = await recall_github_research_love_analyses(command)
    mapping = result.to_mapping()

    assert result.valid is True
    assert result.status == "recalled"
    assert result.first_item.body == '{"analysis":"first"}'
    assert result.second_item.body == '{"analysis":"second"}'
    assert captured["collection"] is ports.collection
    assert captured["embedder"] is ports.embedder
    assert captured["executor"] is ports.executor
    assert captured["authority_store"] is ports.authority_store
    assert mapping["recalled_sql_refs"] == [
        "context-object:first",
        "context-object:second",
    ]
    assert all(
        "body" not in item for item in mapping["recalled_items"]
    )
    assert mapping["boundaries"]["rehydrated_bodies_serialized"] is False
    assert mapping["boundaries"]["global_synthesis_created"] is False


@pytest.mark.asyncio
async def test_missing_expected_analysis_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command()
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    item = RehydratedAuthorityItem(
        schema=REHYDRATED_AUTHORITY_ITEM_SCHEMA,
        sql_ref="context-object:first",
        authority_kind="context_object",
        content_digest="sha256:" + "a" * 64,
        title="Première analyse",
        body="{}",
        storage_ref="",
        media_type="application/json",
    )

    async def fake_execute(query, **kwargs):
        return SimpleNamespace(
            retrieval=SimpleNamespace(items=(item,), hits=()),
            receipt=SimpleNamespace(to_mapping=lambda: {}),
        )

    monkeypatch.setattr(
        module,
        "execute_love_async_hybrid_retrieval",
        fake_execute,
    )

    result = await recall_github_research_love_analyses(command)

    assert result.valid is False
    assert result.status == "failed"
    assert "exactly both" in result.issues[0]


def test_module_reuses_existing_retrieval_and_does_not_synthesize_or_write() -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "execute_love_async_hybrid_retrieval(" in source
    assert "HybridRetrievalFilter(" in source
    assert "HybridRetrievalQuery(" in source
    assert "QdrantClient(" not in source
    assert ".upsert(" not in source
    assert "projection_port.project(" not in source
    assert "put_object(" not in source
    assert "put_revision(" not in source
    assert "Scheduler(" not in source
    assert "finalize_love_memory_evidence_liaison_synthesis(" not in source
    assert "global_synthesis_created" in source
