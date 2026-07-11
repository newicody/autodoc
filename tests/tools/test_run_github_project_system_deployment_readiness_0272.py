import json
from pathlib import Path
import subprocess
import sys


def test_cli_fixture_is_green(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    workflow = (root / "templates/github/autodoc-ticket-artifact.yml").read_text()
    builder = (root / "templates/github/scripts/build_autodoc_ticket_artifact.py").read_text()
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({
        "project": {"id": "PVT_kwHOA3ouXM4Ba3Ar", "number": 2,
                    "url": "https://github.com/users/newicody/projects/2"},
        "workflow": {"state": "active", "path": ".github/workflows/autodoc-ticket-artifact.yml"},
        "workflow_content": workflow,
        "builder_content": builder,
    }))
    output = tmp_path / "report.json"
    completed = subprocess.run([
        sys.executable, "tools/run_github_project_system_deployment_readiness_0272.py",
        "--config", "config/github_project_v2_query_only.example.ini",
        "--execute", "--policy-decision-id", "policy:test:fixture",
        "--fixture-json", str(fixture), "--output", str(output), "--format", "summary",
    ], cwd=root, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(output.read_text())
    assert payload["system_ready"] is True
    assert payload["external_call_performed"] is False
    assert payload["installation_performed"] is False
    assert payload["deployment_performed"] is False
