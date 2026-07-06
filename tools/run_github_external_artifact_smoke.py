#!/usr/bin/env python3
"""GitHub external artifact smoke.

0163 refactors the 0162 boundary smoke so the local GitHub artifact loop uses
existing repository contracts/builders instead of parallel JSON model objects:
GitHubProjectArtifact, build_github_source_candidate,
build_github_project_scenario_packet, build_github_project_context_graph,
export_context_graph_dot, build_github_publication_review and
render_github_publication_review_markdown.

The smoke remains local-only: no SQL write, no Qdrant write, no GitHub API call,
no external network, no Scheduler execution, no LLM execution, and no OpenVINO
execution.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


DEFAULT_OUTPUT_DIR = ".var/smoke/artifacts/0162"
DEFAULT_DEVELOPMENT_REPOSITORY = "newicody/autodoc"
DEFAULT_EXTERNAL_REPOSITORY = "newicody/autodoc-ideas"
DEFAULT_PROJECT_REF = "github:project/autodoc-ideas"
DEFAULT_PROJECT_ITEM_REF = "github:project-item/demo-0162"
DEFAULT_ARTIFACT_REF = "github:artifact/demo-0162"


_REUSED_EXISTING_SURFACES = (
    "src/context/github_project_scenario.py",
    "src/context/context_graph_export.py",
    "src/context/github_publication_review.py",
    "src/context/context_variation_core.py",
    "src/inference/llm_specialist_adapter.py",
    "src/context/server_oriented_deliberation_cycle.py",
    "src/context/source_candidate_github_projection_payload.py",
    "src/context/source_candidate_external_projection_contract.py",
    "src/context/source_candidate_read_only_external_probe.py",
    "src/context/source_candidate_remote_mutation_gate.py",
    "src/context/source_candidate_external_probe_bundle.py",
    "src/context/vector_indexing_job_plan.py",
    "src/context/scheduler_deliberation_route_contract.py",
)

_EXISTING_BUILDERS_USED = (
    "GitHubProjectArtifact",
    "build_github_source_candidate",
    "build_github_context_objective",
    "build_github_project_scenario_packet",
    "build_github_project_context_graph",
    "export_context_graph_dot",
    "build_github_publication_review",
    "render_github_publication_review_markdown",
    "build_context_exploration_plan",
    "LLMSolutionCandidate",
    "LLMSpecialistResult",
    "build_server_orientation_from_github_artifact",
)

_FORBIDDEN_RUNTIME_ACTIONS = (
    "sql_write",
    "qdrant_write",
    "github_api_call",
    "external_network",
    "scheduler_execution",
    "llm_execution",
    "openvino_execution",
    "autodoc_dev_repo_ingestion",
)


@dataclass(frozen=True, slots=True)
class BoundarySurface:
    key: str
    path: Path
    reason: str
    required: bool = True

    def to_mapping(self, *, root: Path) -> dict[str, Any]:
        return {
            "key": self.key,
            "path": _display_path(self.path, root=root),
            "reason": self.reason,
            "required": self.required,
            "status": "present" if self.path.exists() else "missing",
        }


@dataclass(frozen=True, slots=True)
class GitHubExternalArtifactPlan:
    repository_root: Path
    output_dir: Path
    fixture_json: Path
    result_json: Path
    result_md: Path
    scenario_packet_json: Path
    context_graph_json: Path
    context_graph_dot: Path
    publication_review_json: Path
    publication_review_md: Path
    development_repository: str
    external_repository: str
    execute: bool
    surfaces: tuple[BoundarySurface, ...]

    @property
    def ready(self) -> bool:
        return all(surface.path.exists() for surface in self.surfaces if surface.required)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.repository_root),
            "output_dir": str(self.output_dir),
            "fixture_json": str(self.fixture_json),
            "result_json": str(self.result_json),
            "result_md": str(self.result_md),
            "scenario_packet_json": str(self.scenario_packet_json),
            "context_graph_json": str(self.context_graph_json),
            "context_graph_dot": str(self.context_graph_dot),
            "publication_review_json": str(self.publication_review_json),
            "publication_review_md": str(self.publication_review_md),
            "development_repository": self.development_repository,
            "external_repository": self.external_repository,
            "execute": self.execute,
            "ready_for_github_external_artifact_smoke": self.ready,
            "surfaces": [surface.to_mapping(root=self.repository_root) for surface in self.surfaces],
            "boundary": [
                "Autodoc/MissiPy development repo is infrastructure, not an ingestable idea corpus",
                "external GitHub Project repository must be explicit",
                "GitHub is artifact exchange only until a reviewed adapter applies remote mutation",
                "uses existing GitHub/source/specialist/context graph/publication builders",
                *(f"no_{action}" for action in _FORBIDDEN_RUNTIME_ACTIONS),
            ],
            "reused_existing_surfaces": list(_REUSED_EXISTING_SURFACES),
            "existing_builders_used": list(_EXISTING_BUILDERS_USED),
        }

    def to_markdown(self) -> str:
        lines = [
            "# GitHub external artifact smoke plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"development_repository: `{self.development_repository}`",
            f"external_repository: `{self.external_repository}`",
            f"fixture_json: `{self.fixture_json}`",
            f"execute: `{str(self.execute).lower()}`",
            f"ready_for_github_external_artifact_smoke: `{str(self.ready).lower()}`",
            "",
            "## Existing surfaces",
            "",
            "| key | status | required | path | reason |",
            "| --- | --- | --- | --- | --- |",
        ]
        for surface in self.surfaces:
            row = surface.to_mapping(root=self.repository_root)
            lines.append(f"| {row['key']} | {row['status']} | `{str(row['required']).lower()}` | `{row['path']}` | {row['reason']} |")
        lines.extend([
            "",
            "## Existing builders used",
            "",
        ])
        for name in _EXISTING_BUILDERS_USED:
            lines.append(f"- `{name}`")
        lines.extend([
            "",
            "## Boundary",
            "",
            "- external artifact source must be explicit",
            "- external artifact repository must differ from the Autodoc development repository",
            "- no SQL write, no Qdrant write, no GitHub API call, no external network",
            "- output is a local review packet built from existing contracts",
            "",
        ])
        return "\n".join(lines)


def build_github_external_artifact_plan(
    root: Path,
    *,
    output_dir: Path,
    fixture_json: Path | None,
    development_repository: str,
    external_repository: str,
    execute: bool,
) -> GitHubExternalArtifactPlan:
    root = root.resolve()
    output_dir = _resolve_repo_path(root, output_dir)
    fixture = _resolve_repo_path(root, fixture_json) if fixture_json is not None else output_dir / "github_external_artifact_fixture.json"

    return GitHubExternalArtifactPlan(
        repository_root=root,
        output_dir=output_dir,
        fixture_json=fixture,
        result_json=output_dir / "github_external_artifact_smoke_result.json",
        result_md=output_dir / "github_external_artifact_smoke_report.md",
        scenario_packet_json=output_dir / "github_project_scenario_packet.json",
        context_graph_json=output_dir / "github_project_context_graph.json",
        context_graph_dot=output_dir / "github_project_context_graph.dot",
        publication_review_json=output_dir / "github_publication_review_packet.json",
        publication_review_md=output_dir / "github_publication_review_packet.md",
        development_repository=development_repository,
        external_repository=external_repository,
        execute=execute,
        surfaces=tuple(
            BoundarySurface(key, root / path, "existing GitHub/external artifact exchange surface")
            for key, path in (
                ("github_project_scenario", "src/context/github_project_scenario.py"),
                ("context_graph_export", "src/context/context_graph_export.py"),
                ("github_publication_review", "src/context/github_publication_review.py"),
                ("context_variation_core", "src/context/context_variation_core.py"),
                ("llm_specialist_adapter", "src/inference/llm_specialist_adapter.py"),
                ("server_oriented_deliberation_cycle", "src/context/server_oriented_deliberation_cycle.py"),
                ("source_candidate_github_projection_payload", "src/context/source_candidate_github_projection_payload.py"),
                ("source_candidate_external_projection_contract", "src/context/source_candidate_external_projection_contract.py"),
                ("source_candidate_read_only_external_probe", "src/context/source_candidate_read_only_external_probe.py"),
                ("source_candidate_remote_mutation_gate", "src/context/source_candidate_remote_mutation_gate.py"),
                ("source_candidate_external_probe_bundle", "src/context/source_candidate_external_probe_bundle.py"),
                ("vector_indexing_job_plan", "src/context/vector_indexing_job_plan.py"),
                ("scheduler_deliberation_route_contract", "src/context/scheduler_deliberation_route_contract.py"),
            )
        ),
    )


def execute_github_external_artifact_smoke(plan: GitHubExternalArtifactPlan) -> int:
    if not plan.ready:
        for surface in plan.surfaces:
            if surface.required and not surface.path.exists():
                print(f"missing required surface: {surface.path}", file=sys.stderr)
        return 2

    plan.output_dir.mkdir(parents=True, exist_ok=True)
    _prepend_src(plan.repository_root)
    fixture = _load_or_create_fixture(plan)
    validation = validate_external_github_artifact_fixture(
        fixture,
        development_repository=plan.development_repository,
        expected_external_repository=plan.external_repository,
        repository_root=plan.repository_root,
    )

    if not validation["allowed"]:
        result = _blocked_result(plan, fixture, validation)
        plan.fixture_json.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        plan.result_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        plan.result_md.write_text(render_result_markdown(result), encoding="utf-8")
        print("==> github_external_artifact_smoke")
        print(render_result_markdown(result), end="")
        return 1

    builder_result = build_existing_builder_packets(fixture)
    packet = builder_result["packet"]
    graph = builder_result["graph"]
    dot_export = builder_result["dot_export"]
    review = builder_result["review"]
    rendered_review = builder_result["rendered_review"]
    orientation = builder_result["orientation"]

    result = {
        "schema": "missipy.github_project.external_artifact_smoke_result.v2",
        "status": "ok",
        "development_repository": plan.development_repository,
        "external_repository": fixture.get("repository"),
        "project_item_ref": fixture.get("project_item_ref"),
        "artifact_ref": fixture.get("artifact_ref"),
        "source_kind": fixture.get("source_kind"),
        "linked_post": (fixture.get("origin") or {}).get("linked_post") if isinstance(fixture.get("origin"), Mapping) else None,
        "github_exchange_role": "artifact exchange only",
        "publication_review_required": True,
        "publish_to_github": False,
        "external_call_performed": False,
        "performed_actions": {action: False for action in _FORBIDDEN_RUNTIME_ACTIONS},
        "boundary": "external GitHub project artifact accepted locally through existing builders; Autodoc development repo is not an ingestable idea source",
        "validation": validation,
        "reused_existing_surfaces": list(_REUSED_EXISTING_SURFACES),
        "existing_builders_used": list(_EXISTING_BUILDERS_USED),
        "source_candidate_ref": packet.source_candidate.source_ref,
        "sql_context_ref": packet.source_candidate.sql_record.context_ref,
        "plan_id": packet.plan.plan_id,
        "specialist_result_ref": packet.specialist_result.result_ref,
        "publication_ref": packet.publication.publication_ref,
        "review_ref": review.review_ref,
        "graph_snapshot_ref": graph.snapshot_ref,
        "dot_digest": review.dot_digest,
        "result_json": str(plan.result_json),
        "result_md": str(plan.result_md),
        "scenario_packet_json": str(plan.scenario_packet_json),
        "context_graph_json": str(plan.context_graph_json),
        "context_graph_dot": str(plan.context_graph_dot),
        "publication_review_json": str(plan.publication_review_json),
        "publication_review_md": str(plan.publication_review_md),
        "orientation": _to_mapping(orientation),
    }

    plan.fixture_json.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.scenario_packet_json.write_text(json.dumps(packet.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.context_graph_json.write_text(json.dumps(graph.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.context_graph_dot.write_text(dot_export.dot + "\n", encoding="utf-8")
    plan.publication_review_json.write_text(json.dumps(review.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.publication_review_md.write_text(rendered_review.markdown + "\n", encoding="utf-8")
    plan.result_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.result_md.write_text(render_result_markdown(result), encoding="utf-8")

    print("==> github_external_artifact_smoke")
    print(render_result_markdown(result), end="")
    return 0


def build_existing_builder_packets(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Build local-only packets through existing repo builders/contracts."""
    from context.context_graph_export import build_github_project_context_graph, export_context_graph_dot
    from context.context_variation_core import ContextExplorationBudget, ContextVariationAxis, build_context_exploration_plan
    from context.github_project_scenario import (
        GitHubProjectArtifact,
        GitHubProjectPublicationPolicy,
        build_github_context_objective,
        build_github_project_scenario_packet,
        build_github_source_candidate,
    )
    from context.github_publication_review import (
        GitHubPublicationReviewPolicy,
        build_github_publication_review,
        render_github_publication_review_markdown,
    )
    from context.server_oriented_deliberation_cycle import build_server_orientation_from_github_artifact
    from inference.llm_specialist_adapter import LLMSolutionCandidate, LLMSpecialistResult, LLMSpecialistTarget

    artifact = GitHubProjectArtifact(
        artifact_ref=str(fixture["artifact_ref"]),
        project_ref=str(fixture.get("project_ref", DEFAULT_PROJECT_REF)),
        item_ref=str(fixture["project_item_ref"]),
        title=str(fixture.get("title", "External idea fixture")),
        body=str(fixture.get("body", "External GitHub artifact fixture.")),
        author_ref=str(fixture.get("author_ref", "github:user/copilot")),
        metadata=(
            ("repository", str(fixture["repository"])),
            ("source_kind", str(fixture["source_kind"])),
            ("origin_kind", "github"),
            ("producer", "github_action_copilot"),
        ),
    )
    source_candidate = build_github_source_candidate(artifact)
    objective = build_github_context_objective(source_candidate)
    axis = ContextVariationAxis(
        axis_id="github-external-artifact-intake",
        label="GitHub external artifact intake",
        question="How should the local server enrich and respond to this external GitHub Project artifact?",
        tags=("github", "external-artifact", "local-only"),
    )
    budget = ContextExplorationBudget(max_variants=1, max_depth=1, max_specialist_calls=1, max_retrievals=1, max_wall_time_s=1.0)
    plan_id = f"github-external-plan-{_digest(artifact.artifact_ref)}"
    plan = build_context_exploration_plan(
        plan_id=plan_id,
        objective=objective,
        axes=(axis,),
        budget=budget,
        base_context_refs=(source_candidate.sql_record.context_ref,),
        payload_refs=(artifact.artifact_ref,),
        specialist_refs=("specialist:github-external-artifact-smoke",),
        cost_hint="tiny",
    )
    draft_id = f"draft-github-external-{_digest(plan.plan_id)}"
    candidate = LLMSolutionCandidate(
        candidate_ref=f"specialist:solution:{_digest(artifact.artifact_ref)}",
        draft_id=draft_id,
        title="Local synthesis candidate for external GitHub artifact",
        summary="Local-only candidate proving the GitHub artifact can flow through existing scenario/publication/review contracts.",
        evidence_refs=(source_candidate.sql_record.context_ref,),
        action_refs=(artifact.item_ref,),
        confidence=0.5,
        metadata=(("source", "0163_existing_builders_smoke"),),
    )
    specialist_result = LLMSpecialistResult(
        result_ref=f"specialist:result:{_digest(candidate.candidate_ref)}",
        prompt_ref=f"specialist:prompt:{_digest(plan.plan_id)}",
        draft_id=draft_id,
        target=LLMSpecialistTarget(target_ref="llm:local:specialist", backend_ref="llm:adapter:injected", model_ref="llm:model:fixture", runtime_mode="fixture"),
        candidates=(candidate,),
        raw_output_ref="artifact:local/0163/no-llm-executed",
        capped=False,
    )
    packet = build_github_project_scenario_packet(
        artifact=artifact,
        plan=plan,
        specialist_result=specialist_result,
        policy=GitHubProjectPublicationPolicy(max_candidates=1, max_summary_chars=512),
    )
    graph = build_github_project_context_graph(packet)
    dot_export = export_context_graph_dot(graph, graph_name="github_external_artifact_smoke_0163")
    review = build_github_publication_review(
        packet,
        graph,
        dot_export,
        policy=GitHubPublicationReviewPolicy(max_candidates=1, max_summary_chars=512, max_body_chars=2048),
    )
    rendered_review = render_github_publication_review_markdown(review)
    orientation = build_server_orientation_from_github_artifact(
        artifact=artifact,
        source_candidate=source_candidate,
        intent="local review of external GitHub Project artifact",
        requested_specialist_refs=("specialist:github-external-artifact-smoke",),
        requested_document_kinds=("analysis", "publication_review"),
        do_directives=("use existing builders", "keep publication review local"),
        avoid_directives=("do not ingest development repository", "do not call GitHub API"),
        context_refs=(source_candidate.sql_record.context_ref,),
    )
    return {
        "artifact": artifact,
        "source_candidate": source_candidate,
        "plan": plan,
        "specialist_result": specialist_result,
        "packet": packet,
        "graph": graph,
        "dot_export": dot_export,
        "review": review,
        "rendered_review": rendered_review,
        "orientation": orientation,
    }


