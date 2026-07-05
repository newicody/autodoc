from __future__ import annotations

import pytest

from context.context_graph_export import (
    ContextGraphEdge,
    ContextGraphNode,
    ContextGraphPolicy,
    build_github_project_context_graph,
    export_context_graph_dot,
)
from context.context_variation_core import ContextExplorationBudget, ContextVariationAxis, build_context_exploration_plan
from context.github_project_scenario import (
    GitHubProjectArtifact,
    build_github_context_objective,
    build_github_project_scenario_packet,
    build_github_source_candidate,
)
from inference.llm_specialist_adapter import LLMSpecialistTarget, build_llm_solution_candidate, build_llm_specialist_result


def test_github_project_context_graph_links_sql_authority_projection_and_publication() -> None:
    packet = _packet()

    graph = build_github_project_context_graph(packet)

    mapping = graph.to_mapping()
    assert mapping["runtime_import"] == "none; passive export only"
    assert graph.snapshot_ref.startswith("ctx-graph:github-project:")
    node_labels = {node.label for node in graph.nodes}
    assert "SQLContextStore authority" in node_labels
    assert "Qdrant projection/retrieval" in node_labels
    assert "LLMSpecialistResult" in node_labels
    assert "GitHubProjectPublication" in node_labels
    edge_labels = {edge.label for edge in graph.edges}
    assert "recall refs then SQL re-hydrate" in edge_labels
    assert "future adapter posts result" in edge_labels


def test_context_graph_dot_export_is_deterministic_and_escaped() -> None:
    graph = build_github_project_context_graph(_packet())

    exported = export_context_graph_dot(graph)
    exported_again = export_context_graph_dot(graph)

    assert exported.dot == exported_again.dot
    assert exported.node_count == len(graph.nodes)
    assert exported.edge_count == len(graph.edges)
    assert "digraph context_graph_snapshot_0122" in exported.dot
    assert "SQLContextStore authority" in exported.dot
    assert "qdrant:projection:" in exported.dot
    assert "github_publication -> future_github_adapter" in exported.dot


def test_context_graph_policy_can_hide_future_adapter() -> None:
    graph = build_github_project_context_graph(_packet(), policy=ContextGraphPolicy(include_future_adapter=False))

    assert "future_github_adapter" not in {node.node_id for node in graph.nodes}
    assert "e_future_adapter" not in {edge.edge_id for edge in graph.edges}


def test_context_graph_rejects_edges_to_unknown_nodes() -> None:
    node = ContextGraphNode(node_id="known", label="Known", kind="sql_authority", ref="sql:known")
    edge = ContextGraphEdge(edge_id="edge", source_id="known", target_id="missing", label="bad", kind="plans")

    with pytest.raises(ValueError, match="known node ids"):
        from context.context_graph_export import ContextGraphSnapshot

        ContextGraphSnapshot(snapshot_ref="ctx-graph:test", title="Bad graph", nodes=(node,), edges=(edge,))


def test_context_graph_policy_bounds_nodes_and_edges() -> None:
    with pytest.raises(ValueError, match="nodes exceed"):
        build_github_project_context_graph(_packet(), policy=ContextGraphPolicy(max_nodes=1))

    with pytest.raises(ValueError, match="edges exceed"):
        build_github_project_context_graph(_packet(), policy=ContextGraphPolicy(max_edges=1))


def _packet():
    artifact = GitHubProjectArtifact(
        artifact_ref="github:artifact:baby-fork-graph-0001",
        project_ref="github:project:autodoc",
        item_ref="github:item:baby-fork-graph",
        author_ref="github:user:eric",
        title="Baby fork graph exploration",
        body="Explore graph visibility for SQL authority, Qdrant projection and specialist output.",
    )
    source = build_github_source_candidate(artifact)
    objective = build_github_context_objective(source)
    axes = (
        ContextVariationAxis(
            axis_id="material",
            label="Material",
            question="Which material context should be explored?",
            tags=("material",),
        ),
        ContextVariationAxis(
            axis_id="safety",
            label="Safety",
            question="Which safety constraints should be explored?",
            tags=("safety",),
        ),
    )
    plan = build_context_exploration_plan(
        plan_id="plan-github-graph",
        objective=objective,
        axes=axes,
        budget=ContextExplorationBudget(
            max_variants=2,
            max_depth=3,
            max_specialist_calls=2,
            max_retrievals=4,
            max_wall_time_s=30.0,
        ),
        base_context_refs=(source.sql_record.context_ref,),
        specialist_refs=("specialist:graph",),
    )
    prompt = _Prompt(prompt_ref="specialist:prompt:draft-graph:001", draft_id="draft-graph")
    candidate = build_llm_solution_candidate(
        draft_id="draft-graph",
        title="Graph candidate",
        summary="Use the passive graph to inspect context flow without changing runtime authority.",
        evidence_refs=(source.sql_record.context_ref,),
        action_refs=("github:project-action:graph",),
        confidence=0.8,
    )
    specialist_result = build_llm_specialist_result(
        prompt=prompt,
        target=LLMSpecialistTarget(),
        candidates=(candidate,),
    )
    return build_github_project_scenario_packet(
        artifact=artifact,
        plan=plan,
        specialist_result=specialist_result,
    )


class _Prompt:
    def __init__(self, *, prompt_ref: str, draft_id: str) -> None:
        self.prompt_ref = prompt_ref
        self.draft_id = draft_id
