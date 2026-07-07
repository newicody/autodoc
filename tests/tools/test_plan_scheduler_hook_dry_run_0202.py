from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_scheduler_hook_dry_run.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("plan_scheduler_hook_dry_run_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _surface_report(path: str, symbols: list[str]) -> dict:
    return {
        "path": path,
        "role": "role",
        "exists": True,
        "parse_error": "",
        "function_count": len(symbols),
        "class_count": 0,
        "functions": symbols,
        "classes": [],
        "required_symbols": symbols,
        "matched_required_symbols": symbols,
        "missing_required_symbols": [],
        "use_before_new_code": True,
    }


def _audit_fixture(tmp_path: Path, *, success: bool = True) -> dict:
    return {
        "schema": "missipy.scheduler.integration_surface_audit.v1",
        "bloc": "C",
        "bloc_name": "scheduler-hook-controlled",
        "accepted_baseline": "controlled-dev-routeproxy-write-read-v1",
        "controlled_dev_baseline_ref": "baseline:controlled-dev-routeproxy-write-read-v1:0123456789abcdef",
        "policy_decision_id": "policy:allow:controlled-dev:manual0199",
        "target_runtime_root": str(tmp_path / "runtime" / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "runtime" / "dev-controlled" / "routeproxy-isolated"),
        "surface_count": 6,
        "existing_surface_count": 6,
        "integration_surface_audit_success": success,
        "scheduler_hook_plan_allowed_next": success,
        "next_recommended_patch": "0202-scheduler_hook_dry_run_plan",
        "recommended_integration_path": {
            "path": "adapter -> command builder -> minimal handler -> readback",
            "reuse_first": [
                "src/runtime/scheduler_route_adapter.py",
                "src/runtime/scheduler_route_handler_minimal.py",
                "src/runtime/scheduler_route_handshake.py",
            ],
        },
        "provenance_warning": "source_baseline_ref or source_entry_digest missing from P0200 acceptance; preserve this as a provenance repair item",
        "issues": [] if success else ["integration_surface_audit_success must be true"],
        "warnings": [],
        "existing_surfaces_reused": True,
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
        "runtime_imports_executed_by_0201": False,
        "scheduler_run_executed": False,
        "handler_called_by_0201": False,
        "routeproxy_prepared_by_0201": False,
        "read_route_frame_called_by_0201": False,
        "writer_permits_requested_by_0201": False,
        "frames_written_by_0201": False,
        "controlproxy_frames_written_by_0201": False,
        "eventbus_instantiated_by_0201": False,
        "network_used_by_0201": False,
        "surface_reports": [
            _surface_report("src/runtime/scheduler_route_adapter.py", ["scheduler_route_request_mapping"]),
            _surface_report("src/runtime/scheduler_route_handler_minimal.py", ["build_single_frame_route_command", "handle_scheduler_route_command", "read_scheduler_route_handler_result_frames"]),
            _surface_report("src/runtime/scheduler_route_handshake.py", ["prepare_route_for_scheduler"]),
            _surface_report("src/runtime/controlproxy_scheduler_handler.py", ["handle_scheduler_route_request"]),
            _surface_report("src/runtime/route_proxy_runtime_minimal.py", ["RouteProxyRuntimePolicy", "prepare_route_proxy_runtime"]),
            _surface_report("src/runtime/shm_runtime_schema.py", ["EventBusMessage", "ContextBusMessage"]),
        ],
    }


def test_0202_plans_scheduler_hook_dry_run_from_clean_audit(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "scheduler_integration_surface_audit.json"
    output = tmp_path / "scheduler_hook_dry_run_plan.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path), indent=2), encoding="utf-8")

    plan = module.plan_scheduler_hook_dry_run(
        surface_audit_path=audit_path,
        output_path=output,
    )

    assert plan["scheduler_hook_dry_run_plan_ready"] is True
    assert plan["execution_allowed_by_0202"] is False
    assert plan["scheduler_run_execution_allowed"] is False
    assert plan["p0203_may_execute_controlled_scheduler_hook"] is True
    assert plan["planned_next_patch"] == "0203-controlled_scheduler_hook_smoke_acceptance"
    assert plan["existing_surfaces_reused"] is True
    assert plan["new_runtime_handler_added"] is False
    assert plan["new_adapter_added"] is False
    assert plan["scheduler_run_executed"] is False
    assert plan["frames_written_by_0202"] is False
    assert plan["provenance_repair_items"]
    assert output.exists()


def test_0202_rejects_failed_surface_audit(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "scheduler_integration_surface_audit.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path, success=False), indent=2), encoding="utf-8")

    plan = module.plan_scheduler_hook_dry_run(surface_audit_path=audit_path)

    assert plan["scheduler_hook_dry_run_plan_ready"] is False
    assert plan["p0203_may_execute_controlled_scheduler_hook"] is False
    assert "integration_surface_audit_success must be true" in plan["issues"]
    assert "scheduler_hook_plan_allowed_next must be true" in plan["issues"]
