from __future__ import annotations

import pytest

from context.love_study_contracts_0287 import (
    LOVE_ANALYSIS_FINDING_SCHEMA,
    LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA,
    LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
    LOVE_STUDIES_LABORATORY_REF,
    LOVE_STUDY_PROTOTYPE_DEFINITION_SCHEMA,
    LOVE_STUDY_REQUEST_SCHEMA,
    LOVE_STUDY_RESULT_SCHEMA,
    LoveAnalysisFinding,
    LoveConceptAffectAnalysis,
    LoveRelationalDynamicsAnalysis,
    LoveStudyContractError,
    LoveStudyRequest,
    LoveStudyResult,
    build_love_study_prototype_definition,
)


def _request() -> LoveStudyRequest:
    return LoveStudyRequest(
        schema=LOVE_STUDY_REQUEST_SCHEMA,
        study_ref="love-study:issue-42",
        source_issue_ref="github-issue:newicody-projects-42",
        objective="Analyser les représentations de l'amour dans le texte.",
        subject_text="Une relation est décrite avec affection et incertitude.",
        constraints=("Ne pas inventer les intentions d'une personne absente.",),
        success_criteria=("Relier chaque constat à une preuve explicite.",),
        context_refs=("context-revision:love-r1",),
        evidence_refs=("artifact:issue-body-42",),
    )


def _finding(*, ref: str = "love-finding:affection") -> LoveAnalysisFinding:
    return LoveAnalysisFinding(
        schema=LOVE_ANALYSIS_FINDING_SCHEMA,
        finding_ref=ref,
        dimension="affection",
        statement="Le texte exprime une affection explicite.",
        status="observed",
        evidence_refs=("artifact:issue-body-42",),
        confidence=0.8,
    )


def _first_analysis() -> LoveConceptAffectAnalysis:
    return LoveConceptAffectAnalysis(
        schema=LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
        analysis_ref="love-analysis:concept-affect-42",
        study_ref="love-study:issue-42",
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        context_revision_ref="context-revision:love-r1",
        findings=(_finding(),),
        concepts=("affection", "engagement"),
        affects=("tendresse", "incertitude"),
        uncertainties=("Le point de vue de l'autre personne est absent.",),
        contradictions=(),
        limitations=("Analyse limitée au texte transmis.",),
        recommendations=("Demander une clarification explicite.",),
        evidence_refs=("artifact:issue-body-42",),
        artifact_refs=("artifact:concept-affect-42",),
    )


def test_request_keeps_authority_and_defers_global_synthesis() -> None:
    payload = _request().to_mapping()

    assert payload["request_authoritative"] is True
    assert payload["global_synthesis_created"] is False
    assert payload["scheduler_route_created"] is False
    assert payload["synthesis_policy"] == "liaison_after_domain_analyses"
    assert set(payload["requested_specialist_refs"]) == {
        LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
    }


def test_prototype_declares_disabled_native_laboratory_and_two_specialists() -> None:
    prototype = build_love_study_prototype_definition()
    payload = prototype.to_mapping()

    assert prototype.schema == LOVE_STUDY_PROTOTYPE_DEFINITION_SCHEMA
    assert prototype.laboratory.laboratory_ref == LOVE_STUDIES_LABORATORY_REF
    assert prototype.laboratory.provider_kind == "autodoc_native"
    assert prototype.laboratory.execution_boundary == "in_process"
    assert prototype.laboratory.availability == "declared"
    assert prototype.laboratory.enabled is False
    assert prototype.laboratory.network_allowed is False
    assert {item.descriptor.specialist_ref for item in prototype.specialists} == {
        LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
    }
    assert payload["provider_instantiated"] is False
    assert payload["task_handlers_attached"] is False
    assert payload["scheduler_registration_performed"] is False
    assert payload["openvino_runtime_loaded"] is False


def test_specialists_are_multitask_and_global_synthesis_is_not_default() -> None:
    prototype = build_love_study_prototype_definition()
    definitions = {
        item.descriptor.specialist_ref: item for item in prototype.specialists
    }

    first = definitions[LOVE_CONCEPT_AFFECT_SPECIALIST_REF]
    second = definitions[LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF]

    first_capabilities = {
        item.capability for item in first.descriptor.capabilities
    }
    second_capabilities = {
        item.capability for item in second.descriptor.capabilities
    }
    assert {
        "love.evidence_extraction",
        "love.concept_analysis",
        "love.affect_mapping",
        "analysis.compare",
        "analysis.critique",
        "analysis.local_synthesis",
    } == first_capabilities
    assert {
        "love.relational_dynamics",
        "love.reciprocity_analysis",
        "love.communication_analysis",
        "analysis.critique",
        "analysis.validate",
        "recommendation.build",
    } == second_capabilities
    assert all(
        "global_synthesis" not in item.contribution_kinds
        for definition in prototype.specialists
        for item in definition.task_types
    )


