from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_context_recall_integration.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("plan_context_recall_integration_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _surface(path: str, tokens: list[str]) -> dict:
    return {"path": path, "matched_tokens": tokens, "use_before_new_code": True}


def _audit_fixture(tmp_path: Path, *, success: bool = True) -> dict:
    return {
        "schema": "missipy.context_recall.integration_audit.v1",
        "bloc": "G",
        "target_runtime_root": str(tmp_path / "runtime" / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "runtime" / "dev-controlled" / "routeproxy-isolated"),
        "sql_ref": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5",
        "qdrant_payload": {"sql_ref": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5"},
        "projection_digest": "664d37d9325811349ade719e09a089df43759c439a2dc01b998e7c8365f5caca",
        "source_entry_digest": "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855",
        "repair_digest": "00750a169d8d765968a6aee28a5d26a9342aa53f2922bb3b865a13bf3a320b88",
        "context_recall_integration_audit_success": success,
        "context_recall_integration_plan_allowed_next": success,
        "planned_next_patch": "0214-context_recall_integration_plan",
        "target_path": "context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact",
        "issues": [] if success else ["context_recall_integration_audit_success must be true"],
        "warnings": [],
        "existing_surfaces_reused": True,
        "context_surface_count": 1,
        "recall_surface_count": 1,
        "rehydrate_surface_count": 1,
        "response_surface_count": 1,
        "projection_surface_count": 1,
        "context_surfaces": [_surface("src/context/context_recall_contract.py", ["context", "query", "artifact"])],
        "recall_surfaces": [_surface("src/context/context_recall_contract.py", ["Qdrant", "recall", "vector"])],
        "rehydrate_surfaces": [_surface("src/context/context_recall_contract.py", ["sql_ref", "rehydrate", "get_record"])],
        "response_surfaces": [_surface("src/context/context_recall_contract.py", ["response", "result", "to_mapping"])],
        "projection_surfaces": [_surface("tools/projection_acceptance.py", ["controlled_sql_qdrant_projection_acceptance", "qdrant_payload", "sql_ref"])],
        "integration_contract": {
            "input": "context/query artifact",
            "recall": "Qdrant recall returns sql_ref",
            "rehydration": "SQL authority hydrates sql_ref",
            "output": "response/result artifact",
            "authority": "SQL remains durable authority",
            "projection": "Qdrant remains projection/search/recall only",
        },
        "runtime_imports_executed_by_0213": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0213": False,
        "routeproxy_prepared_by_0213": False,
        "read_route_frame_called_by_0213": False,
        "writer_permits_requested_by_0213": False,
        "frames_written_by_0213": False,
        "controlproxy_frames_written_by_0213": False,
        "eventbus_instantiated_by_0213": False,
        "network_used_by_0213": False,
        "sql_record_read_by_0213": False,
        "qdrant_queried_by_0213": False,
        "recall_executed_by_0213": False,
        "sql_written_by_0213": False,
        "qdrant_written_by_0213": False,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_scheduler_added": False,
        "new_controlproxy_runtime_added": False,
        "new_routeproxy_runtime_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
        "new_graph_renderer_added": False,
        "new_inference_path_added": False,
    }


def test_0214_plans_context_recall_integration_without_execution(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "context_recall_integration_audit.json"
    output = tmp_path / "context_recall_integration_plan.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path), indent=2), encoding="utf-8")

    plan = module.plan_context_recall_integration(
        integration_audit_path=audit_path,
        output_path=output,
    )

    assert plan["context_recall_integration_plan_ready"] is True
    assert plan["execution_allowed_by_0214"] is False
    assert plan["recall_execution_allowed_by_0214"] is False
    assert plan["qdrant_query_allowed_by_0214"] is False
    assert plan["sql_record_read_allowed_by_0214"] is False
    assert plan["sql_write_allowed_by_0214"] is False
    assert plan["qdrant_write_allowed_by_0214"] is False
    assert plan["p0215_may_execute_controlled_context_recall_acceptance"] is True
    assert plan["integration_strategy"] == "context_query_qdrant_recall_sql_ref_sql_rehydrate_response_artifact"
    assert plan["target_path"] == "context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact"
    assert plan["context_query_surface"]["path"] == "src/context/context_recall_contract.py"
    assert plan["recall_surface"]["path"] == "src/context/context_recall_contract.py"
    assert plan["rehydrate_surface"]["path"] == "src/context/context_recall_contract.py"
    assert plan["response_surface"]["path"] == "src/context/context_recall_contract.py"
    assert plan["projection_surface"]["path"] == "tools/projection_acceptance.py"
    assert plan["planned_next_patch"] == "0215-controlled_context_recall_integration_acceptance"
    assert plan["recall_executed_by_0214"] is False
    assert plan["sql_record_read_by_0214"] is False
    assert plan["qdrant_queried_by_0214"] is False
    assert output.exists()


def test_0214_rejects_failed_integration_audit(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "context_recall_integration_audit.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path, success=False), indent=2), encoding="utf-8")

    plan = module.plan_context_recall_integration(integration_audit_path=audit_path)

    assert plan["context_recall_integration_plan_ready"] is False
    assert plan["p0215_may_execute_controlled_context_recall_acceptance"] is False
    assert "context_recall_integration_audit_success must be true" in plan["issues"]
    assert "context_recall_integration_plan_allowed_next must be true" in plan["issues"]
