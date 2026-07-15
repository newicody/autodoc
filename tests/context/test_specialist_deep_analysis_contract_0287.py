from __future__ import annotations

from dataclasses import replace
import hashlib

from context.correlated_research_work_package_0287 import (
    CorrelatedResearchWorkPackage,
    ResearchAttachmentReference,
)
from context.specialist_deep_analysis_contract_0287 import (
    DEEP_ANALYSIS_CONTRIBUTION_SCHEMA,
    DEEP_ANALYSIS_FINDING_SCHEMA,
    DeepAnalysisContribution,
    DeepAnalysisFinding,
    build_deep_analysis_contribution_message_v2,
    build_deep_analysis_demand_message_v2,
    build_deep_analysis_request_from_work_package,
    project_deep_analysis_to_output_fragment,
    validate_contribution_for_request,
)
from context.specialist_laboratory_message_v2_0287 import (
    SPECIALIST_ARTIFACT_REFERENCE_SCHEMA,
    SpecialistArtifactReference,
)


def _work_package() -> CorrelatedResearchWorkPackage:
    attachment = ResearchAttachmentReference(
        url="https://example.invalid/love-notes.txt",
        filename="love-notes.txt",
        kind="issue_attachment",
        raw_dataset_ref="dataset:github-attachment:love-notes",
        sha256=hashlib.sha256(b"love notes").hexdigest(),
        byte_count=10,
        content_type="text/plain",
    )
    return CorrelatedResearchWorkPackage(
        work_package_ref="research-work-package:love-42",
        repository="newicody/projects",
        run_id="4242",
        issue_number=42,
        issue_url="https://github.com/newicody/projects/issues/42",
        origin_frame_id="github-frame:42",
        ticket_revision_id="github-ticket-revision:42-r1",
        source_candidate_ref="source-candidate:42",
        conversation_ref="laboratory-conversation:love-study",
        return_route_ref="route:github-issue:42",
        context_generation=1,
        authoritative_request={
            "schema": "missipy.github.authoritative_request.v1",
            "title": "Study love",
        },
        correlation_manifest={
            "schema": "missipy.github.dual_artifact_manifest.v1"
        },
        copilot_advisory={
            "schema": "missipy.github.copilot_advisory.v2",
            "artifact_ref": "github-advisory:love-42",
        },
        attachments=(attachment,),
        context_refs=("ctx:issue:42",),
        evidence_refs=("ctx:source-love-note",),
    )


def _artifact() -> SpecialistArtifactReference:
    return SpecialistArtifactReference(
        schema=SPECIALIST_ARTIFACT_REFERENCE_SCHEMA,
        artifact_ref="artifact:love-analysis-1",
        artifact_schema=DEEP_ANALYSIS_CONTRIBUTION_SCHEMA,
        producer_ref="specialist:love-concept-and-affect-analyst",
        producer_visit_ref="laboratory-visit:love-1",
        storage_ref="sql:artifact:love-analysis-1",
        content_sha256=hashlib.sha256(b"analysis").hexdigest(),
        media_type="application/json",
        byte_count=256,
        evidence_refs=("ctx:source-love-note",),
    )


def _request():
    return build_deep_analysis_request_from_work_package(
        _work_package(),
        specialist_ref="specialist:love-concept-and-affect-analyst",
        domain_ref="domain:love-concepts-and-affects",
        objective="Analyse the concepts and affects expressed in the source",
        expected_output_contract_ref="contract:missipy.love.affect_analysis.v1",
        contribution_kind="domain_analysis",
        depth="deep",
        constraints=("Do not infer absent intentions",),
        success_criteria=(
            "Every observed finding links to evidence",
            "Uncertainties remain explicit",
        ),
        mission_ref="mission:love-study:affects",
    )


