from pathlib import Path
import json
import subprocess
import sys

from context.authorized_route_request_queue import append_authorized_route_requests_from_context_bus
from context.github_artifact_dataset_bus_observation import append_github_artifact_dataset_bus_observation


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_authorized_route_request_queue_dry_run.py"


def test_0180_tool_dry_run_audits_queue(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(
        runtime_root=tmp_path,
        raw={
            "report_ref": "report:github-artifact:tool0180",
            "repository": "newicody/autodoc-ideas",
            "run_id": "run0180tool",
            "artifact_id": "artifact0180tool",
            "status": "queued",
            "dataset_root_ref": "server-dataset:github-artifacts",
            "raw_count": 1,
            "queued_count": 1,
            "failed_count": 0,
            "occurred_at": "2026-07-07T00:00:00Z",
        },
    )
    handoff = append_authorized_route_requests_from_context_bus(
        context_bus_path=tmp_path / "context.bus.jsonl",
        runtime_root=tmp_path,
        policy_decision_id="policy:allow:github-artifact:tool0180",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--queue",
            handoff.queue_path,
            "--repo-root",
            str(ROOT),
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
    assert report["item_count"] == 1
    assert report["ready_count"] == 1
    assert report["dry_run_only"] is True
    assert report["handler_called"] is False
