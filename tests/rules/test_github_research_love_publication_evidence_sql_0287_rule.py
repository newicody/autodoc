from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import context.github_research_love_publication_evidence_sql_0287 as module
from context.context_revision_sql_authority_0287 import (
    CONTEXT_REVISION_SCHEMA,
    ContextRevision,
)
from context.github_research_love_final_deliverable_sql_0287 import (
    RECEIPT_SCHEMA as FINAL_SQL_RECEIPT_SCHEMA,
    RESULT_SCHEMA as FINAL_SQL_RESULT_SCHEMA,
)
from context.github_research_love_final_remote_publication_0287 import (
    RESULT_SCHEMA as FINAL_REMOTE_RESULT_SCHEMA,
)
from context.github_research_love_publication_evidence_sql_0287 import (
    GitHubResearchLovePublicationEvidenceCommand,
    build_github_research_love_publication_evidence_plan,
    execute_github_research_love_publication_evidence,
    inspect_github_research_love_publication_evidence,
)
from context.love_final_deliverable_remote_publication_0287 import (
    LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_RESULT_SCHEMA,
)


class WriteResult:
    def __init__(self, inserted: bool, replay: bool) -> None:
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
            return WriteResult(True, False)
        if existing.to_mapping() == item.to_mapping():
            return WriteResult(False, True)
        raise RuntimeError("immutable collision")


def _parent() -> ContextRevision:
    return ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref="context-revision:github-love-final-test",
        context_ref="context:love",
        parent_revision_refs=("context-revision:github-love-pair",),
        memberships=(),
        validation_status="accepted",
        significance="material",
        created_at="2026-07-18T12:00:00Z",
    )


def _final() -> dict[str, object]:
    return {
        "schema": FINAL_SQL_RESULT_SCHEMA,
        "valid": True,
        "status": "persisted",
        "plan": {
            "plan_digest": "sha256:" + "1" * 64,
            "work_package_ref": "research-work-package:test",
        },
        "receipt": {
            "schema": FINAL_SQL_RECEIPT_SCHEMA,
            "plan_digest": "sha256:" + "1" * 64,
            "packet_ref": "publication:final-synthesis:test",
            "target_ref": "github:newicody/projects#15",
            "authority_object_ref": "context-object:github-love-final-test",
            "artifact_ref": "artifact:github-love-final-test",
            "revision_ref": "context-revision:github-love-final-test",
            "readback_verified": True,
        },
    }


def _publication() -> dict[str, object]:
    plan_digest = "sha256:" + "2" * 64
    return {
        "schema": FINAL_REMOTE_RESULT_SCHEMA,
        "valid": True,
        "status": "published",
        "issues": [],
        "plan_digest": plan_digest,
        "lineage_digest": "sha256:" + "3" * 64,
        "final_sql_revision_ref": "context-revision:github-love-final-test",
        "final_authority_object_ref": "context-object:github-love-final-test",
        "final_artifact_ref": "artifact:github-love-final-test",
        "final_packet_ref": "publication:final-synthesis:test",
        "publication_plan": {
            "schema": "missipy.love.final_deliverable_publication_plan.v1",
            "repository": "newicody/projects",
            "issue_number": 15,
            "marker": "<!-- autodoc:final-deliverable:test -->",
            "body_sha256": "sha256:" + "4" * 64,
            "plan_digest": plan_digest,
        },
        "remote_publication": {
            "schema": (
                LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_RESULT_SCHEMA
            ),
            "valid": True,
            "mode": "execute",
            "action": "created_and_projected",
            "issues": [],
            "plan_digest": plan_digest,
            "issue_action": "create",
            "project_action": "update",
            "issue_comment_id": 123,
            "issue_comment_url": (
                "https://github.com/newicody/projects/issues/15"
                "#issuecomment-123"
            ),
            "project_snapshot": {
                "project_item_id": "PVTI_test",
                "field_ref": "PVTF_test",
                "field_name": "Résumé",
                "value": "Livrable final prêt",
            },
            "readback": {
                "schema": (
                    "missipy.love.final_deliverable_publication_readback.v1"
                ),
                "valid": True,
                "issues": [],
            },
            "issue_mutation_performed": True,
            "project_mutation_performed": True,
            "remote_mutation_performed": True,
            "partial_execution": False,
        },
    }


def _command(store: MemoryStore):
    return GitHubResearchLovePublicationEvidenceCommand(
        runtime_ports=SimpleNamespace(authority_store=store),  # type: ignore[arg-type]
        final_deliverable=_final(),
        remote_publication=_publication(),
        closed_at="2026-07-18T13:00:00Z",
    )


def test_plan_persists_minimal_remote_proof_and_closes_child_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MemoryStore(_parent())
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    plan = build_github_research_love_publication_evidence_plan(
        _command(store)
    )
    evidence = json.loads(plan.authority_object.body)

    assert evidence["issue_comment_id"] == 123
    assert evidence["project_item_id"] == "PVTI_test"
    assert evidence["exact_readback_valid"] is True
    assert evidence["cycle_status"] == "closed"
    assert "body" not in evidence
    assert plan.revision.parent_revision_refs == (
        "context-revision:github-love-final-test",
    )
    assert plan.revision.metadata["cycle_status"] == "closed"
    assert plan.revision.metadata[
        "remote_publication_reexecuted"
    ] is False


def test_execute_is_created_then_idempotent_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MemoryStore(_parent())
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    plan = build_github_research_love_publication_evidence_plan(
        _command(store)
    )

    readiness = inspect_github_research_love_publication_evidence(
        store,
        plan,
    )
    first = execute_github_research_love_publication_evidence(
        store,
        plan,
    )
    second = execute_github_research_love_publication_evidence(
        store,
        plan,
    )

    assert readiness.ready is True
    assert first.action == "created"
    assert second.action == "replay"
    assert first.readback_verified is True
    assert first.to_mapping()["cycle_status"] == "closed"
    assert first.to_mapping()["boundaries"][
        "remote_publication_reexecuted"
    ] is False


def test_preview_or_partial_remote_result_cannot_close_cycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MemoryStore(_parent())
    broken = _publication()
    remote = dict(broken["remote_publication"])
    remote["mode"] = "preview"
    broken["remote_publication"] = remote
    command = GitHubResearchLovePublicationEvidenceCommand(
        runtime_ports=SimpleNamespace(authority_store=store),  # type: ignore[arg-type]
        final_deliverable=_final(),
        remote_publication=broken,
        closed_at="2026-07-18T13:00:00Z",
    )
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    with pytest.raises(
        module.GitHubResearchLovePublicationEvidenceError,
        match="valid execute",
    ):
        build_github_research_love_publication_evidence_plan(command)


def test_module_only_persists_sql_proof_and_never_republishes() -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "put_object(" in source
    assert "put_artifact(" in source
    assert "put_revision(" in source
    assert "execute_love_final_deliverable_remote_publication(" not in source
    assert "create_comment(" not in source
    assert "update_field(" not in source
    assert "GitHubCliFinalDeliverablePublicationAdapter(" not in source
    assert "QdrantClient(" not in source
    assert "projection_port.project(" not in source
    assert "Scheduler(" not in source
