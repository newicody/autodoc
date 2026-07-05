from __future__ import annotations

import pytest

from context.context_graph_export import ContextGraphNode, ContextGraphSnapshot, build_github_project_context_graph, export_context_graph_dot
from context.context_variation_core import ContextExplorationBudget, ContextVariationAxis, build_context_exploration_plan
from context.github_project_scenario import (
    GitHubProjectArtifact,
    build_github_context_objective,
    build_github_project_scenario_packet,
    build_github_source_candidate,
)
from context.github_publication_review import (
    GitHubPublicationReviewPolicy,
    build_github_publication_review,
    render_github_publication_review_markdown,
)
from inference.llm_specialist_adapter import LLMSpecialistTarget, build_llm_solution_candidate, build_llm_specialist_result


def test_github_publication_review_is_local_reviewable_and_reference_only() -> None:
    packet = _packet(candidate_count=2)
    graph = build_github_project_context_graph(packet)
    dot_export = export_context_graph_dot(graph)

    review = build_github_publication_review(packet, graph, dot_export)

    mapping = review.to_mapping()
    assert mapping["runtime_import"] == "none; external GitHub adapter posts only after review"
    assert review.review_ref.startswith("github-review:publication:")
    assert review.publication_ref == packet.publication.publication_ref
    assert review.sql_context_ref == packet.source_candidate.sql_record.context_ref
    assert review.graph_snapshot_ref == graph.snapshot_ref
    assert len(review.dot_digest) == 16
    assert review.status == "pending"
    assert review.candidate_refs == tuple(candidate.candidate_ref for candidate in packet.publication.candidates)


def test_github_publication_review_markdown_renders_review_without_posting() -> None:
    packet = _packet(candidate_count=1)
    graph = build_github_project_context_graph(packet)
    review = build_github_publication_review(packet, graph, export_context_graph_dot(graph))

    rendered = render_github_publication_review_markdown(review)

    assert rendered.review_ref == review.review_ref
    assert rendered.candidate_count == 1
    assert "Review status: pending" in rendered.markdown
    assert "Publication is local and reviewable; it does not post to GitHub." in rendered.markdown
    assert "External GitHub adapter required after approval." in rendered.markdown
    assert "SQLContextStore authority" in rendered.markdown
    assert "Qdrant graph/projection evidence digest" in rendered.markdown


def test_github_publication_review_policy_caps_candidates_and_body() -> None:
    packet = _packet(candidate_count=3, long_summary=True)
    graph = build_github_project_context_graph(packet)
    policy = GitHubPublicationReviewPolicy(max_candidates=1, max_summary_chars=32, max_body_chars=64)

    review = build_github_publication_review(packet, graph, export_context_graph_dot(graph), policy=policy)

    assert len(review.candidates) == 1
    assert review.capped is True
    assert review.candidates[0].truncated is True
    assert len(review.candidates[0].summary) <= 32
    assert len(review.body) <= 64
    assert dict(review.metadata)["body_truncated"] == "true"


def test_github_publication_review_rejects_graph_without_publication_ref() -> None:
    packet = _packet(candidate_count=1)
    graph = ContextGraphSnapshot(
        snapshot_ref="ctx-graph:bad",
        title="Bad",
        nodes=(ContextGraphNode("sql_authority", "SQL", "sql_authority", packet.source_candidate.sql_record.context_ref),),
        edges=(),
    )

    with pytest.raises(ValueError, match="publication_ref"):
        build_github_publication_review(packet, graph, export_context_graph_dot(graph))


def test_github_publication_review_requires_matching_dot_export_snapshot() -> None:
    packet = _packet(candidate_count=1)
    graph = build_github_project_context_graph(packet)
    wrong = export_context_graph_dot(
        ContextGraphSnapshot(
            snapshot_ref="ctx-graph:other",
            title="Other",
            nodes=(ContextGraphNode("github_publication", "Publication", "github_publication", packet.publication.publication_ref),),
            edges=(),
        )
    )

    with pytest.raises(ValueError, match="snapshot_ref"):
        build_github_publication_review(packet, graph, wrong)


def _packet(*, candidate_count: int, long_summary: bool = False):
    artifact = GitHubProjectArtifact(
        artifact_ref="github:artifact:baby-fork-review-0001",
        project_ref="github:project:autodoc",
        item_ref="github:item:baby-fork-review",
        author_ref="github:user:eric",
        title="Baby fork review publication",
        body="Prepare a local review packet before posting back to the GitHub Project.",
    )
    source = build_github_source_candidate(artifact)
    objective = build_github_context_objective(source)
    plan = build_context_exploration_plan(
        plan_id="plan-github-review",
        objective=objective,
        axes=(
            ContextVariationAxis("material", "Material", "Which material context should be explored?", ("material",)),
            ContextVariationAxis("safety", "Safety", "Which safety constraints should be explored?", ("safety",)),
        ),
        budget=ContextExplorationBudget(
            max_variants=2,
            max_depth=3,
            max_specialist_calls=2,
            max_retrievals=4,
            max_wall_time_s=30.0,
        ),
        base_context_refs=(source.sql_record.context_ref,),
        specialist_refs=("specialist:review",),
    )
    prompt = _Prompt(prompt_ref="specialist:prompt:draft-review:001", draft_id="draft-review")
    candidates = tuple(
        build_llm_solution_candidate(
            draft_id="draft-review",
            title=f"Review candidate {index}",
            summary=("x" * 96 if long_summary else "Review this local publication candidate before external synchronization."),
            evidence_refs=(source.sql_record.context_ref,),
            action_refs=(f"github:project-action:review-{index}",),
            ordinal=index,
            confidence=0.7,
        )
        for index in range(1, candidate_count + 1)
    )
    specialist_result = build_llm_specialist_result(
        prompt=prompt,
        target=LLMSpecialistTarget(),
        candidates=candidates,
    )
    return build_github_project_scenario_packet(artifact=artifact, plan=plan, specialist_result=specialist_result)


class _Prompt:
    def __init__(self, *, prompt_ref: str, draft_id: str) -> None:
        self.prompt_ref = prompt_ref
        self.draft_id = draft_id
