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


def _fixture(repository: str = "newicody/autodoc-ideas", body: str = "GitHub Action artifact") -> dict[str, object]:
    return {
        "schema": "missipy.github_project.external_artifact_fixture.v1",
        "repository": repository,
        "project_item_ref": "github:project-item/demo-0162",
        "artifact_ref": "github:artifact/demo-0162",
        "source_kind": "github_project_external_artifact",
        "title": "idea",
        "body": body,
        "origin": {
            "kind": "github",
            "producer": "github_action_copilot",
            "linked_post": "github:project-item/demo-0162",
        },
    }


def test_0162_accepts_external_github_project_artifact_fixture() -> None:
    module = _load_module()
    validation = module.validate_fixture(
        _fixture(),
        development_repository="newicody/autodoc",
        expected_external_repository="newicody/autodoc-ideas",
        repository_root=ROOT,
    )

    assert validation["allowed"] is True
    assert validation["issues"] == []


def test_0162_rejects_autodoc_development_repo_as_idea_source() -> None:
    module = _load_module()
    validation = module.validate_fixture(
        _fixture("newicody/autodoc"),
        development_repository="newicody/autodoc",
        expected_external_repository="newicody/autodoc-ideas",
        repository_root=ROOT,
    )

    assert validation["allowed"] is False
    assert any(issue["code"] == "development_repo_ingestion" for issue in validation["issues"])


def test_0162_rejects_dev_repo_material_inside_fixture() -> None:
    module = _load_module()
    validation = module.validate_fixture(
        _fixture(body="please inspect patch.diff and tools/run_local_artifact_vector_indexing_runner.py"),
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

    assert result["status"] == "ok"
    assert result["external_repository"] == "newicody/autodoc-ideas"
    assert result["publish_to_github"] is False
    assert result["external_call_performed"] is False
    assert review["publish_to_github"] is False
    assert review["external_adapter"] == "required_after_review"
