from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import context.github_research_love_two_qdrant_projections_0287 as module
from context.github_research_love_two_qdrant_projections_0287 import (
    GitHubResearchLoveTwoProjectionCommand,
    build_github_research_love_two_projection_plan,
    execute_github_research_love_two_projections,
)
from context.github_research_love_sql_persistence_0287 import (
    RECEIPT_SCHEMA as SQL_RECEIPT_SCHEMA,
    RESULT_SCHEMA as SQL_RESULT_SCHEMA,
)


class Object:
    def __init__(self, ref: str, specialist: str) -> None:
        self.object_ref = ref
        self.body = "{}"
        self.content_digest = "sha256:" + "a" * 64
        self.metadata = {
            "specialist_ref": specialist,
            "laboratory_ref": "laboratory:love-studies-local",
        }


class Store:
    def __init__(self) -> None:
        self.objects = {
            "context-object:first": Object(
                "context-object:first",
                "specialist:love-concept-affect-analyst",
            ),
            "context-object:second": Object(
                "context-object:second",
                "specialist:love-relational-dynamics-analyst",
            ),
        }
        self.revision = SimpleNamespace(
            revision_ref="context-revision:pair",
            memberships=(),
        )

    def get_object(self, ref: str):
        return self.objects.get(ref)

    def get_revision(self, ref: str):
        return self.revision if ref == self.revision.revision_ref else None


def _sql_result() -> dict[str, object]:
    return {
        "schema": SQL_RESULT_SCHEMA,
        "valid": True,
        "status": "persisted",
        "plan": {
            "plan_digest": "sha256:" + "b" * 64,
        },
        "receipt": {
            "schema": SQL_RECEIPT_SCHEMA,
            "plan_digest": "sha256:" + "b" * 64,
            "work_package_ref": "research-work-package:test",
            "first_object_ref": "context-object:first",
            "second_object_ref": "context-object:second",
            "first_artifact_ref": "artifact:first",
            "second_artifact_ref": "artifact:second",
            "revision_ref": "context-revision:pair",
            "readback_verified": True,
            "action": "created",
        },
    }


def _ports(store: Store) -> SimpleNamespace:
    return SimpleNamespace(
        authority_store=store,
        projection_port=object(),
        attestation=SimpleNamespace(
            embedding_dimension=384,
            qdrant_collection="autodoc-love",
            model_ref="openvino.embedding.e5-small",
            model_revision="multilingual-e5-small",
        ),
    )


def _command(store: Store) -> GitHubResearchLoveTwoProjectionCommand:
    return GitHubResearchLoveTwoProjectionCommand(
        runtime_ports=_ports(store),  # type: ignore[arg-type]
        sql_persistence=_sql_result(),
        reference_point_reader=SimpleNamespace(
            read_named_reference_point=lambda **kwargs: None
        ),  # type: ignore[arg-type]
        branch_ref="branch:github-research",
        project_ref="project:github-research",
        conversation_ref="conversation:github-research",
        security_scope="security:research-local",
        dense_vector_name="dense",
        sparse_vector_name="sparse",
        projected_at="2026-07-18T12:00:00Z",
    )


def test_plan_keeps_two_sql_objects_and_two_probe_plans_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = Store()
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    plan = build_github_research_love_two_projection_plan(_command(store))

    assert plan.first.request.object_ref == "context-object:first"
    assert plan.second.request.object_ref == "context-object:second"
    assert plan.first.request.object_ref != plan.second.request.object_ref
    assert plan.first.dimension == 384
    assert plan.second.dimension == 384
    assert plan.first.collection_name == "autodoc-love"
    assert plan.second.collection_name == "autodoc-love"
    assert plan.first.plan_digest != plan.second.plan_digest


@pytest.mark.asyncio
async def test_execution_reuses_live_probe_twice_without_synthesis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = Store()
    command = _command(store)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    plan = build_github_research_love_two_projection_plan(command)
    monkeypatch.setattr(
        module,
        "inspect_github_research_love_two_projections",
        lambda **kwargs: SimpleNamespace(ready=True, issues=()),
    )
    calls: list[str] = []

    async def fake_execute(store, projector, reader, probe_plan, gate):
        calls.append(probe_plan.request.object_ref)
        return SimpleNamespace(
            to_mapping=lambda: {
                "schema": "missipy.love.live_qdrant_projection_receipt.v1",
                "plan_digest": probe_plan.plan_digest,
                "projection_ref": (
                    "projection:" + probe_plan.request.object_ref.split(":")[-1]
                ),
                "point_id": (
                    "point:" + probe_plan.request.object_ref.split(":")[-1]
                ),
                "object_ref": probe_plan.request.object_ref,
                "revision_ref": probe_plan.request.revision_ref,
                "source_content_digest": "sha256:" + "a" * 64,
                "sql_projection": {
                    "inserted": True,
                    "idempotent_replay": False,
                },
                "qdrant_payload": {
                    "sql_ref": probe_plan.request.object_ref,
                    "source_ref": probe_plan.request.object_ref,
                },
                "checks": {
                    "sql_source_rehydrated": True,
                },
                "boundaries": {
                    "qdrant_vectors_serialized": False,
                    "authoritative_body_serialized": False,
                },
            }
        )

    monkeypatch.setattr(
        module,
        "execute_love_live_projection_probe",
        fake_execute,
    )

    receipt = await execute_github_research_love_two_projections(
        command,
        plan,
    )
    mapping = receipt.to_mapping()

    assert calls == ["context-object:first", "context-object:second"]
    assert receipt.first["object_ref"] != receipt.second["object_ref"]
    assert mapping["checks"]["two_qdrant_points_written"] is True
    assert mapping["boundaries"]["embedding_dimension"] == 384
    assert mapping["boundaries"]["global_synthesis_created"] is False


def test_wrong_embedding_dimension_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = Store()
    command = _command(store)
    command.runtime_ports.attestation.embedding_dimension = 385
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    with pytest.raises(
        module.GitHubResearchLoveTwoProjectionError,
        match="384",
    ):
        build_github_research_love_two_projection_plan(command)


def test_module_reuses_existing_probe_and_serializes_no_vectors_or_body() -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "build_love_live_projection_probe_plan(" in source
    assert "inspect_love_live_projection_probe(" in source
    assert "execute_love_live_projection_probe(" in source
    assert "QdrantClient(" not in source
    assert "from qdrant_client" not in source
    assert "import openvino" not in source
    assert "Scheduler(" not in source
    assert "global_synthesis_created" in source
    assert "qdrant_vectors_serialized" in source
    assert "authoritative_body_serialized" in source
