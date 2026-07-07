from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_github_idea_repo_attachment_bootstrap_bundle.py"


def test_0170_attachment_bootstrap_stages_templates(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--repository",
            "newicody/autodoc-ideas",
            "--output-dir",
            str(tmp_path / "stage"),
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
    assert (tmp_path / "stage" / ".github" / "workflows" / "autodoc-attachment-manifest.yml").exists()
    assert (tmp_path / "stage" / "scripts" / "build_autodoc_issue_attachment_manifest.py").exists()


def test_0170_attachment_bootstrap_rejects_development_repository(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--repository",
            "newicody/autodoc",
            "--output-dir",
            str(tmp_path / "stage"),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    report = json.loads(completed.stdout)

    assert completed.returncode == 1
    assert report["status"] == "blocked"
    assert report["issues"][0]["code"] == "development_repository_rejected"
