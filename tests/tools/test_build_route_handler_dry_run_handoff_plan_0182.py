from pathlib import Path
import importlib.util
import json
import subprocess
import sys

from context.authorized_route_request_queue import append_authorized_route_requests_from_context_bus
from context.github_artifact_dataset_bus_observation import append_github_artifact_dataset_bus_observation


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_route_handler_dry_run_handoff_plan.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("build_route_handler_dry_run_handoff_plan_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _observation() -> dict[str, object]:
    return {
        "report_ref": "report:github-artifact:0182",
        "repository": "newicody/autodoc-ideas",
        "run_id": "run0182",
        "artifact_id": "artifact0182",
        "status": "queued",
        "dataset_root_ref": "server-dataset:github-artifacts",
        "raw_count": 1,
        "queued_count": 1,
        "failed_count": 0,
        "occurred_at": "2026-07-07T00:00:00Z",
    }


def _write_fake_handler(root: Path) -> None:
    path = root / "src/runtime/scheduler_route_handler_minimal.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "def handle_scheduler_route_request(request, *, runtime_root=None):\n"
            "    raise AssertionError('must not execute in dry-run test')\n"
        ),
        encoding="utf-8",
    )


def _write_queue(root: Path) -> str:
    append_github_artifact_dataset_bus_observation(runtime_root=root, raw=_observation())
    handoff = append_authorized_route_requests_from_context_bus(
        context_bus_path=root / "context.bus.jsonl",
        runtime_root=root,
        policy_decision_id="policy:allow:github-artifact:0182",
    )
    return handoff.queue_path


def test_0182_builds_dry_run_handoff_plan_without_handler_call(tmp_path: Path) -> None:
    module = _load_tool_module()
    _write_fake_handler(tmp_path)
    queue_path = _write_queue(tmp_path)

    report = module.build_route_handler_dry_run_handoff_plan(
        queue_path=queue_path,
        repo_root=tmp_path,
        output_path=tmp_path / "route_handler_dry_run_plan.jsonl",
    )

    assert report["item_count"] == 1
    assert report["ready_count"] == 1
    assert report["dry_run_only"] is True
    assert report["handler_called"] is False
    assert report["runtime_imports_executed"] is False
    assert report["handler"]["function_found"] is True
    assert report["items"][0]["ready_for_later_handler_call"] is True
    assert (tmp_path / "route_handler_dry_run_plan.jsonl").exists()


def test_0182_blocks_when_handler_function_missing(tmp_path: Path) -> None:
    module = _load_tool_module()
    path = tmp_path / "src/runtime/scheduler_route_handler_minimal.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("def other_function(): pass\n", encoding="utf-8")
    queue_path = _write_queue(tmp_path)

    report = module.build_route_handler_dry_run_handoff_plan(queue_path=queue_path, repo_root=tmp_path)

    assert report["item_count"] == 1
    assert report["ready_count"] == 0
    assert report["blocked_count"] == 1
    assert "handler function not found" in report["items"][0]["issues"]


def test_0182_cli_outputs_json(tmp_path: Path) -> None:
    _write_fake_handler(tmp_path)
    queue_path = _write_queue(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--queue",
            queue_path,
            "--repo-root",
            str(tmp_path),
            "--output",
            str(tmp_path / "route_handler_dry_run_plan.jsonl"),
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
    assert report["schema"] == "missipy.route_handler.dry_run_handoff_plan.v1"
    assert report["dry_run_only"] is True
    assert report["handler_called"] is False
    assert report["frames_written"] is False