def test_concept_affect_analysis_is_attributable_and_not_global_synthesis() -> None:
    payload = _first_analysis().to_mapping()

    assert payload["specialist_ref"] == LOVE_CONCEPT_AFFECT_SPECIALIST_REF
    assert payload["contribution_kind"] == "domain_analysis"
    assert payload["global_synthesis_claimed"] is False
    assert payload["findings"][0]["evidence_refs"] == [
        "artifact:issue-body-42"
    ]


def test_relational_analysis_requires_first_analysis_reference() -> None:
    analysis = LoveRelationalDynamicsAnalysis(
        schema=LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA,
        analysis_ref="love-analysis:relational-42",
        study_ref="love-study:issue-42",
        specialist_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        context_revision_ref="context-revision:love-r1",
        findings=(
            _finding(ref="love-finding:reciprocity"),
        ),
        dynamics=("reciprocity", "communication", "boundaries"),
        source_analysis_refs=("love-analysis:concept-affect-42",),
        uncertainties=("La réciprocité n'est pas directement confirmée.",),
        contradictions=(),
        limitations=("Une seule perspective est disponible.",),
        recommendations=("Formuler les attentes et les limites.",),
        evidence_refs=("artifact:issue-body-42",),
        artifact_refs=("artifact:relational-42",),
    )

    assert analysis.to_mapping()["source_analysis_refs"] == [
        "love-analysis:concept-affect-42"
    ]

    with pytest.raises(LoveStudyContractError):
        LoveRelationalDynamicsAnalysis(
            schema=LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA,
            analysis_ref="love-analysis:invalid",
            study_ref="love-study:issue-42",
            specialist_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
            context_revision_ref="context-revision:love-r1",
            findings=(_finding(),),
            dynamics=("reciprocity",),
            source_analysis_refs=(),
            uncertainties=(),
            contradictions=(),
            limitations=(),
            recommendations=(),
            evidence_refs=("artifact:issue-body-42",),
            artifact_refs=("artifact:relational-invalid",),
        )


def test_local_synthesis_must_be_explicit() -> None:
    with pytest.raises(LoveStudyContractError):
        LoveConceptAffectAnalysis(
            schema=LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
            analysis_ref="love-analysis:local-synthesis-invalid",
            study_ref="love-study:issue-42",
            specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
            context_revision_ref="context-revision:love-r1",
            findings=(_finding(),),
            concepts=("affection",),
            affects=("tendresse",),
            uncertainties=(),
            contradictions=(),
            limitations=(),
            recommendations=(),
            evidence_refs=("artifact:issue-body-42",),
            artifact_refs=("artifact:local-synthesis-invalid",),
            contribution_kind="local_synthesis",
        )


def test_synthesized_study_result_requires_liaison_and_final_artifact() -> None:
    result = LoveStudyResult(
        schema=LOVE_STUDY_RESULT_SCHEMA,
        result_ref="love-study-result:42",
        study_ref="love-study:issue-42",
        status="synthesized",
        context_revision_ref="context-revision:love-r2",
        concept_affect_analysis_ref="love-analysis:concept-affect-42",
        relational_dynamics_analysis_ref="love-analysis:relational-42",
        unresolved_points=("Le point de vue de l'autre personne reste absent.",),
        liaison_synthesis_ref="specialist-liaison-synthesis:love-42",
        final_artifact_ref="final-artifact:love-42",
    )

    assert result.to_mapping()["global_synthesis_complete"] is True

    with pytest.raises(LoveStudyContractError):
        LoveStudyResult(
            schema=LOVE_STUDY_RESULT_SCHEMA,
            result_ref="love-study-result:invalid",
            study_ref="love-study:issue-42",
            status="synthesized",
            context_revision_ref="context-revision:love-r2",
            concept_affect_analysis_ref="love-analysis:concept-affect-42",
            relational_dynamics_analysis_ref="love-analysis:relational-42",
            unresolved_points=(),
        )
