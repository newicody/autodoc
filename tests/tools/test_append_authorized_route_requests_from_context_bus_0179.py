from pathlib import Path
import json
import subprocess
import sys

from context.github_artifact_dataset_bus_observation import append_github_artifact_dataset_bus_observation


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "append_authorized_route_requests_from_context_bus.py"


def test_0179_tool_writes_authorized_handoff_queue(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(
        runtime_root=tmp_path,
        raw={
            "report_ref": "report:github-artifact:tool0179",
            "repository": "newicody/autodoc-ideas",
            "run_id": "run0179tool",
            "artifact_id": "artifact0179tool",
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
            "--runtime-root",
            str(tmp_path),
            "--policy-decision-id",
            "policy:allow:github-artifact:tool0179",
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
    assert report["queued_count"] == 1
    assert report["authorized_only"] is True
    assert report["handler_called"] is False
    assert Path(report["queue_path"]).exists()
