from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import context.github_research_love_sql_persistence_0287 as module
from context.context_revision_sql_authority_0287 import (
    CONTEXT_REVISION_SCHEMA,
    ContextRevision,
)
from context.github_research_love_sql_persistence_0287 import (
    build_github_research_love_sql_persistence_plan,
    execute_github_research_love_sql_persistence,
    inspect_github_research_love_sql_persistence,
)
from context.github_research_love_first_visit_dispatch_0287 import (
    SCHEMA as FIRST_SCHEMA,
)
from context.github_research_love_second_visit_dispatch_0287 import (
    SCHEMA as SECOND_SCHEMA,
)


class WriteResult:
    def __init__(self, *, inserted: bool, replay: bool) -> None:
        self.inserted = inserted
        self.idempotent_replay = replay


class MemoryStore:
    def __init__(self, parent: ContextRevision) -> None:
        self.objects: dict[str, object] = {}
        self.artifacts: dict[str, object] = {}
        self.revisions: dict[str, object] = {
            parent.revision_ref: parent,
        }

    def get_object(self, ref: str):
        return self.objects.get(ref)

    def put_object(self, item):
        return self._put(self.objects, item.object_ref, item)

    def get_artifact(self, ref: str):
        return self.artifacts.get(ref)

    def put_artifact(self, item):
        return self._put(self.artifacts, item.artifact_ref, item)

    def get_revision(self, ref: str):
        return self.revisions.get(ref)

    def put_revision(self, item):
        return self._put(self.revisions, item.revision_ref, item)

    @staticmethod
    def _put(target, ref, item):
        existing = target.get(ref)
        if existing is None:
            target[ref] = item
            return WriteResult(inserted=True, replay=False)
        if existing.to_mapping() == item.to_mapping():
            return WriteResult(inserted=False, replay=True)
        raise RuntimeError("immutable collision")


def _parent() -> ContextRevision:
    return ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref="context-revision:love-base",
        context_ref="context:love",
        parent_revision_refs=(),
        memberships=(),
        validation_status="accepted",
        significance="minor",
        created_at="2026-07-18T00:00:00Z",
    )


def _result(
    *,
    visit_ref: str,
    specialist_ref: str,
    laboratory_ref: str,
    output_contract_ref: str,
    analysis_ref: str,
    machine_schema: str,
    parent_visit_ref: str | None,
) -> dict[str, object]:
    return {
        "schema": "missipy.laboratory.visit_result.v1",
        "visit_ref": visit_ref,
        "laboratory_ref": laboratory_ref,
        "specialist_ref": specialist_ref,
        "status": "completed",
        "output_contract_ref": output_contract_ref,
        "machine_result": {
            "schema": machine_schema,
            "analysis_ref": analysis_ref,
            "specialist_ref": specialist_ref,
            "contribution_kind": "domain_analysis",
        },
        "human_representation": f"Analyse {analysis_ref}",
        "confidence": 0.8,
        "evidence_refs": ["artifact:source"],
        "assumptions": [],
        "requested_context_refs": [],
        "requested_specialist_refs": [],
        "requested_laboratory_refs": [],
        "followup_request_refs": [],
        "provenance_refs": ["ctx:github-research-test"],
        "conversation_ref": "laboratory-conversation:test",
        "parent_visit_ref": parent_visit_ref,
    }


def _first_dispatch() -> dict[str, object]:
    specialist = "specialist:love-concept-affect-analyst"
    laboratory = "laboratory:love-studies-local"
    task = {
        "task_ref": "specialist-task:love-first-test",
        "expected_output_contract_ref": "contract:love.concept_affect_analysis.v1",
    }
    visit = {
        "visit_ref": "laboratory-visit:love-first-test",
        "specialist_ref": specialist,
        "laboratory_ref": laboratory,
    }
    result = _result(
        visit_ref=visit["visit_ref"],
        specialist_ref=specialist,
        laboratory_ref=laboratory,
        output_contract_ref=task["expected_output_contract_ref"],
        analysis_ref="love-analysis:concept-test",
        machine_schema="missipy.love.concept_affect_analysis.v1",
        parent_visit_ref=None,
    )
    return {
        "schema": FIRST_SCHEMA,
        "valid": True,
        "status": "first-specialist-completed",
        "work_package_ref": "research-work-package:test",
        "surface": {
            "first_task": task,
            "first_visit": visit,
        },
        "scheduler_receipt": {
            "execution": {
                "specialist_stage": "first_analysis",
                "result_valid": True,
                "result": result,
            }
        },
    }