def _contribution() -> DeepAnalysisContribution:
    finding = DeepAnalysisFinding(
        schema=DEEP_ANALYSIS_FINDING_SCHEMA,
        finding_ref="finding:affection-present",
        status="observed",
        statement="Affection is explicitly expressed",
        confidence=0.8,
        evidence_refs=("ctx:source-love-note",),
        rationale="The source directly uses affectionate language",
    )
    return DeepAnalysisContribution(
        schema=DEEP_ANALYSIS_CONTRIBUTION_SCHEMA,
        contribution_ref="specialist-contribution:love-affects-1",
        request_ref=_request().request_ref,
        specialist_ref="specialist:love-concept-and-affect-analyst",
        visit_ref="laboratory-visit:love-1",
        domain_ref="domain:love-concepts-and-affects",
        contribution_kind="domain_analysis",
        output_contract_ref="contract:missipy.love.affect_analysis.v1",
        findings=(finding,),
        human_representation="Affection is present; reciprocity is unresolved.",
        machine_payload={"dimension_scores": {"affection": 0.8}},
        uncertainties=("The other person's perspective is unavailable",),
        contradictions=(),
        limitations=("Single-source analysis",),
        recommendations=("Request the second relational analysis",),
        requested_specialist_refs=(
            "specialist:love-relational-dynamics-analyst",
        ),
        evidence_refs=("ctx:source-love-note",),
        artifact_refs=(_artifact(),),
    )


def test_work_package_projects_to_deep_analysis_request() -> None:
    request = _request()

    mapping = request.to_mapping()
    assert mapping["work_package_ref"] == "research-work-package:love-42"
    assert mapping["attachment_refs"] == [
        "dataset:github-attachment:love-notes"
    ]
    assert mapping["advisory_ref"] == "github-advisory:love-42"
    assert mapping["requested_contribution_kind"] == "domain_analysis"
    assert mapping["global_synthesis_requested"] is False
    assert mapping["scheduler_route_created"] is False


def test_analysis_contribution_preserves_detail_for_later_synthesis() -> None:
    contribution = _contribution()

    mapping = contribution.to_mapping()
    assert mapping["analysis_preserved_for_later_synthesis"] is True
    assert mapping["global_synthesis_performed"] is False
    assert mapping["findings"][0]["status"] == "observed"
    assert mapping["contradictions"] == []
    assert mapping["requested_specialist_refs"] == [
        "specialist:love-relational-dynamics-analyst"
    ]


def test_request_and_contribution_map_to_v2_messages() -> None:
    request = _request()
    demand = build_deep_analysis_demand_message_v2(
        request,
        message_ref="laboratory-message:love-demand-1",
        visit_ref="laboratory-visit:love-1",
        laboratory_ref="laboratory:love-studies-local",
        correlation_ref="correlation:love-study-42",
    )
    contribution = _contribution()
    analysis = build_deep_analysis_contribution_message_v2(
        contribution,
        demand_message=demand,
        message_ref="laboratory-message:love-analysis-1",
        sequence_no=1,
    )

    assert demand.kind == "demand"
    assert analysis.kind == "analysis"
    assert analysis.reply_to_message_ref == demand.message_ref
    assert analysis.artifact_refs[0].artifact_ref == "artifact:love-analysis-1"
    assert analysis.payload["global_synthesis_performed"] is False


def test_contribution_validation_and_liaison_projection_are_explicit() -> None:
    request = _request()
    contribution = _contribution()

    assert validate_contribution_for_request(request, contribution) == ()
    fragment = project_deep_analysis_to_output_fragment(contribution)
    assert fragment["ready_for_liaison_synthesis"] is True
    assert fragment["liaison_synthesis_created"] is False
    assert fragment["global_synthesis_performed"] is False
    assert fragment["artifact_refs"] == ["artifact:love-analysis-1"]


def test_global_synthesis_is_not_silently_accepted_for_analysis_mission() -> None:
    request = _request()
    contribution = replace(
        _contribution(),
        contribution_kind="global_synthesis",
    )

    assert validate_contribution_for_request(request, contribution) == (
        "contribution kind does not match requested contribution kind",
    )
