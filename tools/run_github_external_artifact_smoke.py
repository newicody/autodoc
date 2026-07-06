#!/usr/bin/env python3
"""Local-only GitHub external artifact smoke.

0162 corrects the source boundary after the local patch-ingestion detour:
Autodoc/MissiPy's development repository is infrastructure, not the business
idea corpus. The ingestable source is an explicit external GitHub Project
repository that produces artifacts through GitHub Action/Copilot.

This tool performs no SQL write, Qdrant write, GitHub API call, external
network call, Scheduler execution, LLM execution, or OpenVINO execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


DEFAULT_OUTPUT_DIR = ".var/smoke/artifacts/0162"
DEFAULT_DEVELOPMENT_REPOSITORY = "newicody/autodoc"
DEFAULT_EXTERNAL_REPOSITORY = "newicody/autodoc-ideas"
DEFAULT_PROJECT_ITEM_REF = "github:project-item/demo-0162"
DEFAULT_ARTIFACT_REF = "github:artifact/demo-0162"

EXISTING_SURFACES = (
    "src/context/github_project_scenario.py",
    "src/context/server_oriented_deliberation_cycle.py",
    "src/context/github_publication_review.py",
    "src/context/source_candidate_github_projection_payload.py",
    "src/context/source_candidate_external_projection_contract.py",
    "src/context/source_candidate_read_only_external_probe.py",
    "src/context/source_candidate_remote_mutation_gate.py",
    "src/context/source_candidate_external_probe_bundle.py",
    "src/context/vector_indexing_job_plan.py",
    "src/context/scheduler_deliberation_route_contract.py",
)

FORBIDDEN_ACTIONS = (
    "no_sql_write",
    "no_qdrant_write",
    "no_github_api_call",
    "no_external_network",
    "no_scheduler_execution",
    "no_llm_execution",
    "no_openvino_execution",
    "no_autodoc_dev_repo_ingestion",
)


@dataclass(frozen=True, slots=True)
class Surface:
    key: str
    path: Path
    reason: str

    def to_mapping(self, *, root: Path) -> dict[str, Any]:
        return {
            "key": self.key,
            "path": _display_path(self.path, root=root),
            "reason": self.reason,
            "required": True,
            "status": "present" if self.path.exists() else "missing",
        }


@dataclass(frozen=True, slots=True)
class Plan:
    repository_root: Path
    output_dir: Path
    fixture_json: Path
    result_json: Path
    result_md: Path
    publication_review_json: Path
    publication_review_md: Path
    development_repository: str
    external_repository: str
    execute: bool
    surfaces: tuple[Surface, ...]

    @property
    def ready(self) -> bool:
        return all(surface.path.exists() for surface in self.surfaces)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.repository_root),
            "output_dir": str(self.output_dir),
            "fixture_json": str(self.fixture_json),
            "result_json": str(self.result_json),
            "result_md": str(self.result_md),
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
                *FORBIDDEN_ACTIONS,
            ],
            "reused_existing_surfaces": list(EXISTING_SURFACES),
        }

    def to_markdown(self) -> str:
        lines = [
            "# GitHub external artifact smoke plan",
            "",
            f"development_repository: `{self.development_repository}`",
            f"external_repository: `{self.external_repository}`",
            f"fixture_json: `{self.fixture_json}`",
            f"execute: `{str(self.execute).lower()}`",
            f"ready_for_github_external_artifact_smoke: `{str(self.ready).lower()}`",
            "",
            "## Existing surfaces",
            "",
            "| key | status | path | reason |",
            "| --- | --- | --- | --- |",
        ]
        for surface in self.surfaces:
            row = surface.to_mapping(root=self.repository_root)
            lines.append(f"| {row['key']} | {row['status']} | `{row['path']}` | {row['reason']} |")
        lines.extend([
            "",
            "## Boundary",
            "",
            "- external artifact source must be explicit",
            "- external artifact repository must differ from the Autodoc development repository",
            "- no SQL write, no Qdrant write, no GitHub API call, no external network",
            "- output is a local publication review packet only",
            "",
        ])
        return "\n".join(lines)


def build_plan(
    root: Path,
    *,
    output_dir: Path,
    fixture_json: Path | None,
    development_repository: str,
    external_repository: str,
    execute: bool,
) -> Plan:
    root = root.resolve()
    output_dir = _resolve(root, output_dir)
    fixture = _resolve(root, fixture_json) if fixture_json is not None else output_dir / "github_external_artifact_fixture.json"
    surfaces = tuple(
        Surface(
            key=Path(path).stem,
            path=root / path,
            reason="existing GitHub/external artifact exchange surface",
        )
        for path in EXISTING_SURFACES
    )
    return Plan(
        repository_root=root,
        output_dir=output_dir,
        fixture_json=fixture,
        result_json=output_dir / "github_external_artifact_smoke_result.json",
        result_md=output_dir / "github_external_artifact_smoke_report.md",
        publication_review_json=output_dir / "github_publication_review_packet.json",
        publication_review_md=output_dir / "github_publication_review_packet.md",
        development_repository=development_repository,
        external_repository=external_repository,
        execute=execute,
        surfaces=surfaces,
    )


def execute_plan(plan: Plan) -> int:
    if not plan.ready:
        for surface in plan.surfaces:
            if not surface.path.exists():
                print(f"missing required surface: {surface.path}", file=sys.stderr)
        return 2

    plan.output_dir.mkdir(parents=True, exist_ok=True)
    fixture = load_or_create_fixture(plan)
    validation = validate_fixture(
        fixture,
        development_repository=plan.development_repository,
        expected_external_repository=plan.external_repository,
        repository_root=plan.repository_root,
    )
    review = build_publication_review_packet(fixture, validation)
    result = {
        "schema": "missipy.github_project.external_artifact_smoke_result.v1",
        "status": "ok" if validation["allowed"] else "blocked",
        "development_repository": plan.development_repository,
        "external_repository": fixture.get("repository"),
        "project_item_ref": fixture.get("project_item_ref"),
        "artifact_ref": fixture.get("artifact_ref"),
        "source_kind": fixture.get("source_kind"),
        "github_exchange_role": "artifact exchange only",
        "publication_review_required": True,
        "publish_to_github": False,
        "external_call_performed": False,
        "runtime_actions": {action: False for action in FORBIDDEN_ACTIONS},
        "boundary": "external GitHub project artifact accepted locally; Autodoc development repo is not an ingestable idea source",
        "validation": validation,
        "reused_existing_surfaces": list(EXISTING_SURFACES),
        "result_json": str(plan.result_json),
        "result_md": str(plan.result_md),
        "publication_review_json": str(plan.publication_review_json),
        "publication_review_md": str(plan.publication_review_md),
    }

    plan.fixture_json.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.publication_review_json.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.publication_review_md.write_text(render_review_markdown(review), encoding="utf-8")
    plan.result_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.result_md.write_text(render_result_markdown(result), encoding="utf-8")

    print("==> github_external_artifact_smoke")
    print(render_result_markdown(result), end="")
    return 0 if result["status"] == "ok" else 1


def validate_fixture(
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
    project_item_ref = str(fixture.get("project_item_ref", ""))
    source_kind = str(fixture.get("source_kind", ""))

    if schema != "missipy.github_project.external_artifact_fixture.v1":
        issues.append(issue("schema", "fixture schema must be missipy.github_project.external_artifact_fixture.v1"))
    if not repository:
        issues.append(issue("repository_missing", "external artifact repository must be explicit"))
    elif not owner_name(repository):
        issues.append(issue("repository_format", "external artifact repository must use owner/name form"))
    elif repository == development_repository:
        issues.append(issue("development_repo_ingestion", "development repository must not be used as idea artifact source"))
    elif repository != expected_external_repository:
        warnings.append(issue("repository_differs_from_plan", f"fixture repository differs from plan repository: {repository}"))

    if not artifact_ref.startswith("github:"):
        issues.append(issue("artifact_ref", "artifact_ref must use github: prefix"))
    if not project_item_ref.startswith("github:"):
        issues.append(issue("project_item_ref", "project_item_ref must use github: prefix"))
    if source_kind != "github_project_external_artifact":
        issues.append(issue("source_kind", "source_kind must be github_project_external_artifact"))

    origin = fixture.get("origin")
    if not isinstance(origin, Mapping):
        issues.append(issue("origin", "origin must be a mapping"))
    else:
        if origin.get("kind") != "github":
            issues.append(issue("origin_kind", "origin.kind must be github"))
        if origin.get("linked_post") != project_item_ref:
            issues.append(issue("linked_post", "origin.linked_post must point to the source project item"))

    text = json.dumps(fixture, ensure_ascii=False, sort_keys=True)
    forbidden = (
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
    for fragment in forbidden:
        if fragment in text:
            issues.append(issue("dev_repo_material", f"fixture must not contain development repository material: {fragment}"))

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


def build_publication_review_packet(fixture: Mapping[str, Any], validation: Mapping[str, Any]) -> dict[str, Any]:
    artifact_ref = str(fixture.get("artifact_ref", DEFAULT_ARTIFACT_REF))
    project_item_ref = str(fixture.get("project_item_ref", DEFAULT_PROJECT_ITEM_REF))
    return {
        "schema": "missipy.github_project.publication_review_stub.v1",
        "review_ref": f"github-review:publication:{digest(artifact_ref + project_item_ref)}",
        "artifact_ref": artifact_ref,
        "target_ref": f"github:project-result:{digest(project_item_ref)}",
        "linked_post": project_item_ref,
        "publish_to_github": False,
        "external_adapter": "required_after_review",
        "external_call_performed": False,
        "action_refs": [artifact_ref, project_item_ref],
        "summary": "Local review packet only; no GitHub mutation was performed.",
        "allowed": bool(validation.get("allowed")),
        "validation_issue_count": len(validation.get("issues", [])),
    }


def load_or_create_fixture(plan: Plan) -> Mapping[str, Any]:
    if plan.fixture_json.exists():
        loaded = json.loads(plan.fixture_json.read_text(encoding="utf-8"))
        if not isinstance(loaded, Mapping):
            raise ValueError("fixture JSON must be an object")
        return loaded
    return {
        "schema": "missipy.github_project.external_artifact_fixture.v1",
        "repository": plan.external_repository,
        "project_item_ref": DEFAULT_PROJECT_ITEM_REF,
        "artifact_ref": DEFAULT_ARTIFACT_REF,
        "source_kind": "github_project_external_artifact",
        "title": "External idea fixture 0162",
        "body": "Artifact produced by GitHub Action/Copilot for local server intake smoke.",
        "origin": {
            "kind": "github",
            "producer": "github_action_copilot",
            "linked_post": DEFAULT_PROJECT_ITEM_REF,
        },
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
        f"publish_to_github: `{result.get('publish_to_github')}`",
        f"external_call_performed: `{result.get('external_call_performed')}`",
        "",
        "## Issues",
        "",
    ]
    lines.extend([f"- `{item.get('code')}`: {item.get('message')}" for item in issues] or ["- none"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- `{item.get('code')}`: {item.get('message')}" for item in warnings] or ["- none"])
    lines.extend(["", "boundary: `external GitHub Project artifact only; Autodoc dev repo is infrastructure`", ""])
    return "\n".join(lines)


def render_review_markdown(packet: Mapping[str, Any]) -> str:
    return "\n".join([
        "# GitHub publication review packet",
        "",
        f"review_ref: `{packet.get('review_ref')}`",
        f"artifact_ref: `{packet.get('artifact_ref')}`",
        f"target_ref: `{packet.get('target_ref')}`",
        f"linked_post: `{packet.get('linked_post')}`",
        f"publish_to_github: `{packet.get('publish_to_github')}`",
        f"external_adapter: `{packet.get('external_adapter')}`",
        f"external_call_performed: `{packet.get('external_call_performed')}`",
        "",
        "This packet is local-only. A future GitHub adapter may publish only after review.",
        "",
    ])


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
    plan = build_plan(
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
    return execute_plan(plan)


def _resolve(root: Path, path: Path) -> Path:
    path = path.expanduser()
    return path if path.is_absolute() else root / path


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def owner_name(value: str) -> bool:
    if value.count("/") != 1:
        return False
    owner, repo = value.split("/", 1)
    return bool(owner.strip()) and bool(repo.strip())


def issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    raise SystemExit(main())
