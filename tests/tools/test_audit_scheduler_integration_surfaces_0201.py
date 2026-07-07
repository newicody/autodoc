from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_scheduler_integration_surfaces.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("audit_scheduler_integration_surfaces_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _acceptance_fixture(tmp_path: Path) -> dict:
    return {
        "schema": "missipy.route_pipeline.controlled_dev_post_execution_acceptance.v1",
        "controlled_dev_smoke_accepted": True,
        "bloc_b_complete": True,
        "next_bloc": "C",
        "accepted_baseline": "controlled-dev-routeproxy-write-read-v1",
        "controlled_dev_baseline_ref": "baseline:controlled-dev-routeproxy-write-read-v1:0123456789abcdef",
        "policy_decision_id": "policy:allow:controlled-dev:manual0199",
        "target_runtime_root": str(tmp_path / "runtime" / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "runtime" / "dev-controlled" / "routeproxy-isolated"),
        "source_baseline_ref": "",
        "source_entry_digest": "",
        "issues": [],
        "warnings": [],
        "existing_surfaces_reused": True,
        "frames_written_count": 1,
        "readback_count": 1,
        "runtime_imports_executed_by_0200": False,
        "handler_called_by_0200": False,
        "routeproxy_prepared_by_0200": False,
        "read_route_frame_called_by_0200": False,
        "writer_permits_requested_by_0200": False,
        "frames_written_by_0200": False,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "eventbus_instantiated": False,
        "network_used": False,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
    }


def _write_surface(root: Path, relative: str, source: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def _write_existing_surfaces(root: Path) -> None:
    _write_surface(root, "src/runtime/scheduler_route_adapter.py", "def scheduler_route_request_mapping():\n    pass\n")
    _write_surface(root, "src/runtime/scheduler_route_handshake.py", "def prepare_route_for_scheduler():\n    pass\n")
    _write_surface(
        root,
        "src/runtime/scheduler_route_handler_minimal.py",
        "def build_single_frame_route_command():\n    pass\n"
        "def handle_scheduler_route_command():\n    pass\n"
        "def read_scheduler_route_handler_result_frames():\n    pass\n",
    )
    _write_surface(root, "src/runtime/controlproxy_scheduler_handler.py", "def handle_scheduler_route_request():\n    pass\n")
    _write_surface(
        root,
        "src/runtime/route_proxy_runtime_minimal.py",
        "class RouteProxyRuntimePolicy:\n    pass\n"
        "def prepare_route_proxy_runtime():\n    pass\n",
    )
    _write_surface(
        root,
        "src/runtime/shm_runtime_schema.py",
        "class EventBusMessage:\n    pass\n"
        "class ContextBusMessage:\n    pass\n",
    )


def test_0201_audits_existing_scheduler_surfaces(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_existing_surfaces(repo)
    acceptance_path = tmp_path / "controlled_dev_routeproxy_smoke_post_execution_acceptance.json"
    output = tmp_path / "scheduler_integration_surface_audit.json"
    acceptance_path.write_text(json.dumps(_acceptance_fixture(tmp_path), indent=2), encoding="utf-8")

    audit = module.audit_scheduler_integration_surfaces(
        acceptance_path=acceptance_path,
        repo_root=repo,
        output_path=output,
    )

    assert audit["integration_surface_audit_success"] is True
    assert audit["scheduler_hook_plan_allowed_next"] is True
    assert audit["existing_surface_count"] == 6
    assert audit["next_recommended_patch"] == "0202-scheduler_hook_dry_run_plan"
    assert audit["existing_surfaces_reused"] is True
    assert audit["new_runtime_handler_added"] is False
    assert audit["new_adapter_added"] is False
    assert audit["runtime_imports_executed_by_0201"] is False
    assert audit["scheduler_run_executed"] is False
    assert audit["frames_written_by_0201"] is False
    assert audit["provenance_warning"]
    assert output.exists()


def test_0201_rejects_missing_scheduler_surface(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_existing_surfaces(repo)
    (repo / "src/runtime/scheduler_route_adapter.py").unlink()
    acceptance_path = tmp_path / "controlled_dev_routeproxy_smoke_post_execution_acceptance.json"
    acceptance_path.write_text(json.dumps(_acceptance_fixture(tmp_path), indent=2), encoding="utf-8")

    audit = module.audit_scheduler_integration_surfaces(
        acceptance_path=acceptance_path,
        repo_root=repo,
    )

    assert audit["integration_surface_audit_success"] is False
    assert "missing existing surface: src/runtime/scheduler_route_adapter.py" in audit["issues"]
