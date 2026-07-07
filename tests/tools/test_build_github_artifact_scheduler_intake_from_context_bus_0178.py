from pathlib import Path
import json
import subprocess
import sys

from context.github_artifact_dataset_bus_observation import append_github_artifact_dataset_bus_observation


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_github_artifact_scheduler_intake_from_context_bus.py"


def test_0178_tool_reads_context_bus_jsonl(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(
        runtime_root=tmp_path,
        raw={
            "report_ref": "report:github-artifact:tool0178",
            "repository": "newicody/autodoc-ideas",
            "run_id": "run0178tool",
            "artifact_id": "artifact0178tool",
            "status": "queued",
            "dataset_root_ref": "server-dataset:github-artifacts",
            "raw_count": 1,
            "queued_count": 1,
            "failed_count": 0,
            "occurred_at": "2026-07-07T00:00:00Z",
        },
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--context-bus",
            str(tmp_path / "context.bus.jsonl"),
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
    assert len(report) == 1
    assert report[0]["authorized"] is False
    assert report[0]["scheduler_route_request"] is None


def test_0178_tool_authorized_requires_policy_id(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(
        runtime_root=tmp_path,
        raw={
            "report_ref": "report:github-artifact:tool0178auth",
            "repository": "newicody/autodoc-ideas",
            "run_id": "run0178toolauth",
            "artifact_id": "artifact0178toolauth",
            "status": "queued",
            "dataset_root_ref": "server-dataset:github-artifacts",
            "raw_count": 1,
            "queued_count": 1,
            "failed_count": 0,
            "occurred_at": "2026-07-07T00:00:00Z",
        },
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--context-bus",
            str(tmp_path / "context.bus.jsonl"),
            "--authorized",
            "--policy-decision-id",
            "policy:allow:github-artifact:tool0178",
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
    assert report[0]["authorized"] is True
    assert report[0]["scheduler_route_request"]["policy_decision_id"] == "policy:allow:github-artifact:tool0178"
