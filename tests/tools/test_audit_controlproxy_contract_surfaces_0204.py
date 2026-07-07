from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_controlproxy_contract_surfaces.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("audit_controlproxy_contract_surfaces_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _acceptance_fixture(tmp_path: Path) -> dict:
    return {
        "schema": "missipy.scheduler.controlled_hook_smoke_acceptance.v1",
        "controlled_scheduler_hook_smoke_accepted": True,
        "bloc_c_complete": True,
        "next_bloc": "D",
        "accepted_baseline": "controlled-scheduler-hook-routeproxy-write-read-v1",
        "policy_decision_id": "policy:allow:scheduler-hook:manual0203-b",
        "target_runtime_root": str(tmp_path / "runtime" / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "runtime" / "dev-controlled" / "routeproxy-isolated"),
        "issues": [],
        "warnings": [],
        "existing_surfaces_reused": True,
        "frames_written_count": 1,
        "readback_count": 1,
        "provenance_repair_items": [
            "source_baseline_ref or source_entry_digest missing from P0200 acceptance; preserve this as a provenance repair item"
        ],
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "eventbus_instantiated": False,
        "network_used": False,
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


def _write_surface(root: Path, relative: str, source: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def _write_existing_surfaces(root: Path) -> None:
    _write_surface(
        root,
        "src/runtime/controlproxy_scheduler_handler.py",
        "class ControlProxySchedulerRouteRequestHandler:\n    def handle(self):\n        pass\n"
        "def handle_scheduler_route_request():\n    pass\n"
        "def resolve_scheduler_route_request_handler():\n    pass\n"
        "def scheduler_route_request_payload():\n    pass\n"
        "ControlProxy = 'ControlProxy'\nSchedulerRouteRequest = 'SchedulerRouteRequest'\n",
    )
    _write_surface(
        root,
        "src/runtime/scheduler_route_adapter.py",
        "class SchedulerRouteRequest:\n    pass\n"
        "class SchedulerRouteReply:\n    pass\n"
        "def scheduler_route_request_mapping():\n    pass\n"
        "def handle_scheduler_route_request():\n    pass\n"
        "policy_decision_id = 'policy_decision_id'\nscope = 'scope'\nholder = 'holder'\n",
    )
    _write_surface(
        root,
        "src/runtime/scheduler_route_handler_minimal.py",
        "class SchedulerRouteHandlerCommand:\n    pass\n"
        "def build_single_frame_route_command():\n    pass\n"
        "def handle_scheduler_route_command():\n    pass\n"
        "def read_scheduler_route_handler_result_frames():\n    pass\n"
        "priority = 'priority'\nruntime_policy = 'runtime_policy'\nroute_ref = 'route_ref'\n",
    )
    _write_surface(
        root,
        "src/runtime/route_proxy_runtime_minimal.py",
        "class RouteProxyRuntimePolicy:\n    pass\n"
        "def prepare_route_proxy_runtime():\n    pass\n"
        "def request_writer_permit():\n    pass\n"
        "def write_route_frame():\n    pass\n"
        "def read_route_frame():\n    pass\n"
        "def mark_route_frame_stale():\n    pass\n"
        "stale = 'stale'\npriority = 'priority'\nroute_root = 'route_root'\n",
    )
    _write_surface(
        root,
        "src/runtime/shm_runtime_schema.py",
        "class EventBusMessage:\n    pass\nclass ContextBusMessage:\n    pass\nclass RouteMessage:\n    pass\n"
        "topic = 'topic'\nschema = 'schema'\npayload = 'payload'\n",
    )
    _write_surface(root, "src/runtime/bus_visualization_adapter.py", "graph = 'graph'\nedge = 'edge'\nnode = 'node'\n")


def test_0204_audits_controlproxy_contract_surfaces(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_existing_surfaces(repo)
    acceptance_path = tmp_path / "controlled_scheduler_hook_smoke_acceptance.json"
    output = tmp_path / "controlproxy_contract_audit.json"
    acceptance_path.write_text(json.dumps(_acceptance_fixture(tmp_path), indent=2), encoding="utf-8")

    audit = module.audit_controlproxy_contract_surfaces(
        acceptance_path=acceptance_path,
        repo_root=repo,
        output_path=output,
    )

    assert audit["controlproxy_contract_audit_success"] is True
    assert audit["stale_priority_zone_plan_allowed_next"] is True
    assert audit["existing_surface_count"] == 6
    assert audit["next_recommended_patch"] == "0205-controlproxy_stale_priority_zone_smoke_plan"
    assert audit["recommended_contract"]["authority"] == "Scheduler/policy/zone"
    assert audit["recommended_contract"]["coordination_surface"] == "ControlProxy"
    assert audit["recommended_contract"]["data_plane"] == "RouteProxy"
    assert audit["existing_surfaces_reused"] is True
    assert audit["new_controlproxy_runtime_added"] is False
    assert audit["runtime_imports_executed_by_0204"] is False
    assert audit["frames_written_by_0204"] is False
    assert audit["controlproxy_frames_written_by_0204"] is False
    assert audit["provenance_repair_items"]
    assert output.exists()


def test_0204_rejects_missing_required_controlproxy_surface(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_existing_surfaces(repo)
    (repo / "src/runtime/controlproxy_scheduler_handler.py").unlink()
    acceptance_path = tmp_path / "controlled_scheduler_hook_smoke_acceptance.json"
    acceptance_path.write_text(json.dumps(_acceptance_fixture(tmp_path), indent=2), encoding="utf-8")

    audit = module.audit_controlproxy_contract_surfaces(
        acceptance_path=acceptance_path,
        repo_root=repo,
    )

    assert audit["controlproxy_contract_audit_success"] is False
    assert "missing existing surface: src/runtime/controlproxy_scheduler_handler.py" in audit["issues"]
