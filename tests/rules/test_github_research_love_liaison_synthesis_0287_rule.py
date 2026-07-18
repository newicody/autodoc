from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from context.github_research_love_liaison_synthesis_0287 import (
    GitHubResearchLoveLiaisonSynthesisCommand,
    build_github_research_love_liaison_synthesis,
)
from context.github_research_love_two_analysis_recall_0287 import (
    GitHubResearchLoveTwoAnalysisRecallPlan,
    GitHubResearchLoveTwoAnalysisRecallResult,
)
from context.hybrid_retrieval_sql_rehydration_0287 import (
    HYBRID_FILTER_SCHEMA,
    HYBRID_QUERY_SCHEMA,
    REHYDRATED_AUTHORITY_ITEM_SCHEMA,
    HybridRetrievalFilter,
    HybridRetrievalQuery,
    RehydratedAuthorityItem,
)
from context.love_study_contracts_0287 import (
    LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA,
    LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
)


def _finding(ref: str, dimension: str, statement: str) -> dict[str, object]:
    return {
        "schema": "missipy.love.analysis_finding.v1",
        "finding_ref": ref,
        "dimension": dimension,
        "statement": statement,
        "status": "observed",
        "evidence_refs": ["artifact:source"],
        "confidence": 0.8,
        "uncertainty": None,
    }


def _visit_body(machine: dict[str, object], *, specialist: str) -> str:
    value = {
        "schema": "missipy.laboratory.visit_result.v1",
        "visit_ref": (
            "laboratory-visit:first"
            if machine["schema"] == LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA
            else "laboratory-visit:second"
        ),
        "laboratory_ref": "laboratory:love-studies-local",
        "specialist_ref": specialist,
        "status": "completed",
        "output_contract_ref": "contract:analysis",
        "machine_result": machine,
        "human_representation": f"Représentation {machine['analysis_ref']}",
        "confidence": 0.8,
        "evidence_refs": ["artifact:source"],
        "assumptions": [],
        "requested_context_refs": [],
        "requested_specialist_refs": [],
        "requested_laboratory_refs": [],
        "followup_request_refs": [],
        "provenance_refs": ["ctx:github-research-test"],
        "conversation_ref": "laboratory-conversation:test",
        "parent_visit_ref": None,
    }
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _analyses() -> tuple[dict[str, object], dict[str, object]]:
    first = {
        "schema": LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
        "analysis_ref": "love-analysis:first",
        "study_ref": "love-study:test",
        "specialist_ref": LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        "context_revision_ref": "context-revision:base",
        "findings": [
            _finding(
                "love-finding:first",
                "reciprocity",
                "La confiance apparaît liée à la réciprocité.",
            )
        ],
        "concepts": ["reciprocity", "attachment"],
        "affects": ["trust"],
        "uncertainties": ["Le contexte temporel reste incomplet."],
        "contradictions": [],
        "limitations": ["Analyse limitée au texte fourni."],
        "recommendations": ["Clarifier les attentes explicites."],
        "evidence_refs": ["artifact:source"],
        "artifact_refs": ["artifact:first"],
        "local_synthesis": "La confiance dépend de signes réciproques.",
        "contribution_kind": "domain_analysis",
    }
    second = {
        "schema": LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA,
        "analysis_ref": "love-analysis:second",
        "study_ref": "love-study:test",
        "specialist_ref": LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        "context_revision_ref": "context-revision:base",
        "findings": [
            _finding(
                "love-finding:second",
                "reciprocity",
                "Une asymétrie de réciprocité est observable.",
            )
        ],
        "dynamics": ["reciprocity", "asymmetry"],
        "source_analysis_refs": ["love-analysis:first"],
        "uncertainties": ["Les intentions ne sont pas disponibles."],
        "contradictions": ["Confiance déclarée mais réciprocité incertaine."],
        "limitations": ["Aucune intention n’est inférée."],
        "recommendations": ["Définir les limites et attentes."],
        "evidence_refs": ["artifact:source"],
        "artifact_refs": ["artifact:second"],
        "local_synthesis": "La relation présente une asymétrie à clarifier.",
        "contribution_kind": "domain_analysis",
    }
    return first, second


def _item(sql_ref: str, body: str, title: str) -> RehydratedAuthorityItem:
    digest = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
    return RehydratedAuthorityItem(
        schema=REHYDRATED_AUTHORITY_ITEM_SCHEMA,
        sql_ref=sql_ref,
        authority_kind="context_object",
        content_digest=digest,
        title=title,
        body=body,
        storage_ref="",
        media_type="application/json",
    )


