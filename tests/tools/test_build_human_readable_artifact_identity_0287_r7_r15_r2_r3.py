from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


def _load_tool():
    path = (
        Path(__file__).resolve().parents[2]
        / "templates/github/projects-repository/scripts"
        / "build_human_readable_artifact_identity.py"
    )
    spec = importlib.util.spec_from_file_location("artifact_identity_tool", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tool_writes_identity_and_github_outputs(tmp_path, monkeypatch) -> None:
    issue = tmp_path / "issue.json"
    request = tmp_path / "authoritative_request.json"
    advisory = tmp_path / "copilot_advisory.json"
    manifest = tmp_path / "dual_artifact_manifest.json"
    output = tmp_path / "artifact_identity.json"
    github_output = tmp_path / "github-output.txt"
    issue.write_text(json.dumps({"number": 9, "title": "Analyse du moteur E5"}))
    request.write_text(
        json.dumps(
            {
                "repository": "newicody/projects",
                "issue_number": 9,
                "title": "Analyse du moteur E5",
                "artifact_ref": "github-request:r",
            }
        )
    )
    advisory.write_text(
        json.dumps(
            {
                "artifact_ref": "github-advisory:a",
                "request_artifact_ref": "github-request:r",
            }
        )
    )
    manifest.write_text(
        json.dumps(
            {
                "manifest_ref": "github-dual-manifest:m",
                "request_artifact_ref": "github-request:r",
                "advisory_artifact_ref": "github-advisory:a",
            }
        )
    )
    monkeypatch.setenv("AUTODOC_ISSUE_JSON", str(issue))
    monkeypatch.setenv("AUTODOC_REQUEST", str(request))
    monkeypatch.setenv("AUTODOC_ADVISORY", str(advisory))
    monkeypatch.setenv("AUTODOC_MANIFEST", str(manifest))
    monkeypatch.setenv("AUTODOC_ARTIFACT_IDENTITY", str(output))
    monkeypatch.setenv("GITHUB_REPOSITORY", "newicody/projects")
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    assert _load_tool().main() == 0
    payload = json.loads(output.read_text())
    assert payload["identities"][1]["display_title"] == (
        "Premier avis Copilot — Analyse du moteur E5"
    )
    outputs = github_output.read_text()
    assert "request_name=autodoc-i9-analyse-du-moteur-e5--authoritative-request-v1" in outputs
    assert "advisory_name=autodoc-i9-analyse-du-moteur-e5--copilot-advisory-v2" in outputs
    assert "manifest_name=autodoc-i9-analyse-du-moteur-e5--run-manifest-v1" in outputs
