from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
HANDLER_TOOL = ROOT / "tools" / "run_isolated_scheduler_route_handler_smoke.py"
TOOL = ROOT / "tools" / "readback_isolated_scheduler_route_handler_smoke.py"


def _load_tool_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_plan(root: Path) -> Path:
    plan = root / "isolated_handler_execution_plan.jsonl"
    isolated = root / "routeproxy-isolated"
    plan.write_text(
        json.dumps(
            {
                "source_request_id": "request-0188",
                "source_route_id": "route-0188",
                "source_task_id": "task-0188",
                "policy_decision_id": "policy:allow:0188",
                "command_ref": "scheduler-command:task-0188",
                "handler_call_allowed_by_0186": False,
                "handler_surface": "handle_scheduler_route_command",
                "isolated_runtime_root": str(isolated),
                "runtime_policy_kwargs": {"route_root": str(isolated)},
                "ready_for_later_isolated_handler_call": True,
                "command_mapping": {
                    "schema": "missipy.scheduler.route_handler_command.v1",
                    "command_ref": "scheduler-command:task-0188",
                    "handler_ref": "handler:scheduler-route-minimal",
                    "route_root_ref": "route:runtime/root",
                    "frame_requests": [
                        {
                            "schema": "missipy.scheduler.route_frame_request.v1",
                            "route_ref": "route:0188-test",
                            "owner_ref": "scheduler-command:task-0188",
                            "context_ref": "ctx:request-0188",
                            "context_generation": 1,
                            "priority": 50,
                            "frame_kind": "runtime_probe",
                            "payload": {"policy_decision_id": "policy:allow:0188"},
                            "write_allowed": True,
                            "denial_reason": None,
                        }
                    ],
                    "runtime_policy": None,
                    "scheduler_run_modified": False,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return plan


def _write_0187_smoke(root: Path) -> Path:
    handler_module = _load_tool_module(HANDLER_TOOL, "run_isolated_scheduler_route_handler_smoke_tool_0188")
    plan = _write_plan(root)
    smoke = root / "isolated_scheduler_route_handler_smoke.jsonl"
    handler_module.run_isolated_scheduler_route_handler_smoke(plan_path=plan, output_path=smoke)
    return smoke


def test_0188_reads_back_frame_without_new_frame_write_or_handler_call(tmp_path: Path) -> None:
    module = _load_tool_module(TOOL, "readback_isolated_scheduler_route_handler_smoke_tool")
    smoke = _write_0187_smoke(tmp_path)

    before = set((tmp_path / "routeproxy-isolated" / "frames").glob("*.json"))
    report = module.run_isolated_scheduler_route_handler_readback_smoke(
        smoke_path=smoke,
        output_path=tmp_path / "isolated_scheduler_route_handler_readback_smoke.jsonl",
    )
    after = set((tmp_path / "routeproxy-isolated" / "frames").glob("*.json"))

    assert report["item_count"] == 1
    assert report["readback_count"] == 1
    assert report["blocked_count"] == 0
    assert report["routeproxy_prepared"] is True
    assert report["read_route_frame_called"] is True
    assert report["handler_called"] is False
    assert report["writer_permits_requested"] is False
    assert report["frames_written"] is False
    assert report["controlproxy_frames_written"] is False
    assert before == after
    item = report["items"][0]
    assert item["issues"] == []
    assert item["readback_frames"][0]["route_ref"] == "route:0188-test"
    assert (tmp_path / "isolated_scheduler_route_handler_readback_smoke.jsonl").exists()


def test_0188_blocks_unsafe_smoke_item(tmp_path: Path) -> None:
    module = _load_tool_module(TOOL, "readback_isolated_scheduler_route_handler_smoke_tool_block")
    smoke = tmp_path / "isolated_scheduler_route_handler_smoke.jsonl"
    smoke.write_text(
        json.dumps(
            {
                "handler_called": False,
                "isolated_runtime_root": "relative-root",
                "written_route_refs": [],
                "frame_paths": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = module.run_isolated_scheduler_route_handler_readback_smoke(smoke_path=smoke)

    assert report["readback_count"] == 0
    assert report["blocked_count"] == 1
    assert report["handler_called"] is False
    assert "0187 smoke item did not call handler" in report["items"][0]["issues"]


def test_0188_cli_outputs_json(tmp_path: Path) -> None:
    smoke = _write_0187_smoke(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--smoke",
            str(smoke),
            "--output",
            str(tmp_path / "isolated_scheduler_route_handler_readback_smoke.jsonl"),
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
    assert report["schema"] == "missipy.scheduler.route_handler.isolated_readback_smoke.v1"
    assert report["readback_count"] == 1
    assert report["handler_called"] is False
    assert report["frames_written"] is False
    assert report["network_used"] is False