def validate_external_github_artifact_fixture(
    fixture: Mapping[str, Any],
    *,
    development_repository: str,
    expected_external_repository: str,
    repository_root: Path,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    schema = str(fixture.get("schema", ""))
    repository = str(fixture.get("repository", ""))
    artifact_ref = str(fixture.get("artifact_ref", ""))
    project_ref = str(fixture.get("project_ref", DEFAULT_PROJECT_REF))
    project_item_ref = str(fixture.get("project_item_ref", ""))
    source_kind = str(fixture.get("source_kind", ""))

    if schema != "missipy.github_project.external_artifact_fixture.v1":
        issues.append(_issue("schema", "fixture schema must be missipy.github_project.external_artifact_fixture.v1"))

    if not repository:
        issues.append(_issue("repository_missing", "external artifact repository must be explicit"))
    elif not _is_owner_name(repository):
        issues.append(_issue("repository_format", "external artifact repository must use owner/name form"))
    elif repository == development_repository:
        issues.append(_issue("development_repo_ingestion", "development repository must not be used as idea artifact source"))
    elif repository != expected_external_repository:
        warnings.append(_issue("repository_differs_from_plan", f"fixture repository differs from plan repository: {repository}"))

    if not artifact_ref.startswith("github:"):
        issues.append(_issue("artifact_ref", "artifact_ref must use github: prefix"))
    if not project_ref.startswith("github:"):
        issues.append(_issue("project_ref", "project_ref must use github: prefix"))
    if not project_item_ref.startswith("github:"):
        issues.append(_issue("project_item_ref", "project_item_ref must use github: prefix"))
    if source_kind != "github_project_external_artifact":
        issues.append(_issue("source_kind", "source_kind must be github_project_external_artifact"))

    origin = fixture.get("origin")
    if not isinstance(origin, Mapping):
        issues.append(_issue("origin", "origin must be a mapping"))
    else:
        if origin.get("kind") != "github":
            issues.append(_issue("origin_kind", "origin.kind must be github"))
        if origin.get("producer") not in {"github_action_copilot", "github_action", "copilot"}:
            warnings.append(_issue("origin_producer", "origin.producer should identify GitHub Action/Copilot"))
        if origin.get("linked_post") != project_item_ref:
            issues.append(_issue("linked_post", "origin.linked_post must point to the source project item"))

    forbidden_text = json.dumps(fixture, ensure_ascii=False, sort_keys=True)
    forbidden_fragments = (
        str(repository_root),
        "/home/eric/projet/git/autodoc",
        "patch/",
        "patch.diff",
        "apply_patch_queue",
        "tools/run_",
        "tests/tools/",
        "tests/rules/",
        "artifact:local/",
        "sql:artifact/vector-indexing/",
        "sql:smoke/vector-indexing/",
    )
    for fragment in forbidden_fragments:
        if fragment in forbidden_text:
            issues.append(_issue("dev_repo_material", f"fixture must not contain development repository material: {fragment}"))

    return {
        "allowed": not issues,
        "issues": issues,
        "warnings": warnings,
        "repository": repository,
        "development_repository": development_repository,
        "external_repository_required": True,
        "github_exchange_role": "artifact exchange only",
        "publish_to_github": False,
        "external_call_performed": False,
    }


def render_result_markdown(result: Mapping[str, Any]) -> str:
    validation = result.get("validation", {})
    issues = validation.get("issues", []) if isinstance(validation, Mapping) else []
    warnings = validation.get("warnings", []) if isinstance(validation, Mapping) else []

    lines = [
        "# GitHub external artifact smoke result",
        "",
        f"status: `{result.get('status')}`",
        f"development_repository: `{result.get('development_repository')}`",
        f"external_repository: `{result.get('external_repository')}`",
        f"project_item_ref: `{result.get('project_item_ref')}`",
        f"artifact_ref: `{result.get('artifact_ref')}`",
        f"source_candidate_ref: `{result.get('source_candidate_ref')}`",
        f"sql_context_ref: `{result.get('sql_context_ref')}`",
        f"publication_ref: `{result.get('publication_ref')}`",
        f"review_ref: `{result.get('review_ref')}`",
        f"graph_snapshot_ref: `{result.get('graph_snapshot_ref')}`",
        f"github_exchange_role: `{result.get('github_exchange_role')}`",
        f"publication_review_required: `{result.get('publication_review_required')}`",
        f"publish_to_github: `{result.get('publish_to_github')}`",
        f"external_call_performed: `{result.get('external_call_performed')}`",
        "",
        "## Existing builders used",
        "",
    ]
    for name in result.get("existing_builders_used", []):
        lines.append(f"- `{name}`")
    lines.extend(["", "## Issues", ""])
    if issues:
        for issue in issues:
            lines.append(f"- `{issue.get('code')}`: {issue.get('message')}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for warning in warnings:
            lines.append(f"- `{warning.get('code')}`: {warning.get('message')}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "boundary: `external GitHub Project artifact only; Autodoc dev repo is infrastructure`",
        "",
    ])
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local-only GitHub external artifact boundary smoke.")
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--fixture-json", type=Path, default=None)
    parser.add_argument("--development-repository", default=DEFAULT_DEVELOPMENT_REPOSITORY)
    parser.add_argument("--external-repository", default=DEFAULT_EXTERNAL_REPOSITORY)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    plan = build_github_external_artifact_plan(
        args.repository_root,
        output_dir=args.output_dir,
        fixture_json=args.fixture_json,
        development_repository=args.development_repository,
        external_repository=args.external_repository,
        execute=args.execute,
    )

    if args.format == "json":
        print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))
    else:
        print(plan.to_markdown(), end="")

    if not args.execute:
        return 0 if plan.ready else 2

    return execute_github_external_artifact_smoke(plan)


