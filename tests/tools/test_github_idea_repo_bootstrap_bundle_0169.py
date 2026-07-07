from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_github_idea_repo_bootstrap_bundle.py"


def test_0169_bootstrap_bundle_stages_templates(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--repository",
            "newicody/autodoc-ideas",
            "--project-url",
            "https://github.com/users/newicody/projects/2",
            "--output-dir",
            str(tmp_path / "bundle"),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    report = json.loads(completed.stdout)

    assert report["status"] == "ok"
    assert report["github_api_called"] is False
    assert report["remote_mutation_performed"] is False
    targets = {item["target_path"] for item in report["files"]}
    assert ".github/workflows/autodoc-ticket-artifact.yml" in targets
    assert ".github/ISSUE_TEMPLATE/autodoc_task.yml" in targets
    assert "scripts/build_autodoc_ticket_artifact.py" in targets
    for item in report["files"]:
        assert Path(item["staged_path"]).exists()
        assert item["external_written"] is False


def test_0169_bootstrap_bundle_writes_explicit_external_repo_root(tmp_path: Path) -> None:
    external = tmp_path / "autodoc-ideas"
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--repository",
            "newicody/autodoc-ideas",
            "--project-url",
            "https://github.com/users/newicody/projects/2",
            "--output-dir",
            str(tmp_path / "bundle"),
            "--external-repo-root",
            str(external),
            "--write",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    report = json.loads(completed.stdout)

    assert report["status"] == "ok"
    assert report["write_requested"] is True
    assert (external / ".github" / "workflows" / "autodoc-ticket-artifact.yml").exists()
    assert (external / ".github" / "ISSUE_TEMPLATE" / "autodoc_task.yml").exists()
    assert (external / "scripts" / "build_autodoc_ticket_artifact.py").exists()
    assert all(item["external_written"] is True for item in report["files"])


def test_0169_bootstrap_rejects_development_repository(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--repository",
            "newicody/autodoc",
            "--project-url",
            "https://github.com/users/newicody/projects/2",
            "--output-dir",
            str(tmp_path / "bundle"),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 1
    report = json.loads(completed.stdout)
    assert report["status"] == "blocked"
    assert {issue["code"] for issue in report["issues"]} == {"development_repository_rejected"}
