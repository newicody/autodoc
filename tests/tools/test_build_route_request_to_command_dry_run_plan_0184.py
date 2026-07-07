from pathlib import Path
import importlib.util
import json
import subprocess
import sys

from context.authorized_route_request_queue import append_authorized_route_requests_from_context_bus
from context.github_artifact_dataset_bus_observation import append_github_artifact_dataset_bus_observation


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_route_request_to_command_dry_run_plan.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("build_route_request_to_command_dry_run_plan_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_queue(root: Path) -> str:
    append_github_artifact_dataset_bus_observation(
        runtime_root=root,
        raw={
            "report_ref": "report:github-artifact:0184",
            "repository": "newicody/autodoc-ideas",
            "run_id": "run0184",
            "artifact_id": "artifact0184",
            "status": "queued",
            "dataset_root_ref": "server-dataset:github-artifacts",
            "raw_count": 1,
            "queued_count": 1,
            "failed_count": 0,
            "occurred_at": "2026-07-07T00:00:00Z",
        },
    )
    handoff = append_authorized_route_requests_from_context_bus(
        context_bus_path=root / "context.bus.jsonl",
        runtime_root=root,
        policy_decision_id="policy:allow:github-artifact:0184",
    )
    return handoff.queue_path


def test_0184_builds_route_request_to_command_dry_run_plan(tmp_path: Path) -> None:
    module = _load_tool_module()
    queue_path = _write_queue(tmp_path)

    report = module.build_route_request_to_command_dry_run_plan(
        queue_path=queue_path,
        output_path=tmp_path / "route_request_to_command_dry_run_plan.jsonl",
    )

    assert report["item_count"] == 1
    assert report["ready_count"] == 1
    assert report["dry_run_only"] is True
    assert report["builder_called"] is False
    assert report["handler_called"] is False
    assert report["frames_written"] is False
    item = report["items"][0]
    assert item["builder_surface"] == "build_single_frame_route_command"
    assert item["handler_surface"] == "handle_scheduler_route_command"
    kwargs = item["builder_kwargs"]
    assert kwargs["command_ref"].startswith("scheduler-command:")
    assert kwargs["route_ref"].startswith("route:")
    assert kwargs["owner_ref"].startswith("scheduler-command:")
    assert kwargs["context_ref"].startswith("ctx:")
    assert kwargs["frame_kind"] == "runtime_probe"
    assert kwargs["runtime_policy"] is None
    assert (tmp_path / "route_request_to_command_dry_run_plan.jsonl").exists()


def test_0184_output_filename_is_locked(tmp_path: Path) -> None:
    module = _load_tool_module()
    queue_path = _write_queue(tmp_path)

    try:
        module.build_route_request_to_command_dry_run_plan(
            queue_path=queue_path,
            output_path=tmp_path / "wrong.jsonl",
        )
    except module.RouteRequestToCommandDryRunPlanError as exc:
        assert "route_request_to_command_dry_run_plan.jsonl" in str(exc)
    else:
        raise AssertionError("expected locked output filename error")


def test_0184_cli_outputs_json(tmp_path: Path) -> None:
    queue_path = _write_queue(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--queue",
            queue_path,
            "--output",
            str(tmp_path / "route_request_to_command_dry_run_plan.jsonl"),
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
    assert report["schema"] == "missipy.route_request.to_command_dry_run_plan.v1"
    assert report["ready_count"] == 1
    assert report["dry_run_only"] is True
    assert report["builder_called"] is False
    assert report["handler_called"] is False