def _recall(
    *,
    second_study_ref: str = "love-study:test",
) -> GitHubResearchLoveTwoAnalysisRecallResult:
    first, second = _analyses()
    second["study_ref"] = second_study_ref
    first_item = _item(
        "context-object:first",
        _visit_body(
            first,
            specialist=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        ),
        "Première analyse",
    )
    second_item = _item(
        "context-object:second",
        _visit_body(
            second,
            specialist=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        ),
        "Seconde analyse",
    )
    filter_ = HybridRetrievalFilter(
        schema=HYBRID_FILTER_SCHEMA,
        context_revision_ref="context-revision:pair",
        branch_ref="branch:github",
        project_ref="project:github",
        security_scope="security:local",
    )
    query = HybridRetrievalQuery(
        schema=HYBRID_QUERY_SCHEMA,
        query_ref="retrieval-query:github-love-test",
        task_ref="task:github-love-test",
        query_text="Relier les deux analyses.",
        filter=filter_,
        final_limit=2,
        group_by="source_ref",
    )
    plan = GitHubResearchLoveTwoAnalysisRecallPlan(
        schema="missipy.github.research_love_two_analysis_recall_plan.v1",
        work_package_ref="research-work-package:test",
        sql_persistence_plan_digest="sha256:" + "1" * 64,
        projection_pair_plan_digest="sha256:" + "2" * 64,
        expected_sql_refs=(
            "context-object:first",
            "context-object:second",
        ),
        query=query,
    )
    return GitHubResearchLoveTwoAnalysisRecallResult(
        schema="missipy.github.research_love_two_analysis_recall_result.v1",
        valid=True,
        status="recalled",
        issues=(),
        plan=plan,
        retrieval_execution=SimpleNamespace(),
        items_by_sql_ref={
            first_item.sql_ref: first_item,
            second_item.sql_ref: second_item,
        },
    )


def test_builds_existing_liaison_with_two_sources_and_one_audit_fragment() -> None:
    result = build_github_research_love_liaison_synthesis(
        GitHubResearchLoveLiaisonSynthesisCommand(
            recall=_recall(),
        )
    )
    mapping = result.to_mapping()

    assert result.valid is True
    assert result.status == "synthesized"
    assert result.mutualization is not None
    assert result.mutualization.convergences == ("reciprocity",)
    assert len(result.fragments) == 3
    assert result.synthesis is not None
    assert result.synthesis.final_publication_ready is False
    assert result.synthesis.provenance_hidden is True
    assert len(result.synthesis.sections) == 3
    assert mapping["boundaries"]["source_authority_objects_modified"] is False
    assert mapping["boundaries"]["final_publication_packet_created"] is False
    assert mapping["boundaries"]["sql_write_performed"] is False
    assert mapping["boundaries"]["qdrant_write_performed"] is False


def test_source_json_bodies_are_not_serialized_in_result_mapping() -> None:
    recall = _recall()
    result = build_github_research_love_liaison_synthesis(
        GitHubResearchLoveLiaisonSynthesisCommand(recall=recall)
    )
    encoded = json.dumps(
        result.to_mapping(),
        ensure_ascii=False,
        sort_keys=True,
    )

    assert recall.first_item.body not in encoded
    assert recall.second_item.body not in encoded
    assert "source_authority_bodies_serialized" in encoded


def test_mismatched_study_refs_fail_closed() -> None:
    result = build_github_research_love_liaison_synthesis(
        GitHubResearchLoveLiaisonSynthesisCommand(
            recall=_recall(second_study_ref="love-study:other"),
        )
    )

    assert result.valid is False
    assert result.status == "failed"
    assert "study_ref mismatch" in result.issues[0]


def test_digest_mismatch_fails_closed() -> None:
    recall = _recall()
    first = recall.first_item
    broken = RehydratedAuthorityItem(
        schema=first.schema,
        sql_ref=first.sql_ref,
        authority_kind=first.authority_kind,
        content_digest="sha256:" + "0" * 64,
        title=first.title,
        body=first.body,
        storage_ref=first.storage_ref,
        media_type=first.media_type,
    )
    broken_recall = GitHubResearchLoveTwoAnalysisRecallResult(
        schema=recall.schema,
        valid=True,
        status="recalled",
        issues=(),
        plan=recall.plan,
        retrieval_execution=SimpleNamespace(),
        items_by_sql_ref={
            broken.sql_ref: broken,
            recall.second_item.sql_ref: recall.second_item,
        },
    )

    result = build_github_research_love_liaison_synthesis(
        GitHubResearchLoveLiaisonSynthesisCommand(recall=broken_recall)
    )

    assert result.valid is False
    assert "digest mismatch" in result.issues[0]


def test_module_reuses_existing_liaison_without_final_packet_or_writes() -> None:
    import context.github_research_love_liaison_synthesis_0287 as module

    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "LoveEvidenceMutualization(" in source
    assert "SpecialistOutputFragment(" in source
    assert "build_specialist_liaison_synthesis(" in source
    assert "build_final_synthesis_packet(" not in source
    assert "put_object(" not in source
    assert "put_revision(" not in source
    assert ".upsert(" not in source
    assert "projection_port.project(" not in source
    assert "Scheduler(" not in source
    assert "final_publication_ready" in source
