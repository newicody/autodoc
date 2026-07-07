from pathlib import Path
import json
import subprocess
import sys

from runtime.shm_runtime_schema import ContextBusMessage, EventBusMessage


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "project_github_artifact_dataset_bus_observation.py"


def test_0176_tool_projects_input_to_existing_bus_jsonl(tmp_path: Path) -> None:
    payload = {
        "report_ref": "report:github-artifact:tool",
        "repository": "newicody/autodoc-ideas",
        "run_id": "run0176tool",
        "artifact_id": "artifact0176tool",
        "status": "queued",
        "dataset_root_ref": "server-dataset:github-artifacts",
        "raw_count": 1,
        "queued_count": 1,
        "failed_count": 0,
        "occurred_at": "2026-07-07T00:00:00Z",
    }
    input_path = tmp_path / "observation.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    runtime_root = tmp_path / "runtime"

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--input",
            str(input_path),
            "--runtime-root",
            str(runtime_root),
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
    assert report["uses_existing_runtime_shm_schema"] is True
    assert report["creates_parallel_bus"] is False
    assert report["writes_vispy_directly"] is False

    event = EventBusMessage.from_mapping(json.loads((runtime_root / "event.bus.jsonl").read_text(encoding="utf-8")))
    context = ContextBusMessage.from_mapping(json.loads((runtime_root / "context.bus.jsonl").read_text(encoding="utf-8")))
    assert event.payload["repository"] == "newicody/autodoc-ideas"
    assert context.payload["queued_count"] == 1
