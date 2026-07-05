from __future__ import annotations

import pytest

from context.specialist_liaison_synthesis import (
    SpecialistLiaisonPolicy,
    SpecialistOutputFragment,
    build_final_synthesis_packet,
    build_output_fragments_from_specialist_result,
    build_path_trace_from_specialist_result,
    build_specialist_liaison_synthesis,
)
from inference.llm_specialist_adapter import LLMSpecialistTarget, build_llm_solution_candidate, build_llm_specialist_result


class _Prompt:
    def __init__(self, *, prompt_ref: str = "specialist:prompt:thermal-fork:001", draft_id: str = "draft-thermal-fork") -> None:
        self.prompt_ref = prompt_ref
        self.draft_id = draft_id


def test_specialist_liaison_unifies_thermal_analysis_without_github_or_dot_publication() -> None:
    result = _thermal_specialist_result()
    trace = build_path_trace_from_specialist_result(
        request_ref="ctx-request:fork-thermal",
        result=result,
        input_refs=("sql:fork:design-context", "qdrant:recall:fork-materials"),
        depth="deep",
    )
    fragments = build_output_fragments_from_specialist_result(result, default_output_kind="thermal_analysis", default_depth="deep")

    synthesis = build_specialist_liaison_synthesis(
        request_ref="ctx-request:fork-thermal",
        title="Synthèse thermique de la fourchette",
        fragments=fragments,
        traces=(trace,),
    )

    mapping = synthesis.to_mapping()
    assert mapping["publication_surface"] == "none until final adapter"
    assert mapping["final_publication_ready"] is False
    assert mapping["provenance_hidden"] is True
    assert synthesis.bus_trace_refs == (trace.trace_ref,)
    assert synthesis.context_influence_refs == ("ctx-result:fork-thermal-context-delta",)
    assert synthesis.validation_refs == ("artifact:youtube-validation:fork-heat-test",)
    assert "specialist:" not in synthesis.sections[0].body


def test_specialist_path_trace_is_bus_ready_observation_not_command() -> None:
    result = _thermal_specialist_result()

    trace = build_path_trace_from_specialist_result(
        request_ref="ctx-request:fork-thermal",
        result=result,
        input_refs=("sql:fork:design-context",),
    )

    mapping = trace.to_mapping()
    assert mapping["bus_topic_ref"] == "bus:specialist-path-observation"
    assert mapping["observation_only"] is True
    assert mapping["command"] is False
    assert trace.steps[0].output_refs == result.candidate_refs


def test_specialist_fragments_keep_output_kind_depth_context_and_validation_refs() -> None:
    fragments = build_output_fragments_from_specialist_result(_thermal_specialist_result())

    assert len(fragments) == 1
    fragment = fragments[0]
    assert fragment.output_kind == "thermal_analysis"
    assert fragment.depth == "deep"
    assert fragment.context_delta_refs == ("ctx-result:fork-thermal-context-delta",)
    assert fragment.review_request_refs == ("specialist:review:materials",)
    assert fragment.validation_refs == ("artifact:youtube-validation:fork-heat-test",)


def test_final_packet_is_only_built_after_liaison_synthesis() -> None:
    fragments = build_output_fragments_from_specialist_result(_thermal_specialist_result())
    synthesis = build_specialist_liaison_synthesis(
        request_ref="ctx-request:fork-thermal",
        title="Synthèse thermique de la fourchette",
        fragments=fragments,
    )

    packet = build_final_synthesis_packet(synthesis=synthesis, target_ref="github:project:autodoc")

    assert packet.packet_ref.startswith("publication:final-synthesis:")
    assert packet.synthesis.final_publication_ready is True
    assert packet.target_ref == "github:project:autodoc"
    assert "Analyse thermique de la fourchette" in packet.body
    assert packet.context_influence_refs == synthesis.context_influence_refs


def test_liaison_policy_can_hide_review_requests_and_context_influence() -> None:
    fragments = build_output_fragments_from_specialist_result(_thermal_specialist_result())

    synthesis = build_specialist_liaison_synthesis(
        request_ref="ctx-request:fork-thermal",
        title="Synthèse thermique de la fourchette",
        fragments=fragments,
        policy=SpecialistLiaisonPolicy(include_review_requests=False, include_context_influence=False),
    )

    assert synthesis.review_request_refs == ()
    assert synthesis.context_influence_refs == ()


def test_fragment_rejects_untyped_evidence_refs() -> None:
    with pytest.raises(ValueError, match="typed reference"):
        SpecialistOutputFragment(
            fragment_ref="specialist-fragment:bad",
            result_ref="specialist:result:bad",
            output_kind="thermal_analysis",
            title="Bad",
            body="Bad",
            evidence_refs=("not-a-ref",),
        )


def _thermal_specialist_result():
    candidate = build_llm_solution_candidate(
        draft_id="draft-thermal-fork",
        title="Analyse thermique de la fourchette",
        summary="Comparer la conduction dans les branches, isoler les points chauds et proposer une revue matériaux.",
        evidence_refs=("sql:fork:design-context", "qdrant:recall:fork-materials"),
        action_refs=(
            "ctx-result:fork-thermal-context-delta",
            "specialist:review:materials",
            "artifact:youtube-validation:fork-heat-test",
        ),
        confidence=0.82,
        metadata=(
            ("output_kind", "thermal_analysis"),
            ("depth", "deep"),
        ),
    )
    return build_llm_specialist_result(
        prompt=_Prompt(),
        target=LLMSpecialistTarget(target_ref="llm:local:thermal-specialist"),
        candidates=(candidate,),
    )
