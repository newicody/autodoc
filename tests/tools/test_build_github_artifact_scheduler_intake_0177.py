from pathlib import Path
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_github_artifact_scheduler_intake.py"


def _write_input(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "observation_ref": "event:github-artifact-dataset:tool",
                "repository": "newicody/autodoc-ideas",
                "run_id": "run0177tool",
                "artifact_id": "artifact0177tool",
                "dataset_root_ref": "server-dataset:github-artifacts",
                "status": "queued",
                "priority": 50,
                "requested_at": "2026-07-07T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )


def test_0177_tool_builds_unauthorized_candidate(tmp_path: Path) -> None:
    input_path = tmp_path / "intake.json"
    _write_input(input_path)

    completed = subprocess.run(
        [sys.executable, str(TOOL), "--input", str(input_path), "--format", "json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    report = json.loads(completed.stdout)
    assert report["authorized"] is False
    assert report["scheduler_route_request"] is None
    assert report["scheduler_modified"] is False


def test_0177_tool_builds_authorized_route_request_only_with_policy(tmp_path: Path) -> None:
    input_path = tmp_path / "intake.json"
    _write_input(input_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--input",
            str(input_path),
            "--authorized",
            "--policy-decision-id",
            "policy:allow:github-artifact:tool",
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
    assert report["authorized"] is True
    assert report["scheduler_route_request"]["authorized"] is True
    assert report["scheduler_route_request"]["policy_decision_id"] == "policy:allow:github-artifact:tool"
