from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_controlproxy_stale_priority_zone_smoke.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("plan_controlproxy_stale_priority_zone_smoke_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _surface_report(path: str, *, optional: bool = False, missing_tokens=None) -> dict:
    return {
        "path": path,
        "role": "role",
        "optional": optional,
        "exists": True,
        "parse_error": "",
        "function_count": 1,
        "class_count": 1,
        "functions": ["fn"],
        "classes": ["Class"],
        "required_symbols": [],
        "required_tokens": [],
        "matched_required_symbols": [],
        "missing_required_symbols": [],
        "missing_required_tokens": list(missing_tokens or []),
        "use_before_new_code": True,
    }


def _audit_fixture(tmp_path: Path, *, success: bool = True) -> dict:
    return {
        "schema": "missipy.controlproxy.contract_audit.v1",
        "bloc": "D",
        "bloc_name": "controlproxy-contract-and-priority",
        "accepted_baseline": "controlled-scheduler-hook-routeproxy-write-read-v1",
        "policy_decision_id": "policy:allow:scheduler-hook:manual0203-b",
        "target_runtime_root": str(tmp_path / "runtime" / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "runtime" / "dev-controlled" / "routeproxy-isolated"),
        "controlproxy_contract_audit_success": success,
        "stale_priority_zone_plan_allowed_next": success,
        "next_recommended_patch": "0205-controlproxy_stale_priority_zone_smoke_plan",
        "recommended_contract": {
            "authority": "Scheduler/policy/zone",
            "coordination_surface": "ControlProxy",
            "data_plane": "RouteProxy",
            "planned_next_patch": "0205-controlproxy_stale_priority_zone_smoke_plan",
        },
        "contract_decisions": [
            "ControlProxy remains a coordination and contract surface, not business authority.",
            "Scheduler/policy/zone remain authority.",
            "RouteProxy remains the fast data-plane frame surface.",
        ],
        "provenance_repair_items": [
            "source_baseline_ref or source_entry_digest missing from P0200 acceptance; preserve this as a provenance repair item"
        ],
        "issues": [] if success else ["controlproxy_contract_audit_success must be true"],
        "warnings": ["optional representation surface missing token graph in src/runtime/bus_visualization_adapter.py"],
        "existing_surfaces_reused": True,
        "runtime_imports_executed_by_0204": False,
        "scheduler_run_executed": False,
        "handler_called_by_0204": False,
        "routeproxy_prepared_by_0204": False,
        "read_route_frame_called_by_0204": False,
        "writer_permits_requested_by_0204": False,
        "frames_written_by_0204": False,
        "controlproxy_frames_written_by_0204": False,
        "eventbus_instantiated_by_0204": False,
        "network_used_by_0204": False,
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
        "surface_reports": [
            _surface_report("src/runtime/controlproxy_scheduler_handler.py"),
            _surface_report("src/runtime/scheduler_route_adapter.py"),
            _surface_report("src/runtime/scheduler_route_handler_minimal.py"),
            _surface_report("src/runtime/route_proxy_runtime_minimal.py"),
            _surface_report("src/runtime/shm_runtime_schema.py"),
            _surface_report("src/runtime/bus_visualization_adapter.py", optional=True, missing_tokens=["graph", "edge", "node"]),
        ],
    }


def test_0205_plans_controlproxy_stale_priority_zone_smoke(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "controlproxy_contract_audit.json"
    output = tmp_path / "controlproxy_stale_priority_zone_smoke_plan.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path), indent=2), encoding="utf-8")

    plan = module.plan_controlproxy_stale_priority_zone_smoke(
        contract_audit_path=audit_path,
        output_path=output,
    )

    assert plan["controlproxy_stale_priority_zone_smoke_plan_ready"] is True
    assert plan["execution_allowed_by_0205"] is False
    assert plan["controlproxy_frame_write_allowed_by_0205"] is False
    assert plan["routeproxy_frame_write_allowed_by_0205"] is False
    assert plan["p0206_may_execute_controlled_stale_priority_zone_smoke"] is True
    assert plan["planned_next_patch"] == "0206-controlproxy_routeproxy_coherence_acceptance"
    assert plan["planned_contract_path"] == "Scheduler/policy/zone -> ControlProxy contract -> RouteProxy stale priority zone data-plane"
    assert plan["existing_surfaces_reused"] is True
    assert plan["new_controlproxy_runtime_added"] is False
    assert plan["mark_route_frame_stale_called_by_0205"] is False
    assert plan["frames_written_by_0205"] is False
    assert plan["controlproxy_frames_written_by_0205"] is False
    assert plan["provenance_repair_items"]
    assert output.exists()


def test_0205_rejects_failed_controlproxy_contract_audit(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "controlproxy_contract_audit.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path, success=False), indent=2), encoding="utf-8")

    plan = module.plan_controlproxy_stale_priority_zone_smoke(contract_audit_path=audit_path)

    assert plan["controlproxy_stale_priority_zone_smoke_plan_ready"] is False
    assert plan["p0206_may_execute_controlled_stale_priority_zone_smoke"] is False
    assert "controlproxy_contract_audit_success must be true" in plan["issues"]
    assert "stale_priority_zone_plan_allowed_next must be true" in plan["issues"]