def _second_dispatch() -> dict[str, object]:
    specialist = "specialist:love-relational-dynamics-analyst"
    laboratory = "laboratory:love-studies-local"
    task = {
        "task_ref": "specialist-task:love-second-test",
        "expected_output_contract_ref": (
            "contract:love.relational_dynamics_analysis.v1"
        ),
    }
    visit = {
        "visit_ref": "laboratory-visit:love-second-test",
        "parent_visit_ref": "laboratory-visit:love-first-test",
        "specialist_ref": specialist,
        "laboratory_ref": laboratory,
    }
    result = _result(
        visit_ref=visit["visit_ref"],
        specialist_ref=specialist,
        laboratory_ref=laboratory,
        output_contract_ref=task["expected_output_contract_ref"],
        analysis_ref="love-analysis:relational-test",
        machine_schema="missipy.love.relational_dynamics_analysis.v1",
        parent_visit_ref=visit["parent_visit_ref"],
    )
    return {
        "schema": SECOND_SCHEMA,
        "valid": True,
        "status": "second-specialist-completed",
        "work_package_ref": "research-work-package:test",
        "first_visit_ref": "laboratory-visit:love-first-test",
        "preparation": {
            "second_task": task,
            "second_visit": visit,
        },
        "scheduler_receipt": {
            "execution": {
                "specialist_stage": "second_analysis",
                "result_valid": True,
                "result": result,
            }
        },
    }


def _ports(store: MemoryStore):
    return SimpleNamespace(
        authority_store=store,
        base_revision_ref="context-revision:love-base",
    )


def test_plan_keeps_two_objects_and_artifacts_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MemoryStore(_parent())
    ports = _ports(store)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    plan = build_github_research_love_sql_persistence_plan(
        runtime_ports=ports,  # type: ignore[arg-type]
        first_dispatch=_first_dispatch(),
        second_dispatch=_second_dispatch(),
        created_at="2026-07-18T12:00:00Z",
    )

    assert plan.first_object.object_ref != plan.second_object.object_ref
    assert plan.first_artifact.artifact_ref != plan.second_artifact.artifact_ref
    assert len(plan.revision.memberships) == 4
    assert plan.revision.parent_revision_refs == (
        "context-revision:love-base",
    )
    assert plan.revision.context_ref == "context:love"
    assert plan.revision.metadata["global_synthesis_created"] is False


def test_execute_writes_revision_last_and_replays_idempotently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MemoryStore(_parent())
    ports = _ports(store)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    plan = build_github_research_love_sql_persistence_plan(
        runtime_ports=ports,  # type: ignore[arg-type]
        first_dispatch=_first_dispatch(),
        second_dispatch=_second_dispatch(),
        created_at="2026-07-18T12:00:00Z",
    )

    readiness = inspect_github_research_love_sql_persistence(store, plan)
    first = execute_github_research_love_sql_persistence(store, plan)
    second = execute_github_research_love_sql_persistence(store, plan)

    assert readiness.ready is True
    assert first.action == "created"
    assert second.action == "replay"
    assert first.readback_verified is True
    assert store.get_revision(plan.revision.revision_ref) == plan.revision
    assert first.to_mapping()["boundaries"]["qdrant_write_performed"] is False
    assert first.to_mapping()["boundaries"]["global_synthesis_created"] is False


def test_collision_is_rejected_before_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MemoryStore(_parent())
    ports = _ports(store)
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    plan = build_github_research_love_sql_persistence_plan(
        runtime_ports=ports,  # type: ignore[arg-type]
        first_dispatch=_first_dispatch(),
        second_dispatch=_second_dispatch(),
        created_at="2026-07-18T12:00:00Z",
    )
    store.objects[plan.first_object.object_ref] = SimpleNamespace(
        to_mapping=lambda: {"collision": True}
    )

    readiness = inspect_github_research_love_sql_persistence(store, plan)

    assert readiness.ready is False
    assert "immutable first_object collision" in readiness.issues


def test_module_reuses_authority_store_and_does_not_project_or_synthesize() -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "put_object(" in source
    assert "put_artifact(" in source
    assert "put_revision(" in source
    assert "get_object(" in source
    assert "get_artifact(" in source
    assert "get_revision(" in source
    assert "psycopg" not in source
    assert "CREATE TABLE" not in source
    assert "projection_port" not in source
    assert "from qdrant_client" not in source
    assert "import qdrant_client" not in source
    assert "QdrantClient(" not in source
    assert ".upsert(" not in source
    assert ".query_points(" not in source
    assert '"qdrant_write_performed": False' in source
    assert "global_synthesis_created" in source
    assert "Scheduler(" not in source