def _load_or_create_fixture(plan: GitHubExternalArtifactPlan) -> Mapping[str, Any]:
    if plan.fixture_json.exists():
        loaded = json.loads(plan.fixture_json.read_text(encoding="utf-8"))
        if not isinstance(loaded, Mapping):
            raise ValueError("fixture JSON must be an object")
        return loaded

    return {
        "schema": "missipy.github_project.external_artifact_fixture.v1",
        "repository": plan.external_repository,
        "project_ref": DEFAULT_PROJECT_REF,
        "project_item_ref": DEFAULT_PROJECT_ITEM_REF,
        "artifact_ref": DEFAULT_ARTIFACT_REF,
        "source_kind": "github_project_external_artifact",
        "title": "External idea fixture 0162",
        "body": "Artifact produced by GitHub Action/Copilot for local server intake smoke.",
        "author_ref": "github:user/copilot",
        "origin": {
            "kind": "github",
            "producer": "github_action_copilot",
            "linked_post": DEFAULT_PROJECT_ITEM_REF,
        },
    }


def _blocked_result(plan: GitHubExternalArtifactPlan, fixture: Mapping[str, Any], validation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "missipy.github_project.external_artifact_smoke_result.v2",
        "status": "blocked",
        "development_repository": plan.development_repository,
        "external_repository": fixture.get("repository"),
        "project_item_ref": fixture.get("project_item_ref"),
        "artifact_ref": fixture.get("artifact_ref"),
        "github_exchange_role": "artifact exchange only",
        "publication_review_required": False,
        "publish_to_github": False,
        "external_call_performed": False,
        "performed_actions": {action: False for action in _FORBIDDEN_RUNTIME_ACTIONS},
        "validation": validation,
        "existing_builders_used": [],
        "boundary": "external GitHub project artifact rejected before builders because source boundary failed",
    }


def _resolve_repo_path(root: Path, path: Path | None) -> Path:
    if path is None:
        raise ValueError("path must not be None")
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded
    return root / expanded


def _prepend_src(root: Path) -> None:
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _is_owner_name(repository: str) -> bool:
    if repository.count("/") != 1:
        return False
    owner, name = repository.split("/", 1)
    return bool(owner.strip()) and bool(name.strip())


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _to_mapping(value: object) -> object:
    mapper = getattr(value, "to_mapping", None)
    if callable(mapper):
        return mapper()
    return repr(value)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
