from __future__ import annotations

import pytest

from context.context_variation_core import (
    ContextExplorationBudget,
    build_context_exploration_plan,
)
from context.github_project_scenario import (
    GitHubProjectArtifact,
    GitHubProjectPublicationPolicy,
    build_github_context_objective,
    build_github_project_publication,
    build_github_project_scenario_packet,
    build_github_source_candidate,
)
from context.context_variation_core import ContextVariationAxis
from inference.llm_specialist_adapter import (
    LLMSpecialistTarget,
    build_llm_solution_candidate,
    build_llm_specialist_result,
)


def test_github_artifact_becomes_sql_source_candidate() -> None:
    artifact = _artifact()

    source = build_github_source_candidate(artifact)

    assert source.source_ref.startswith("artifact:github-source:")
    assert source.sql_record.context_ref.startswith("sql:github_artifact:")
    assert source.sql_record.kind == "github_artifact"
    assert source.sql_record.parent_ref == artifact.item_ref
    assert dict(source.sql_record.metadata)["project_ref"] == artifact.project_ref
    assert dict(source.sql_record.metadata)["source_system"] == "github_project"


def test_github_objective_points_to_sql_authority_not_artifact_body() -> None:
    source = build_github_source_candidate(_artifact())

    objective = build_github_context_objective(source)

    assert objective.objective_id.startswith("github-objective-")
    assert objective.source_ref == source.sql_record.context_ref
    assert objective.parent_context_ref == source.artifact.item_ref
    assert source.artifact.body in objective.statement


def test_github_publication_serializes_specialist_candidates_with_refs_only() -> None:
    artifact = _artifact()
    source = build_github_source_candidate(artifact)
    objective = build_github_context_objective(source)
    plan = _plan(objective)
    result = _specialist_result(plan_id=plan.plan_id, draft_id="draft-github-001", evidence_ref=source.sql_record.context_ref)

    publication = build_github_project_publication(
        artifact=artifact,
        source_candidate=source,
        plan=plan,
        specialist_result=result,
    )

    assert publication.publication_ref.startswith("github:project-publication:")
    assert publication.sql_context_ref == source.sql_record.context_ref
    assert publication.specialist_result_ref == result.result_ref
    assert publication.candidate_refs == result.candidate_refs
    mapping = publication.to_mapping()
    assert mapping["runtime_import"] == "external GitHub adapter only"
    assert "Autodoc local context exploration result" in publication.body


def test_github_publication_caps_candidates_and_truncates_summaries() -> None:
    artifact = _artifact()
    source = build_github_source_candidate(artifact)
    objective = build_github_context_objective(source)
    plan = _plan(objective)
    result = _specialist_result(plan_id=plan.plan_id, draft_id="draft-github-002", evidence_ref=source.sql_record.context_ref, candidate_count=3)

    publication = build_github_project_publication(
        artifact=artifact,
        source_candidate=source,
        plan=plan,
        specialist_result=result,
        policy=GitHubProjectPublicationPolicy(max_candidates=1, max_summary_chars=20),
    )

    assert publication.capped is True
    assert len(publication.candidates) == 1
    assert publication.candidates[0].truncated is True
    assert len(publication.candidates[0].summary) == 20


def test_github_scenario_packet_links_artifact_sql_plan_and_publication() -> None:
    artifact = _artifact()
    source = build_github_source_candidate(artifact)
    objective = build_github_context_objective(source)
    plan = _plan(objective)
    result = _specialist_result(plan_id=plan.plan_id, draft_id="draft-github-003", evidence_ref=source.sql_record.context_ref)

    packet = build_github_project_scenario_packet(
        artifact=artifact,
        plan=plan,
        specialist_result=result,
    )

    assert packet.source_candidate.sql_record.context_ref == source.sql_record.context_ref
    assert packet.objective == objective
    assert packet.plan == plan
    assert packet.publication.specialist_result_ref == result.result_ref
    assert packet.to_mapping()["schema"] == "missipy.github_project.scenario.v1"


def test_github_scenario_rejects_non_github_refs() -> None:
    with pytest.raises(ValueError, match="artifact_ref must start"):
        GitHubProjectArtifact(
            artifact_ref="artifact:not-github",
            project_ref="github:project:autodoc",
            item_ref="github:item:42",
            title="Bad artifact",
            body="Bad body",
        )


def _artifact() -> GitHubProjectArtifact:
    return GitHubProjectArtifact(
        artifact_ref="github:artifact:baby-fork-0001",
        project_ref="github:project:autodoc",
        item_ref="github:item:baby-fork",
        author_ref="github:user:eric",
        title="Baby fork material exploration",
        body="Explore a baby fork design with safety, material and fabrication constraints.",
        metadata=(("status", "todo"),),
    )


def _plan(objective):
    axis = ContextVariationAxis(
        axis_id="material",
        label="Material",
        question="Which material constraints must shape the baby fork?",
        tags=("material", "safety"),
    )
    return build_context_exploration_plan(
        plan_id="plan-github-baby-fork",
        objective=objective,
        axes=(axis,),
        budget=ContextExplorationBudget(
            max_variants=2,
            max_depth=3,
            max_specialist_calls=2,
            max_retrievals=4,
            max_wall_time_s=30.0,
        ),
        base_context_refs=(objective.source_ref,),
        specialist_refs=("specialist:material",),
    )


def _specialist_result(*, plan_id: str, draft_id: str, evidence_ref: str, candidate_count: int = 1):
    target = LLMSpecialistTarget()
    prompt = _Prompt(prompt_ref=f"specialist:prompt:{draft_id}:abc", draft_id=draft_id)
    candidates = tuple(
        build_llm_solution_candidate(
            draft_id=draft_id,
            title=f"Candidate {index}",
            summary="Use hydrated SQL evidence to propose a bounded project decision. " * 2,
            evidence_refs=(evidence_ref,),
            action_refs=(f"github:project-action:{plan_id}:{index}",),
            confidence=0.75,
            ordinal=index,
        )
        for index in range(1, candidate_count + 1)
    )
    return build_llm_specialist_result(prompt=prompt, target=target, candidates=candidates)


class _Prompt:
    def __init__(self, *, prompt_ref: str, draft_id: str) -> None:
        self.prompt_ref = prompt_ref
        self.draft_id = draft_id
