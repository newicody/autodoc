from __future__ import annotations

import pytest

from context.github_project_scenario import GitHubProjectArtifact, build_github_source_candidate
from context.server_oriented_deliberation_cycle import (
    DeliberationPolicy,
    ServerOrientation,
    build_bus_statistics_from_rounds,
    build_deliberation_round,
    build_final_artifact_envelope,
    build_refined_demands_from_opinions,
    build_server_orientation_from_github_artifact,
    build_specialist_preliminary_opinion,
)
from context.specialist_liaison_synthesis import (
    EndUserSynthesisSection,
    SpecialistLiaisonSynthesis,
)


def test_server_orientation_treats_github_as_artifact_exchange_only() -> None:
    artifact, source = _artifact_and_source()

    orientation = build_server_orientation_from_github_artifact(
        artifact=artifact,
        source_candidate=source,
        intent="Analyser la demande et proposer le type de document avant production.",
        requested_specialist_refs=("specialist:thermal", "specialist:materials"),
        requested_document_kinds=("avis_preliminaire", "plan_de_document"),
        do_directives=("Identifier ce qui est possible", "Identifier ce qui doit être évité"),
        avoid_directives=("Ne rien publier sur GitHub avant synthèse finale",),
        context_refs=("sql:context:spoon-design",),
    )

    mapping = orientation.to_mapping()
    assert mapping["github_exchange_role"] == "artifact exchange only"
    assert mapping["publication_allowed"] is False
    assert orientation.sql_context_ref == source.sql_record.context_ref
    assert orientation.requested_specialist_refs == ("specialist:thermal", "specialist:materials")


def test_preliminary_opinions_are_recomposed_into_refined_demands() -> None:
    orientation = _orientation()
    thermal = build_specialist_preliminary_opinion(
        orientation=orientation,
        specialist_ref="specialist:thermal",
        stance="possible",
        summary="L'analyse thermique est possible si on compare les chemins de conduction.",
        recommendation="Produire une analyse thermique courte puis demander revue matériaux.",
        evidence_refs=("sql:context:spoon-design",),
        proposed_document_kinds=("analyse_thermique",),
        review_request_refs=("specialist:materials",),
        bus_observation_refs=("bus:obs:thermal-path",),
        confidence=0.81,
    )
    alternative = build_specialist_preliminary_opinion(
        orientation=orientation,
        specialist_ref="specialist:ergonomics",
        stance="better_alternative",
        summary="Une autre forme peut limiter le risque d'usage.",
        recommendation="Demander une variante ergonomique avant production finale.",
        requested_context_refs=("ctx:infant-use-context",),
        proposed_specialist_refs=("specialist:ergonomics",),
        proposed_document_kinds=("variante_ergonomique",),
        bus_observation_refs=("specialist-path:trace:ergonomics",),
        confidence=0.64,
    )

    demands = build_refined_demands_from_opinions(
        orientation=orientation,
        opinions=(thermal, alternative),
        round_index=1,
    )

    assert len(demands) == 2
    assert {d.requested_output_kind for d in demands} == {"analyse_thermique", "variante_ergonomique"}
    assert any("Avis préliminaire" in demand.prompt for demand in demands)
    assert any(demand.depth == "deep" for demand in demands)


def test_deliberation_round_keeps_bus_stats_local_and_not_for_github() -> None:
    orientation = _orientation()
    opinion = build_specialist_preliminary_opinion(
        orientation=orientation,
        specialist_ref="specialist:materials",
        stance="needs_context",
        summary="Il faut connaître le matériau réel avant de produire.",
        recommendation="Demander hydratation contexte matériau et revue thermique.",
        evidence_refs=("qdrant:recall:material-candidates",),
        requested_context_refs=("sql:context:materials",),
        review_request_refs=("specialist:thermal",),
        validation_refs=("artifact:youtube:material-test",),
        bus_observation_refs=("bus:obs:materials-path", "specialist-path:trace:materials"),
        confidence=0.72,
    )
    demands = build_refined_demands_from_opinions(orientation=orientation, opinions=(opinion,), round_index=2)

    round_ = build_deliberation_round(
        orientation=orientation,
        opinions=(opinion,),
        refined_demands=demands,
        round_index=2,
    )
    stats = build_bus_statistics_from_rounds((round_,))

    assert round_.convergence_state == "needs_refinement"
    assert round_.to_mapping()["publication_allowed"] is False
    assert stats.bus_observation_count == 2
    assert stats.requested_context_count >= 1
    assert stats.review_request_count >= 1
    assert stats.validation_ref_count >= 1
    assert stats.to_mapping()["publish_to_github"] is False
    assert stats.to_mapping()["for_vispy_later"] is True


