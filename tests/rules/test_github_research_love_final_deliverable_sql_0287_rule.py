from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import context.github_research_love_final_deliverable_sql_0287 as module
from context.context_revision_sql_authority_0287 import (
    CONTEXT_REVISION_SCHEMA,
    ContextRevision,
)
from context.github_research_love_final_deliverable_sql_0287 import (
    GitHubResearchLoveFinalDeliverableCommand,
    build_github_research_love_final_deliverable_plan,
    execute_github_research_love_final_deliverable,
    inspect_github_research_love_final_deliverable,
)
from context.github_research_love_liaison_synthesis_0287 import (
    GitHubResearchLoveLiaisonSynthesisPlan,
    GitHubResearchLoveLiaisonSynthesisResult,
)
from context.github_research_love_sql_persistence_0287 import (
    RECEIPT_SCHEMA as ANALYSIS_SQL_RECEIPT_SCHEMA,
    RESULT_SCHEMA as ANALYSIS_SQL_RESULT_SCHEMA,
)
from context.specialist_liaison_synthesis import (
    SpecialistLiaisonPolicy,
    SpecialistOutputFragment,
    build_specialist_liaison_synthesis,
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
        revision_ref="context-revision:github-love-pair",
        context_ref="context:love",
        parent_revision_refs=("context-revision:love-base",),
        memberships=(),
        validation_status="accepted",
        significance="minor",
        created_at="2026-07-18T11:00:00Z",
    )


def _liaison() -> GitHubResearchLoveLiaisonSynthesisResult:
    fragments = (
        SpecialistOutputFragment(
            fragment_ref="specialist-fragment:first",
            result_ref="specialist:love-concept-affect-analyst",
            output_kind="domain_analysis",
            title="Concepts et affects",
            body="Analyse conceptuelle.",
            evidence_refs=("sql:context-object:first",),
            context_delta_refs=("sql:context-object:first",),
            depth="deep",
        ),
        SpecialistOutputFragment(
            fragment_ref="specialist-fragment:second",
            result_ref="specialist:love-relational-dynamics-analyst",
            output_kind="domain_analysis",
            title="Dynamiques relationnelles",
            body="Analyse relationnelle.",
            evidence_refs=("sql:context-object:second",),
            context_delta_refs=("sql:context-object:second",),
            depth="deep",
        ),
        SpecialistOutputFragment(
            fragment_ref="specialist-fragment:audit",
            result_ref="ctx-result:love-evidence-mutualization",
            output_kind="evidence_mutualization",
            title="Convergences et limites",
            body="Comparaison des deux analyses.",
            evidence_refs=(
                "sql:context-object:first",
                "sql:context-object:second",
            ),
            context_delta_refs=(
                "sql:context-object:first",
                "sql:context-object:second",
            ),
            depth="audit",
        ),
    )
    synthesis = build_specialist_liaison_synthesis(
        request_ref="research-work-package:test",
        title="Synthèse de liaison de l’étude",
        fragments=fragments,
        policy=SpecialistLiaisonPolicy(
            max_fragments=3,
            max_section_chars=8_192,
            hide_specialist_provenance_from_user=True,
        ),
    )
    plan = GitHubResearchLoveLiaisonSynthesisPlan(
        schema=(
            "missipy.github.research_love_liaison_synthesis_plan.v1"
        ),
        work_package_ref="research-work-package:test",
        recall_plan_digest="sha256:" + "1" * 64,
        first_sql_ref="context-object:first",
        second_sql_ref="context-object:second",
        first_analysis_ref="love-analysis:first",
        second_analysis_ref="love-analysis:second",
        study_ref="love-study:test",
        title="Synthèse de liaison de l’étude",
    )
    return GitHubResearchLoveLiaisonSynthesisResult(
        schema=(
            "missipy.github.research_love_liaison_synthesis_result.v1"
        ),
        valid=True,
        status="synthesized",
        issues=(),
        plan=plan,
        mutualization=SimpleNamespace(to_mapping=lambda: {}),
        fragments=fragments,
        synthesis=synthesis,
    )


