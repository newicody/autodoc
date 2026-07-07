from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_controlproxy_routeproxy_coherence_acceptance.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("run_controlproxy_routeproxy_coherence_acceptance_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _plan_fixture(tmp_path: Path, *, ready: bool = True) -> dict:
    runtime = tmp_path / "runtime" / "dev-controlled"
    return {
        "schema": "missipy.controlproxy.stale_priority_zone_smoke_plan.v1",
        "controlproxy_stale_priority_zone_smoke_plan_ready": ready,
        "execution_allowed_by_0205": False,
        "controlproxy_frame_write_allowed_by_0205": False,
        "routeproxy_frame_write_allowed_by_0205": False,
        "p0206_may_execute_controlled_stale_priority_zone_smoke": ready,
        "planned_next_patch": "0206-controlproxy_routeproxy_coherence_acceptance",
        "issues": [] if ready else ["controlproxy_stale_priority_zone_smoke_plan_ready must be true"],
        "warnings": [],
        "existing_surfaces_reused": True,
        "target_runtime_root": str(runtime),
        "target_isolated_runtime_root": str(runtime / "routeproxy-isolated"),
        "provenance_repair_items": ["source_baseline_ref or source_entry_digest missing"],
        "contract_decisions": ["ControlProxy remains coordination, not business authority."],
        "runtime_imports_executed_by_0205": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0205": False,
        "routeproxy_prepared_by_0205": False,
        "mark_route_frame_stale_called_by_0205": False,
        "read_route_frame_called_by_0205": False,
        "writer_permits_requested_by_0205": False,
        "frames_written_by_0205": False,
        "controlproxy_frames_written_by_0205": False,
        "eventbus_instantiated_by_0205": False,
        "network_used_by_0205": False,
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


def test_0206_runs_coherence_acceptance_from_clean_plan(tmp_path: Path, monkeypatch) -> None:
    module = _load_tool_module()
    runtime = tmp_path / "runtime" / "dev-controlled"
    runtime.mkdir(parents=True)
    plan_path = tmp_path / "controlproxy_stale_priority_zone_smoke_plan.json"
    context_bus = tmp_path / "context.bus.jsonl"
    output = runtime / "controlproxy_routeproxy_coherence_acceptance.json"
    plan_path.write_text(json.dumps(_plan_fixture(tmp_path), indent=2), encoding="utf-8")
    context_bus.write_text("{}", encoding="utf-8")

    captured = {}

    def fake_run(command, cwd, text, stdout, stderr, check):
        captured["command"] = command
        pipeline_output = Path(command[command.index("--output") + 1])
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
                    "isolated_runtime_root": str(runtime / "routeproxy-isolated"),
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

    acceptance = module.run_controlproxy_routeproxy_coherence_acceptance(
        stale_priority_zone_plan_path=plan_path,
        context_bus_path=context_bus,
        policy_decision_id="policy:allow:stale-priority-zone:manual0206",
        output_path=output,
        repo_root=ROOT,
    )

    assert acceptance["controlproxy_routeproxy_coherence_accepted"] is True
    assert acceptance["stale_priority_zone_contract_accepted"] is True
    assert acceptance["bloc_d_complete"] is True
    assert acceptance["execution_allowed_by_0206"] is True
    assert acceptance["controlproxy_frame_write_allowed_by_0206"] is False
    assert acceptance["routeproxy_frame_write_allowed_by_0206"] is True
    assert acceptance["scheduler_run_executed"] is False
    assert acceptance["scheduler_run_modified"] is False
    assert acceptance["new_controlproxy_runtime_added"] is False
    assert acceptance["new_routeproxy_runtime_added"] is False
    assert acceptance["mark_route_frame_stale_called_by_0206"] is False
    assert acceptance["frames_written_count"] == 1
    assert acceptance["readback_count"] == 1
    assert acceptance["controlproxy_frames_written"] is False
    assert acceptance["next_recommended_patch"] == "0207-provenance_repair_audit"
    assert "tools/run_isolated_route_pipeline_smoke.py" in captured["command"][1]
    assert output.exists()


def test_0206_rejects_unready_plan_without_subprocess(tmp_path: Path, monkeypatch) -> None:
    module = _load_tool_module()
    runtime = tmp_path / "runtime" / "dev-controlled"
    runtime.mkdir(parents=True)
    plan_path = tmp_path / "controlproxy_stale_priority_zone_smoke_plan.json"
    context_bus = tmp_path / "context.bus.jsonl"
    plan_path.write_text(json.dumps(_plan_fixture(tmp_path, ready=False), indent=2), encoding="utf-8")
    context_bus.write_text("{}", encoding="utf-8")

    called = {"value": False}

    def fake_run(*args, **kwargs):
        called["value"] = True
        return _Completed()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    acceptance = module.run_controlproxy_routeproxy_coherence_acceptance(
        stale_priority_zone_plan_path=plan_path,
        context_bus_path=context_bus,
        policy_decision_id="policy:allow:stale-priority-zone:manual0206",
        repo_root=ROOT,
    )

    assert acceptance["controlproxy_routeproxy_coherence_accepted"] is False
    assert called["value"] is False
    assert "controlproxy_stale_priority_zone_smoke_plan_ready must be true" in acceptance["issues"]
    assert "p0206_may_execute_controlled_stale_priority_zone_smoke must be true" in acceptance["issues"]
