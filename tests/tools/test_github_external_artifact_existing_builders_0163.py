from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_github_external_artifact_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_github_external_artifact_smoke", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_0163_builds_existing_github_scenario_publication_and_review(tmp_path: Path) -> None:
    module = _load_module()
    sys.path.insert(0, str(ROOT / "src"))

    fixture = {
        "schema": "missipy.github_project.external_artifact_fixture.v1",
        "repository": "newicody/autodoc-ideas",
        "project_ref": "github:project/autodoc-ideas",
        "project_item_ref": "github:project-item/demo-0163",
        "artifact_ref": "github:artifact/demo-0163",
        "source_kind": "github_project_external_artifact",
        "title": "External idea fixture 0163",
        "body": "Artifact produced by GitHub Action/Copilot for existing-builder smoke.",
        "origin": {"kind": "github", "producer": "github_action_copilot", "linked_post": "github:project-item/demo-0163"},
    }

    built = module.build_existing_builder_packets(fixture)
    packet = built["packet"]
    review = built["review"]
    dot_export = built["dot_export"]

    assert packet.to_mapping()["schema"] == "missipy.github_project.scenario.v1"
    assert packet.artifact.artifact_ref == "github:artifact/demo-0163"
    assert packet.source_candidate.sql_record.kind == "github_artifact"
    assert packet.publication.publication_ref.startswith("github:project-publication:")
    assert review.review_ref.startswith("github-review:publication:")
    assert review.publication_ref == packet.publication.publication_ref
    assert dot_export.snapshot_ref == review.graph_snapshot_ref
    assert "github_publication" in dot_export.dot


def test_0163_plan_reports_existing_builders(tmp_path: Path) -> None:
    module = _load_module()
    fixture_json = tmp_path / "fixture.json"
    fixture_json.write_text(json.dumps({"schema": "missipy.github_project.external_artifact_fixture.v1"}), encoding="utf-8")

    plan = module.build_github_external_artifact_plan(
        ROOT,
        output_dir=tmp_path / "out",
        fixture_json=fixture_json,
        development_repository="newicody/autodoc",
        external_repository="newicody/autodoc-ideas",
        execute=False,
    )
    payload = plan.to_mapping()

    assert payload["ready_for_github_external_artifact_smoke"] is True
    assert "GitHubProjectArtifact" in payload["existing_builders_used"]
    assert "build_github_project_scenario_packet" in payload["existing_builders_used"]
    assert "build_github_publication_review" in payload["existing_builders_used"]
    assert "src/context/github_project_scenario.py" in payload["reused_existing_surfaces"]
