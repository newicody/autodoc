from pathlib import Path
import importlib.util
import json
import subprocess
import sys

from context.authorized_route_request_queue import append_authorized_route_requests_from_context_bus
from context.github_artifact_dataset_bus_observation import append_github_artifact_dataset_bus_observation


ROOT = Path(__file__).resolve().parents[2]
PLAN_TOOL = ROOT / "tools" / "build_route_request_to_command_dry_run_plan.py"
TOOL = ROOT / "tools" / "build_scheduler_route_handler_command_smoke.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("build_scheduler_route_handler_command_smoke_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_plan_tool_module():
    spec = importlib.util.spec_from_file_location("build_route_request_to_command_dry_run_plan_tool", PLAN_TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_plan(root: Path) -> Path:
    append_github_artifact_dataset_bus_observation(
        runtime_root=root,
        raw={
            "report_ref": "report:github-artifact:0185",
            "repository": "newicody/autodoc-ideas",
            "run_id": "run0185",
            "artifact_id": "artifact0185",
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
        policy_decision_id="policy:allow:github-artifact:0185",
    )
    plan_tool = _load_plan_tool_module()
    plan_path = root / "route_request_to_command_dry_run_plan.jsonl"
    plan_tool.build_route_request_to_command_dry_run_plan(
        queue_path=handoff.queue_path,
        output_path=plan_path,
    )
    return plan_path


def test_0185_smoke_builds_scheduler_route_handler_command_without_handler_call(tmp_path: Path) -> None:
    module = _load_tool_module()
    plan_path = _write_plan(tmp_path)

    report = module.build_scheduler_route_handler_command_smoke(
        plan_path=plan_path,
        output_path=tmp_path / "scheduler_route_handler_command_smoke.jsonl",
    )

    assert report["item_count"] == 1
    assert report["built_count"] == 1
    assert report["blocked_count"] == 0
    assert report["builder_imported"] is True
    assert report["builder_called"] is True
    assert report["handler_called"] is False
    assert report["routeproxy_prepared"] is False
    assert report["frames_written"] is False
    item = report["items"][0]
    assert item["command_built"] is True
    assert item["command_type"] == "SchedulerRouteHandlerCommand"
    command_mapping = item["command_mapping"]
    assert command_mapping["schema"] == "missipy.scheduler.route_handler_command.v1"
    assert command_mapping["scheduler_run_modified"] is False
    assert command_mapping["handler_is_executor"] is True
    assert command_mapping["frame_requests"][0]["frame_kind"] == "runtime_probe"
    assert (tmp_path / "scheduler_route_handler_command_smoke.jsonl").exists()


def test_0185_blocks_non_ready_plan_item(tmp_path: Path) -> None:
    module = _load_tool_module()
    plan_path = tmp_path / "route_request_to_command_dry_run_plan.jsonl"
    plan_path.write_text(
        json.dumps(
            {
                "ready_for_later_command_builder_call": False,
                "builder_surface": "build_single_frame_route_command",
                "handler_surface": "handle_scheduler_route_command",
                "builder_kwargs": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = module.build_scheduler_route_handler_command_smoke(plan_path=plan_path)

    assert report["built_count"] == 0
    assert report["blocked_count"] == 1
    assert "plan item is not ready for command builder call" in report["items"][0]["issues"]


def test_0185_cli_outputs_json(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--plan",
            str(plan_path),
            "--output",
            str(tmp_path / "scheduler_route_handler_command_smoke.jsonl"),
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
    assert report["schema"] == "missipy.scheduler.route_handler.command_builder_smoke.v1"
    assert report["built_count"] == 1
    assert report["builder_called"] is True
    assert report["handler_called"] is False
    assert report["frames_written"] is False
