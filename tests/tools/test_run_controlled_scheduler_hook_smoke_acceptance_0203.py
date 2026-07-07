from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_controlled_scheduler_hook_smoke_acceptance.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("run_controlled_scheduler_hook_smoke_acceptance_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _plan_fixture(tmp_path: Path, *, ready: bool = True) -> dict:
    runtime = tmp_path / "runtime" / "dev-controlled"
    return {
        "schema": "missipy.scheduler.hook_dry_run_plan.v1",
        "scheduler_hook_dry_run_plan_ready": ready,
        "execution_allowed_by_0202": False,
        "scheduler_run_execution_allowed": False,
        "p0203_may_execute_controlled_scheduler_hook": ready,
        "planned_next_patch": "0203-controlled_scheduler_hook_smoke_acceptance",
        "issues": [] if ready else ["scheduler_hook_dry_run_plan_ready must be true"],
        "warnings": [],
        "existing_surfaces_reused": True,
        "target_runtime_root": str(runtime),
        "target_isolated_runtime_root": str(runtime / "routeproxy-isolated"),
        "controlled_dev_baseline_ref": "baseline:controlled-dev-routeproxy-write-read-v1:0123456789abcdef",
        "provenance_repair_items": [
            "source_baseline_ref or source_entry_digest missing from P0200 acceptance; preserve this as a provenance repair item"
        ],
        "reuse_sequence": [
            {"step": "map_authorized_request"},
            {"step": "prepare_route"},
            {"step": "build_command"},
            {"step": "execute_minimal_handler"},
            {"step": "readback"},
        ],
        "runtime_imports_executed_by_0202": False,
        "scheduler_run_executed": False,
        "handler_called_by_0202": False,
        "routeproxy_prepared_by_0202": False,
        "read_route_frame_called_by_0202": False,
        "writer_permits_requested_by_0202": False,
        "frames_written_by_0202": False,
        "controlproxy_frames_written_by_0202": False,
        "eventbus_instantiated_by_0202": False,
        "network_used_by_0202": False,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_scheduler_added": False,
        "new_routeproxy_runtime_added": False,
        "new_controlproxy_runtime_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
        "new_graph_renderer_added": False,
        "new_inference_path_added": False,
    }


class _Completed:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.stdout = '{"pipeline_success": true}'
        self.stderr = ""


def test_0203_runs_controlled_scheduler_hook_smoke_from_clean_plan(tmp_path: Path, monkeypatch) -> None:
    module = _load_tool_module()
    runtime = tmp_path / "runtime" / "dev-controlled"
    runtime.mkdir(parents=True)
    plan_path = tmp_path / "scheduler_hook_dry_run_plan.json"
    context_bus = tmp_path / "context.bus.jsonl"
    output = runtime / "controlled_scheduler_hook_smoke_acceptance.json"
    plan_path.write_text(json.dumps(_plan_fixture(tmp_path), indent=2), encoding="utf-8")
    context_bus.write_text("{}", encoding="utf-8")

    captured = {}

    def fake_run(command, cwd, text, stdout, stderr, check):
        captured["command"] = command
        pipeline_output = Path(command[command.index("--output") + 1])
        pipeline_output.parent.mkdir(parents=True, exist_ok=True)
        pipeline_output.write_text(
            json.dumps(
                {
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
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return _Completed()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    acceptance = module.run_controlled_scheduler_hook_smoke_acceptance(
        scheduler_hook_plan_path=plan_path,
        context_bus_path=context_bus,
        policy_decision_id="policy:allow:scheduler-hook:manual0203",
        output_path=output,
        repo_root=ROOT,
    )

    assert acceptance["controlled_scheduler_hook_smoke_accepted"] is True
    assert acceptance["bloc_c_complete"] is True
    assert acceptance["execution_allowed_by_0203"] is True
    assert acceptance["scheduler_run_executed"] is False
    assert acceptance["scheduler_run_modified"] is False
    assert acceptance["new_scheduler_hook_implementation_added"] is False
    assert acceptance["execution_tool_reused"] == "tools/run_isolated_route_pipeline_smoke.py"
    assert "tools/run_isolated_route_pipeline_smoke.py" in captured["command"][1]
    assert acceptance["frames_written_count"] == 1
    assert acceptance["readback_count"] == 1
    assert acceptance["controlproxy_frames_written"] is False
    assert acceptance["scheduler_modified"] is False
    assert acceptance["network_used"] is False
    assert acceptance["next_recommended_patch"] == "0204-controlproxy_contract_audit"
    assert output.exists()


def test_0203_rejects_unready_plan_without_subprocess(tmp_path: Path, monkeypatch) -> None:
    module = _load_tool_module()
    runtime = tmp_path / "runtime" / "dev-controlled"
    runtime.mkdir(parents=True)
    plan_path = tmp_path / "scheduler_hook_dry_run_plan.json"
    context_bus = tmp_path / "context.bus.jsonl"
    plan_path.write_text(json.dumps(_plan_fixture(tmp_path, ready=False), indent=2), encoding="utf-8")
    context_bus.write_text("{}", encoding="utf-8")

    called = {"value": False}

    def fake_run(*args, **kwargs):
        called["value"] = True
        return _Completed()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    acceptance = module.run_controlled_scheduler_hook_smoke_acceptance(
        scheduler_hook_plan_path=plan_path,
        context_bus_path=context_bus,
        policy_decision_id="policy:allow:scheduler-hook:manual0203",
        repo_root=ROOT,
    )

    assert acceptance["controlled_scheduler_hook_smoke_accepted"] is False
    assert called["value"] is False
    assert "scheduler_hook_dry_run_plan_ready must be true" in acceptance["issues"]
    assert "p0203_may_execute_controlled_scheduler_hook must be true" in acceptance["issues"]