def test_final_artifact_envelope_is_built_only_after_convergence_and_hides_internal_stats() -> None:
    artifact, _source = _artifact_and_source()
    synthesis = _ready_synthesis()

    envelope = build_final_artifact_envelope(
        artifact=artifact,
        synthesis=synthesis,
        target_ref="github:project:autodoc",
    )

    mapping = envelope.to_mapping()
    assert mapping["github_exchange_role"] == "final artifact out only"
    assert mapping["contains_internal_bus_statistics"] is False
    assert envelope.target_ref == "github:project:autodoc"
    assert envelope.synthesis_ref == synthesis.synthesis_ref
    assert "bus" not in envelope.body.lower()


def test_final_artifact_rejects_non_ready_synthesis() -> None:
    artifact, _source = _artifact_and_source()
    synthesis = SpecialistLiaisonSynthesis(
        synthesis_ref="synthesis:local:not-ready",
        request_ref="ctx-request:spoon",
        title="Synthèse non prête",
        sections=(
            EndUserSynthesisSection(
                section_ref="synthesis-section:not-ready",
                title="Brouillon",
                body="Encore en navette.",
                evidence_refs=("sql:context:spoon-design",),
            ),
        ),
        final_publication_ready=False,
    )

    with pytest.raises(ValueError, match="final_publication_ready"):
        build_final_artifact_envelope(artifact=artifact, synthesis=synthesis, target_ref="github:project:autodoc")


def test_orientation_rejects_untyped_refs() -> None:
    with pytest.raises(ValueError, match="typed reference"):
        ServerOrientation(
            orientation_ref="bad",
            artifact_ref="github:artifact:spoon",
            source_ref="artifact:source:spoon",
            sql_context_ref="sql:context:spoon-design",
            title="Bad",
            intent="Bad",
            requested_specialist_refs=("specialist:thermal",),
            requested_document_kinds=("analyse",),
        )


def test_deliberation_policy_bounds_refined_demands() -> None:
    orientation = _orientation()
    opinions = tuple(
        build_specialist_preliminary_opinion(
            orientation=orientation,
            specialist_ref=f"specialist:test-{idx}",
            stance="possible",
            summary=f"Avis {idx}",
            recommendation="Produire une note courte.",
            proposed_document_kinds=("note",),
            confidence=0.5,
        )
        for idx in range(5)
    )

    demands = build_refined_demands_from_opinions(
        orientation=orientation,
        opinions=opinions,
        round_index=1,
        policy=DeliberationPolicy(max_refined_demands=2),
    )

    assert len(demands) == 2


def _artifact_and_source():
    artifact = GitHubProjectArtifact(
        artifact_ref="github:artifact:spoon-request",
        project_ref="github:project:autodoc",
        item_ref="github:item:spoon",
        title="Cuillère bébé",
        body="Artifact Copilot: explorer la meilleure manière de produire une analyse utilisable.",
        author_ref="github:user:copilot",
    )
    return artifact, build_github_source_candidate(artifact)


def _orientation():
    artifact, source = _artifact_and_source()
    return build_server_orientation_from_github_artifact(
        artifact=artifact,
        source_candidate=source,
        intent="Orienter les spécialistes avant production.",
        requested_specialist_refs=("specialist:thermal", "specialist:materials", "specialist:ergonomics"),
        requested_document_kinds=("avis_preliminaire",),
        context_refs=("sql:context:spoon-design",),
    )


def _ready_synthesis() -> SpecialistLiaisonSynthesis:
    section = EndUserSynthesisSection(
        section_ref="synthesis-section:spoon-final",
        title="Analyse retenue",
        body="La synthèse finale propose une analyse thermique puis une revue matériaux avant fabrication.",
        evidence_refs=("sql:context:spoon-design", "qdrant:recall:spoon-materials"),
        context_delta_refs=("ctx-result:spoon-final-context",),
        validation_refs=("artifact:youtube:material-test",),
    )
    return SpecialistLiaisonSynthesis(
        synthesis_ref="synthesis:spoon-final",
        request_ref="ctx-request:spoon",
        title="Synthèse finale cuillère bébé",
        sections=(section,),
        bus_trace_refs=("specialist-path:trace:thermal",),
        context_influence_refs=("ctx-result:spoon-final-context",),
        validation_refs=("artifact:youtube:material-test",),
        final_publication_ready=True,
        provenance_hidden=True,
    )
