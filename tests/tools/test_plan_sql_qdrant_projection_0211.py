from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_sql_qdrant_projection.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("plan_sql_qdrant_projection_tool", TOOL)
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
        "schema": "missipy.sql_qdrant.projection_readiness_audit.v1",
        "bloc": "F",
        "target_runtime_root": str(tmp_path / "runtime" / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "runtime" / "dev-controlled" / "routeproxy-isolated"),
        "source_baseline_ref": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5",
        "source_entry_digest": "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855",
        "repair_digest": "00750a169d8d765968a6aee28a5d26a9342aa53f2922bb3b865a13bf3a320b88",
        "sql_qdrant_projection_readiness_audit_success": success,
        "sql_qdrant_projection_plan_allowed_next": success,
        "planned_next_patch": "0211-sql_qdrant_projection_plan",
        "issues": [] if success else ["sql_qdrant_projection_readiness_audit_success must be true"],
        "warnings": [],
        "existing_surfaces_reused": True,
        "sql_surface_count": 1,
        "qdrant_surface_count": 1,
        "rehydrate_surface_count": 1,
        "provenance_surface_count": 1,
        "sql_surfaces": [_surface("src/runtime/sql_context_store.py", ["DbApiSqlContextStore", "SQL", "sql_ref"])],
        "qdrant_surfaces": [_surface("tools/qdrant_recall.py", ["Qdrant", "qdrant", "vector", "collection"])],
        "rehydrate_surfaces": [_surface("tools/qdrant_recall.py", ["rehydrate", "get_record", "sql_ref"])],
        "provenance_surfaces": [_surface("doc/provenance.md", ["provenance_repair_acceptance", "source_baseline_ref", "source_entry_digest"])],
        "projection_contract": {
            "sql_role": "durable authority",
            "qdrant_role": "projection/search/recall only",
            "payload_contract": "Qdrant payloads carry sql_ref",
            "rehydration_contract": "hydrate returned sql_ref from SQL authority",
            "provenance_contract": "use forward-only provenance repair acceptance as chain repair proof",
        },
        "runtime_imports_executed_by_0210": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0210": False,
        "routeproxy_prepared_by_0210": False,
        "read_route_frame_called_by_0210": False,
        "writer_permits_requested_by_0210": False,
        "frames_written_by_0210": False,
        "controlproxy_frames_written_by_0210": False,
        "eventbus_instantiated_by_0210": False,
        "network_used_by_0210": False,
        "sql_write_allowed_by_0210": False,
        "qdrant_write_allowed_by_0210": False,
        "sql_written_by_0210": False,
        "qdrant_written_by_0210": False,
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


def test_0211_plans_sql_qdrant_projection_without_writes(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "sql_qdrant_projection_readiness_audit.json"
    output = tmp_path / "sql_qdrant_projection_plan.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path), indent=2), encoding="utf-8")

    plan = module.plan_sql_qdrant_projection(
        readiness_audit_path=audit_path,
        output_path=output,
    )

    assert plan["sql_qdrant_projection_plan_ready"] is True
    assert plan["execution_allowed_by_0211"] is False
    assert plan["sql_write_allowed_by_0211"] is False
    assert plan["qdrant_write_allowed_by_0211"] is False
    assert plan["projection_write_allowed_by_0211"] is False
    assert plan["p0212_may_execute_controlled_projection_acceptance"] is True
    assert plan["projection_strategy"] == "sql_authority_qdrant_projection_sql_ref_rehydrate"
    assert plan["sql_authority_surface"]["path"] == "src/runtime/sql_context_store.py"
    assert plan["qdrant_projection_surface"]["path"] == "tools/qdrant_recall.py"
    assert plan["rehydrate_surface"]["path"] == "tools/qdrant_recall.py"
    assert plan["provenance_surface"]["path"] == "doc/provenance.md"
    assert plan["planned_next_patch"] == "0212-controlled_sql_qdrant_projection_acceptance"
    assert plan["sql_written_by_0211"] is False
    assert plan["qdrant_written_by_0211"] is False
    assert output.exists()


def test_0211_rejects_failed_readiness_audit(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "sql_qdrant_projection_readiness_audit.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path, success=False), indent=2), encoding="utf-8")

    plan = module.plan_sql_qdrant_projection(readiness_audit_path=audit_path)

    assert plan["sql_qdrant_projection_plan_ready"] is False
    assert plan["p0212_may_execute_controlled_projection_acceptance"] is False
    assert "sql_qdrant_projection_readiness_audit_success must be true" in plan["issues"]
    assert "sql_qdrant_projection_plan_allowed_next must be true" in plan["issues"]
