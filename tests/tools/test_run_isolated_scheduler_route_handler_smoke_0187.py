from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_isolated_scheduler_route_handler_smoke.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("run_isolated_scheduler_route_handler_smoke_tool", TOOL)
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
                "source_request_id": "request-0187",
                "source_route_id": "route-0187",
                "source_task_id": "task-0187",
                "policy_decision_id": "policy:allow:0187",
                "command_ref": "scheduler-command:task-0187",
                "handler_call_allowed_by_0186": False,
                "handler_surface": "handle_scheduler_route_command",
                "isolated_runtime_root": str(isolated),
                "runtime_policy_kwargs": {"route_root": str(isolated)},
                "ready_for_later_isolated_handler_call": True,
                "command_mapping": {
                    "schema": "missipy.scheduler.route_handler_command.v1",
                    "command_ref": "scheduler-command:task-0187",
                    "handler_ref": "handler:scheduler-route-minimal",
                    "route_root_ref": "route:runtime/root",
                    "frame_requests": [
                        {
                            "schema": "missipy.scheduler.route_frame_request.v1",
                            "route_ref": "route:0187-test",
                            "owner_ref": "scheduler-command:task-0187",
                            "context_ref": "ctx:request-0187",
                            "context_generation": 1,
                            "priority": 50,
                            "frame_kind": "runtime_probe",
                            "payload": {"policy_decision_id": "policy:allow:0187"},
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


def test_0187_runs_handler_only_inside_isolated_runtime_root(tmp_path: Path) -> None:
    module = _load_tool_module()
    plan = _write_plan(tmp_path)

    report = module.run_isolated_scheduler_route_handler_smoke(
        plan_path=plan,
        output_path=tmp_path / "isolated_scheduler_route_handler_smoke.jsonl",
    )

    assert report["item_count"] == 1
    assert report["executed_count"] == 1
    assert report["blocked_count"] == 0
    assert report["handler_called"] is True
    assert report["routeproxy_prepared"] is True
    assert report["frames_written"] is True
    assert report["controlproxy_frames_written"] is False
    assert report["scheduler_modified"] is False
    item = report["items"][0]
    assert item["issues"] == []
    assert item["written_route_refs"] == ["route:0187-test"]
    assert item["denied_route_refs"] == []
    for path in item["frame_paths"]:
        assert Path(path).resolve().is_relative_to((tmp_path / "routeproxy-isolated").resolve())
        assert Path(path).exists()
    assert (tmp_path / "isolated_scheduler_route_handler_smoke.jsonl").exists()


def test_0187_blocks_unsafe_relative_isolated_root(tmp_path: Path) -> None:
    module = _load_tool_module()
    plan = _write_plan(tmp_path)
    item = json.loads(plan.read_text(encoding="utf-8"))
    item["isolated_runtime_root"] = "relative-root"
    item["runtime_policy_kwargs"] = {"route_root": "relative-root"}
    plan.write_text(json.dumps(item) + "\n", encoding="utf-8")

    report = module.run_isolated_scheduler_route_handler_smoke(plan_path=plan)

    assert report["executed_count"] == 0
    assert report["blocked_count"] == 1
    assert report["handler_called"] is False
    assert "isolated_runtime_root is unsafe" in report["items"][0]["issues"]


def test_0187_cli_outputs_json(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--plan",
            str(plan),
            "--output",
            str(tmp_path / "isolated_scheduler_route_handler_smoke.jsonl"),
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
    assert report["schema"] == "missipy.scheduler.route_handler.isolated_smoke.v1"
    assert report["executed_count"] == 1
    assert report["handler_called"] is True
    assert report["frames_written"] is True
    assert report["network_used"] is False
