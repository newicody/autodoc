from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_prototype_live_execution.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("plan_prototype_live_execution_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _audit_fixture(tmp_path: Path, *, success: bool = True, probe_success: bool = True) -> dict:
    runtime = tmp_path / "runtime" / "dev-controlled"
    sql_ref = "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5"
    return {
        "schema": "missipy.prototype.live_readiness_audit.v1",
        "bloc": "H",
        "target_runtime_root": str(runtime),
        "target_isolated_runtime_root": str(runtime / "routeproxy-isolated"),
        "prototype_live_root": str(runtime / "prototype-live"),
        "prototype_live_readiness_audit_success": success,
        "prototype_live_execution_plan_allowed_next": success,
        "planned_next_patch": "0217-prototype_live_execution_plan",
        "target_path": "context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact",
        "sql_ref": sql_ref,
        "qdrant_payload": {"sql_ref": sql_ref},
        "projection_digest": "projection-digest",
        "integration_digest": "integration-digest",
        "source_entry_digest": "source-entry-digest",
        "issues": [] if success else ["not ready"],
        "warnings": [],
        "existing_surfaces_reused": True,
        "live_requirements": {
            "prototype_live_root": str(runtime / "prototype-live"),
            "qdrant_url": "http://127.0.0.1:6333",
            "qdrant_collection": "autodoc_prototype_live",
            "sql_dev_store": str(runtime / "prototype-live" / "prototype_live_sql.jsonl"),
            "response_artifact": str(runtime / "prototype-live" / "prototype_live_response.json"),
            "vector_dimension": 4,
            "vector_mode": "deterministic_test_vector_until_embedding_backend_is_explicitly_selected",
            "must_write_sql_by_p0218": True,
            "must_upsert_qdrant_by_p0218": True,
            "must_query_qdrant_by_p0218": True,
            "must_read_sql_by_p0218": True,
            "must_rehydrate_by_p0218": True,
            "must_write_response_artifact_by_p0218": True,
            "must_set_prototype_success_by_p0218": True,
        },
        "live_boundary": {
            "local_qdrant_only": True,
            "external_network_allowed": False,
            "github_api_allowed": False,
            "scheduler_run_allowed": False,
        },
        "qdrant_local_probe": {"probe_success": probe_success},
        "p0218_required_true_flags": [
            "sql_written_by_0218",
            "qdrant_written_by_0218",
            "qdrant_queried_by_0218",
            "sql_record_read_by_0218",
            "rehydration_executed_by_0218",
            "response_artifact_written_by_0218",
            "prototype_success",
        ],
        "selected_surfaces": {},
        "runtime_imports_executed_by_0216": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0216": False,
        "routeproxy_prepared_by_0216": False,
        "read_route_frame_called_by_0216": False,
        "writer_permits_requested_by_0216": False,
        "frames_written_by_0216": False,
        "controlproxy_frames_written_by_0216": False,
        "eventbus_instantiated_by_0216": False,
        "external_network_used_by_0216": False,
        "live_qdrant_query_executed_by_0216": False,
        "qdrant_queried_by_0216": False,
        "sql_record_read_by_0216": False,
        "recall_executed_by_0216": False,
        "sql_write_allowed_by_0216": False,
        "qdrant_write_allowed_by_0216": False,
        "sql_written_by_0216": False,
        "qdrant_written_by_0216": False,
        "runtime_history_rewritten_by_0216": False,
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


def test_0217_plans_live_prototype_execution_without_running_it(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "prototype_live_readiness_audit.json"
    audit = _audit_fixture(tmp_path)
    runtime = Path(audit["target_runtime_root"])
    runtime.mkdir(parents=True, exist_ok=True)
    output = runtime / "prototype_live_execution_plan.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    plan = module.plan_prototype_live_execution(
        live_readiness_audit_path=audit_path,
        output_path=output,
        require_qdrant_probe_success=True,
    )

    assert plan["prototype_live_execution_plan_ready"] is True
    assert plan["p0218_may_execute_live_prototype"] is True
    assert plan["planned_next_patch"] == "0218-prototype_live_execution_acceptance"
    assert plan["target_path"] == "context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact"
    assert plan["prototype_expected_result"]["sql_written_by_0218"] is True
    assert plan["prototype_expected_result"]["qdrant_written_by_0218"] is True
    assert plan["prototype_expected_result"]["qdrant_queried_by_0218"] is True
    assert plan["prototype_expected_result"]["sql_record_read_by_0218"] is True
    assert plan["prototype_expected_result"]["rehydration_executed_by_0218"] is True
    assert plan["prototype_expected_result"]["response_artifact_written_by_0218"] is True
    assert plan["prototype_expected_result"]["prototype_success"] is True
    assert plan["qdrant_requests"]["create_collection_request"]["json"]["vectors"]["size"] == 4
    assert plan["qdrant_requests"]["upsert_request"]["json"]["points"][0]["payload"]["sql_ref"] == plan["sql_ref"]
    assert plan["qdrant_requests"]["search_request"]["json"]["limit"] == 1
    assert plan["sql_written_by_0217"] is False
    assert plan["qdrant_written_by_0217"] is False
    assert plan["qdrant_queried_by_0217"] is False
    assert output.exists()


def test_0217_rejects_missing_required_qdrant_probe(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "prototype_live_readiness_audit.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path, probe_success=False), indent=2), encoding="utf-8")

    plan = module.plan_prototype_live_execution(
        live_readiness_audit_path=audit_path,
        require_qdrant_probe_success=True,
    )

    assert plan["prototype_live_execution_plan_ready"] is False
    assert "qdrant_local_probe.probe_success must be true when required" in plan["issues"]


def test_0217_rejects_failed_readiness(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "prototype_live_readiness_audit.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path, success=False), indent=2), encoding="utf-8")

    plan = module.plan_prototype_live_execution(live_readiness_audit_path=audit_path)

    assert plan["prototype_live_execution_plan_ready"] is False
    assert "prototype_live_readiness_audit_success must be true" in plan["issues"]
    assert "prototype_live_execution_plan_allowed_next must be true" in plan["issues"]
