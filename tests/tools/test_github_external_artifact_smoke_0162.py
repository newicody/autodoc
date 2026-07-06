from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
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


def test_0162_accepts_external_github_project_artifact_fixture() -> None:
    module = _load_module()
    fixture = {
        "schema": "missipy.github_project.external_artifact_fixture.v1",
        "repository": "newicody/autodoc-ideas",
        "project_ref": "github:project/autodoc-ideas",
        "project_item_ref": "github:project-item/demo-0162",
        "artifact_ref": "github:artifact/demo-0162",
        "source_kind": "github_project_external_artifact",
        "title": "idea",
        "body": "GitHub Action/Copilot artifact",
        "origin": {
            "kind": "github",
            "producer": "github_action_copilot",
            "linked_post": "github:project-item/demo-0162",
        },
    }

    validation = module.validate_external_github_artifact_fixture(
        fixture,
        development_repository="newicody/autodoc",
        expected_external_repository="newicody/autodoc-ideas",
        repository_root=ROOT,
    )

    assert validation["allowed"] is True
    assert validation["issues"] == []


def test_0162_rejects_autodoc_development_repo_as_idea_source() -> None:
    module = _load_module()
    fixture = {
        "schema": "missipy.github_project.external_artifact_fixture.v1",
        "repository": "newicody/autodoc",
        "project_ref": "github:project/autodoc",
        "project_item_ref": "github:project-item/demo-0162",
        "artifact_ref": "github:artifact/demo-0162",
        "source_kind": "github_project_external_artifact",
        "origin": {"kind": "github", "producer": "github_action_copilot", "linked_post": "github:project-item/demo-0162"},
    }

    validation = module.validate_external_github_artifact_fixture(
        fixture,
        development_repository="newicody/autodoc",
        expected_external_repository="newicody/autodoc-ideas",
        repository_root=ROOT,
    )

    assert validation["allowed"] is False
    assert any(issue["code"] == "development_repo_ingestion" for issue in validation["issues"])


def test_0162_rejects_dev_repo_material_inside_fixture() -> None:
    module = _load_module()
    fixture = {
        "schema": "missipy.github_project.external_artifact_fixture.v1",
        "repository": "newicody/autodoc-ideas",
        "project_ref": "github:project/autodoc-ideas",
        "project_item_ref": "github:project-item/demo-0162",
        "artifact_ref": "github:artifact/demo-0162",
        "source_kind": "github_project_external_artifact",
        "body": "please inspect patch.diff from tools/run_local_artifact_vector_indexing_runner.py",
        "origin": {"kind": "github", "producer": "github_action_copilot", "linked_post": "github:project-item/demo-0162"},
    }

    validation = module.validate_external_github_artifact_fixture(
        fixture,
        development_repository="newicody/autodoc",
        expected_external_repository="newicody/autodoc-ideas",
        repository_root=ROOT,
    )

    assert validation["allowed"] is False
    assert any(issue["code"] == "dev_repo_material" for issue in validation["issues"])


def test_0162_cli_execute_writes_local_review_without_remote_mutation(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--output-dir",
            str(tmp_path / "out"),
            "--development-repository",
            "newicody/autodoc",
            "--external-repository",
            "newicody/autodoc-ideas",
            "--execute",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert "ready_for_github_external_artifact_smoke" in completed.stdout

    result = json.loads((tmp_path / "out" / "github_external_artifact_smoke_result.json").read_text(encoding="utf-8"))
    review = json.loads((tmp_path / "out" / "github_publication_review_packet.json").read_text(encoding="utf-8"))
    scenario = json.loads((tmp_path / "out" / "github_project_scenario_packet.json").read_text(encoding="utf-8"))
    graph = json.loads((tmp_path / "out" / "github_project_context_graph.json").read_text(encoding="utf-8"))

    assert result["status"] == "ok"
    assert result["external_repository"] == "newicody/autodoc-ideas"
    assert result["publish_to_github"] is False
    assert result["external_call_performed"] is False
    assert result["performed_actions"]["sql_write"] is False
    assert result["performed_actions"]["qdrant_write"] is False
    assert result["performed_actions"]["github_api_call"] is False
    assert result["source_candidate_ref"].startswith("artifact:github-source:")
    assert result["sql_context_ref"].startswith("sql:")
    assert result["publication_ref"].startswith("github:project-publication:")
    assert result["review_ref"].startswith("github-review:publication:")
    assert "GitHubProjectArtifact" in result["existing_builders_used"]
    assert "build_github_project_scenario_packet" in result["existing_builders_used"]
    assert "build_github_publication_review" in result["existing_builders_used"]
    assert review["runtime_import"] == "none; external GitHub adapter posts only after review"
    assert scenario["schema"] == "missipy.github_project.scenario.v1"
    assert graph["schema"] == "missipy.context_graph.snapshot.v1"
    assert (tmp_path / "out" / "github_project_context_graph.dot").exists()
