from __future__ import annotations

import copy

import pytest

from context.github_research_love_final_deliverable_sql_0287 import (
    RECEIPT_SCHEMA as FINAL_SQL_RECEIPT_SCHEMA,
    RESULT_SCHEMA as FINAL_SQL_RESULT_SCHEMA,
)
from context.github_research_love_final_remote_publication_0287 import (
    GitHubResearchLoveFinalPublicationCommand,
    GitHubResearchLoveFinalRemotePublicationError,
    _validated_lineage,
)
from context.github_research_love_liaison_synthesis_0287 import (
    RESULT_SCHEMA as LIAISON_RESULT_SCHEMA,
)


_WORK_PACKAGE_REF = "research-work-package:compact-synthesis"
_SYNTHESIS_REF = "synthesis:specialist-liaison:compact-synthesis"
_PACKET_REF = "publication:final-synthesis:compact-synthesis"
_TARGET_REF = "github:newicody/projects#54"
_AUTHORITY_REF = "context-object:github-love-final-compact"
_ARTIFACT_REF = "artifact:github-love-final-compact"


def _liaison() -> dict[str, object]:
    return {
        "schema": LIAISON_RESULT_SCHEMA,
        "valid": True,
        "status": "synthesized",
        "issues": [],
        "plan": {
            "work_package_ref": _WORK_PACKAGE_REF,
            "plan_digest": "sha256:" + "1" * 64,
            "first_sql_ref": "context-object:first-analysis",
            "second_sql_ref": "context-object:second-analysis",
        },
        "mutualization": {"uncertainties": []},
        "synthesis": {
            "schema": "missipy.specialist_liaison.synthesis.v1",
            "synthesis_ref": _SYNTHESIS_REF,
            "request_ref": _WORK_PACKAGE_REF,
            "title": "Synthèse de liaison de l’étude",
            "section_refs": ["synthesis-section:one"],
            "sections": [],
            "final_publication_ready": False,
            "provenance_hidden": True,
        },
    }


def _final_deliverable() -> dict[str, object]:
    return {
        "schema": FINAL_SQL_RESULT_SCHEMA,
        "valid": True,
        "status": "persisted",
        "issues": [],
        "plan": {
            "work_package_ref": _WORK_PACKAGE_REF,
            "liaison_plan_digest": "sha256:" + "1" * 64,
            "first_analysis_object_ref": "context-object:first-analysis",
            "second_analysis_object_ref": "context-object:second-analysis",
            "parent_revision_ref": "context-revision:analysis",
            "packet": {
                "schema": "missipy.specialist_liaison.final_packet.v1",
                "packet_ref": _PACKET_REF,
                "target_ref": _TARGET_REF,
                "title": "Synthèse de liaison de l’étude",
                "body": "Livrable final",
                "synthesis_ref": _SYNTHESIS_REF,
                "evidence_refs": ["sql:context-object:first-analysis"],
                "context_influence_refs": [],
                "validation_refs": [],
            },
            "authority_object": {
                "object_ref": _AUTHORITY_REF,
                "metadata": {
                    "synthesis_ref": _SYNTHESIS_REF,
                    "final_publication_ready": True,
                    "specialist_provenance_hidden": True,
                },
            },
            "artifact": {"artifact_ref": _ARTIFACT_REF},
            "boundaries": {"final_publication_ready": True},
        },
        "receipt": {
            "schema": FINAL_SQL_RECEIPT_SCHEMA,
            "readback_verified": True,
            "target_ref": _TARGET_REF,
            "packet_ref": _PACKET_REF,
            "authority_object_ref": _AUTHORITY_REF,
            "artifact_ref": _ARTIFACT_REF,
            "revision_ref": "context-revision:final",
        },
        "remote_publication_performed": False,
    }


def _command(
    *,
    liaison: dict[str, object] | None = None,
    final_deliverable: dict[str, object] | None = None,
) -> GitHubResearchLoveFinalPublicationCommand:
    return GitHubResearchLoveFinalPublicationCommand(
        final_deliverable=final_deliverable or _final_deliverable(),
        liaison=liaison or _liaison(),
        repository="newicody/projects",
        issue_number=54,
        source_issue_ref="github-frame:newicody/projects/issues/54",
        policy_decision_id="policy:0287:r16-r51",
        operator_decision="approve",
        project_item_id="PVTI_test",
        project_field_ref="PVTF_test",
        project_field_name="Résumé",
    )


def test_compact_final_packet_rehydrates_ready_publication_view() -> None:
    liaison = _liaison()
    original = copy.deepcopy(liaison["synthesis"])

    lineage = _validated_lineage(_command(liaison=liaison))

    assert lineage["packet_synthesis"]["synthesis_ref"] == _SYNTHESIS_REF
    assert lineage["packet_synthesis"]["final_publication_ready"] is True
    assert liaison["synthesis"] == original
    assert liaison["synthesis"]["final_publication_ready"] is False


def test_compact_packet_rejects_cross_synthesis_correlation() -> None:
    final_deliverable = _final_deliverable()
    final_deliverable["plan"]["packet"]["synthesis_ref"] = (
        "synthesis:specialist-liaison:other"
    )

    with pytest.raises(
        GitHubResearchLoveFinalRemotePublicationError,
        match="liaison synthesis_ref differs from final packet",
    ):
        _validated_lineage(_command(final_deliverable=final_deliverable))


def test_compact_packet_requires_sql_readiness_proof() -> None:
    final_deliverable = _final_deliverable()
    final_deliverable["plan"]["boundaries"]["final_publication_ready"] = False

    with pytest.raises(
        GitHubResearchLoveFinalRemotePublicationError,
        match="final SQL plan does not prove publication readiness",
    ):
        _validated_lineage(_command(final_deliverable=final_deliverable))


def test_embedded_legacy_packet_remains_supported_without_compact_ref() -> None:
    final_deliverable = _final_deliverable()
    packet = final_deliverable["plan"]["packet"]
    synthesis_ref = packet.pop("synthesis_ref")
    packet["synthesis"] = {
        "synthesis_ref": synthesis_ref,
        "request_ref": _WORK_PACKAGE_REF,
        "title": "Synthèse de liaison de l’étude",
        "final_publication_ready": True,
        "provenance_hidden": True,
    }

    lineage = _validated_lineage(
        _command(final_deliverable=final_deliverable)
    )

    assert lineage["packet_synthesis"]["synthesis_ref"] == _SYNTHESIS_REF
    assert lineage["packet_synthesis"]["final_publication_ready"] is True


def test_embedded_packet_rejects_conflicting_compact_ref() -> None:
    final_deliverable = _final_deliverable()
    packet = final_deliverable["plan"]["packet"]
    packet["synthesis"] = {
        "synthesis_ref": "synthesis:specialist-liaison:other",
        "final_publication_ready": True,
        "provenance_hidden": True,
    }

    with pytest.raises(
        GitHubResearchLoveFinalRemotePublicationError,
        match="embedded packet synthesis_ref mismatch",
    ):
        _validated_lineage(_command(final_deliverable=final_deliverable))