def _analysis_sql() -> dict[str, object]:
    return {
        "schema": ANALYSIS_SQL_RESULT_SCHEMA,
        "valid": True,
        "status": "persisted",
        "plan": {
            "plan_digest": "sha256:" + "2" * 64,
        },
        "receipt": {
            "schema": ANALYSIS_SQL_RECEIPT_SCHEMA,
            "work_package_ref": "research-work-package:test",
            "first_object_ref": "context-object:first",
            "second_object_ref": "context-object:second",
            "revision_ref": "context-revision:github-love-pair",
            "readback_verified": True,
        },
    }


def _ports(store: MemoryStore):
    return SimpleNamespace(authority_store=store)


def _command(store: MemoryStore):
    return GitHubResearchLoveFinalDeliverableCommand(
        runtime_ports=_ports(store),  # type: ignore[arg-type]
        liaison=_liaison(),
        analysis_sql_persistence=_analysis_sql(),
        target_ref="github:newicody/projects#15",
        created_at="2026-07-18T12:00:00Z",
    )


def test_plan_reuses_final_packet_builder_and_keeps_sources_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MemoryStore(_parent())
    command = _command(store)
    source_synthesis = command.liaison.synthesis
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    plan = build_github_research_love_final_deliverable_plan(command)
    packet_mapping = plan.packet.to_mapping()
    stored_packet = json.loads(plan.authority_object.body)

    assert source_synthesis is not None
    assert source_synthesis.final_publication_ready is False
    assert plan.packet.synthesis.final_publication_ready is True
    assert plan.packet.synthesis.provenance_hidden is True
    assert packet_mapping["target_ref"] == "github:newicody/projects#15"
    assert stored_packet["packet_ref"] == plan.packet.packet_ref
    assert stored_packet["body"] == plan.packet.body
    assert plan.revision.parent_revision_refs == (
        "context-revision:github-love-pair",
    )
    assert len(plan.revision.memberships) == 2
    assert plan.revision.metadata["source_analyses_modified"] is False
    assert plan.revision.metadata["source_liaison_modified"] is False


def test_execute_is_created_then_idempotent_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MemoryStore(_parent())
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )
    plan = build_github_research_love_final_deliverable_plan(
        _command(store)
    )

    readiness = inspect_github_research_love_final_deliverable(
        store,
        plan,
    )
    first = execute_github_research_love_final_deliverable(
        store,
        plan,
    )
    second = execute_github_research_love_final_deliverable(
        store,
        plan,
    )

    assert readiness.ready is True
    assert first.action == "created"
    assert second.action == "replay"
    assert first.readback_verified is True
    assert store.get_revision(plan.revision.revision_ref) == plan.revision
    assert first.to_mapping()["boundaries"][
        "remote_publication_performed"
    ] is False
    assert first.to_mapping()["boundaries"][
        "projectv2_mutation_performed"
    ] is False


def test_analysis_lineage_mismatch_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = MemoryStore(_parent())
    command = _command(store)
    broken = _analysis_sql()
    receipt = dict(broken["receipt"])
    receipt["second_object_ref"] = "context-object:other"
    broken["receipt"] = receipt
    command = GitHubResearchLoveFinalDeliverableCommand(
        runtime_ports=command.runtime_ports,
        liaison=command.liaison,
        analysis_sql_persistence=broken,
        target_ref=command.target_ref,
        created_at=command.created_at,
    )
    monkeypatch.setattr(
        module,
        "validate_imported_actions_runtime_ports",
        lambda value: value,
    )

    with pytest.raises(
        module.GitHubResearchLoveFinalDeliverableError,
        match="second analysis SQL reference mismatch",
    ):
        build_github_research_love_final_deliverable_plan(command)


def test_module_reuses_existing_packet_and_only_writes_sql_authority() -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "build_final_synthesis_packet(" in source
    assert "put_object(" in source
    assert "put_artifact(" in source
    assert "put_revision(" in source
    assert "QdrantClient(" not in source
    assert ".upsert(" not in source
    assert "projection_port.project(" not in source
    assert "Scheduler(" not in source
    assert "github_mutation_performed" in source
    assert "remote_publication_performed" in source
