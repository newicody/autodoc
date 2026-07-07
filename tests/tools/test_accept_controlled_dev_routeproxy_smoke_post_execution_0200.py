from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "accept_controlled_dev_routeproxy_smoke_post_execution.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("accept_controlled_dev_routeproxy_smoke_post_execution_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _execution_fixture(tmp_path: Path) -> dict:
    runtime = tmp_path / "runtime" / "dev-controlled"
    isolated = runtime / "routeproxy-isolated"
    pipeline_output = runtime / "isolated_route_pipeline_smoke.json"
    return {
        "schema": "missipy.route_pipeline.controlled_dev_routeproxy_smoke_execution.v1",
        "bloc": "B",
        "bloc_name": "controlled-dev-smoke",
        "controlled_dev_plan_path": str(tmp_path / "controlled_dev_routeproxy_smoke_plan.json"),
        "context_bus_path": str(tmp_path / "context.bus.jsonl"),
        "policy_decision_id": "policy:allow:controlled-dev:manual0199",
        "target_runtime_root": str(runtime),
        "target_isolated_runtime_root": str(isolated),
        "execution_tool_reused": "tools/run_isolated_route_pipeline_smoke.py",
        "execution_unlocked_by_p0199": True,
        "execution_allowed_by_0199": True,
        "execution_scope": "controlled-dev-routeproxy-smoke",
        "pipeline_output": str(pipeline_output),
        "subprocess_returncode": 0,
        "pipeline_success": True,
        "queued_count": 1,
        "policy_scoped_queued_count": 1,
        "command_plan_ready_count": 1,
        "command_built_count": 1,
        "handler_executed_count": 1,
        "frames_written_count": 1,
        "readback_count": 1,
        "issues": [],
        "warnings": [],
        "execution_success": True,
        "existing_surfaces_reused": True,
        "existing_pipeline_tool_executed": True,
        "selected_baseline_ref": "baseline:isolated-route-pipeline-write-read-v1:0123456789abcdef",
        "selected_entry_digest": "0123456789abcdef" * 4,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "eventbus_instantiated": False,
        "network_used": False,
        "requires_p0200_post_execution_audit": True,
    }


def _pipeline_fixture(execution: dict) -> dict:
    return {
        "schema": "missipy.route_pipeline.isolated_smoke.v1",
        "pipeline_success": True,
        "queued_count": 1,
        "policy_scoped_queued_count": 1,
        "command_plan_ready_count": 1,
        "command_built_count": 1,
        "handler_executed_count": 1,
        "frames_written_count": 1,
        "readback_count": 1,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "eventbus_instantiated": False,
        "network_used": False,
        "artifacts": {
            "queue": str(Path(execution["target_runtime_root"]) / "scheduler.route_requests.jsonl"),
            "policy_scoped_queue": str(Path(execution["target_runtime_root"]) / "scheduler.route_requests.policy_scoped.jsonl"),
            "route_request_to_command_plan": str(Path(execution["target_runtime_root"]) / "route_request_to_command_dry_run_plan.jsonl"),
            "command_builder_smoke": str(Path(execution["target_runtime_root"]) / "scheduler_route_handler_command_smoke.jsonl"),
            "isolated_handler_execution_plan": str(Path(execution["target_runtime_root"]) / "isolated_handler_execution_plan.jsonl"),
            "isolated_handler_smoke": str(Path(execution["target_runtime_root"]) / "isolated_scheduler_route_handler_smoke.jsonl"),
            "isolated_handler_readback_smoke": str(Path(execution["target_runtime_root"]) / "isolated_scheduler_route_handler_readback_smoke.jsonl"),
        },
    }


def _write_fixture_files(tmp_path: Path) -> Path:
    execution = _execution_fixture(tmp_path)
    runtime = Path(execution["target_runtime_root"])
    runtime.mkdir(parents=True)
    pipeline = _pipeline_fixture(execution)
    for raw in pipeline["artifacts"].values():
        Path(raw).write_text("{}", encoding="utf-8")
    Path(execution["pipeline_output"]).write_text(json.dumps(pipeline, indent=2), encoding="utf-8")
    execution_path = runtime / "controlled_dev_routeproxy_smoke_execution.json"
    execution_path.write_text(json.dumps(execution, indent=2), encoding="utf-8")
    return execution_path


def test_0200_accepts_clean_controlled_dev_execution(tmp_path: Path) -> None:
    module = _load_tool_module()
    execution_path = _write_fixture_files(tmp_path)
    runtime = execution_path.parent
    output = runtime / "controlled_dev_routeproxy_smoke_post_execution_acceptance.json"
    registry = runtime / "controlled_dev_routeproxy_smoke_registry.jsonl"

    acceptance = module.accept_controlled_dev_routeproxy_smoke_post_execution(
        execution_report_path=execution_path,
        output_path=output,
        registry_path=registry,
    )

    assert acceptance["controlled_dev_smoke_accepted"] is True
    assert acceptance["bloc_b_complete"] is True
    assert acceptance["next_bloc"] == "C"
    assert acceptance["accepted_baseline"] == "controlled-dev-routeproxy-write-read-v1"
    assert acceptance["issues"] == []
    assert acceptance["existing_surfaces_reused"] is True
    assert acceptance["frames_written_count"] == 1
    assert acceptance["readback_count"] == 1
    assert acceptance["controlproxy_frames_written"] is False
    assert acceptance["scheduler_modified"] is False
    assert acceptance["network_used"] is False
    assert output.exists()
    assert registry.exists()


def test_0200_rejects_scheduler_modification(tmp_path: Path) -> None:
    module = _load_tool_module()
    execution_path = _write_fixture_files(tmp_path)
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    execution["scheduler_modified"] = True
    execution_path.write_text(json.dumps(execution, indent=2), encoding="utf-8")

    acceptance = module.accept_controlled_dev_routeproxy_smoke_post_execution(
        execution_report_path=execution_path,
    )

    assert acceptance["controlled_dev_smoke_accepted"] is False
    assert "Scheduler must not be modified" in acceptance["issues"]
