from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "accept_controlled_context_recall_integration.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("accept_controlled_context_recall_integration_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _surface(path: str, tokens: list[str]) -> dict:
    return {"path": path, "matched_tokens": tokens, "use_before_new_code": True}


def _plan_fixture(tmp_path: Path, *, ready: bool = True) -> dict:
    return {
        "schema": "missipy.context_recall.integration_plan.v1",
        "bloc": "G",
        "target_runtime_root": str(tmp_path / "runtime" / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "runtime" / "dev-controlled" / "routeproxy-isolated"),
        "sql_ref": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5",
        "qdrant_payload": {"sql_ref": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5"},
        "projection_digest": "664d37d9325811349ade719e09a089df43759c439a2dc01b998e7c8365f5caca",
        "source_entry_digest": "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855",
        "repair_digest": "00750a169d8d765968a6aee28a5d26a9342aa53f2922bb3b865a13bf3a320b88",
        "context_recall_integration_plan_ready": ready,
        "integration_strategy": "context_query_qdrant_recall_sql_ref_sql_rehydrate_response_artifact",
        "target_path": "context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact",
        "p0215_may_execute_controlled_context_recall_acceptance": ready,
        "planned_next_patch": "0215-controlled_context_recall_integration_acceptance",
        "issues": [] if ready else ["context_recall_integration_plan_ready must be true"],
        "warnings": [],
        "existing_surfaces_reused": True,
        "context_query_surface": _surface("src/context/artifact_intake_contract.py", ["artifact", "query"]),
        "recall_surface": _surface("src/context/context_graph_export.py", ["Qdrant", "qdrant", "recall", "vector"]),
        "rehydrate_surface": _surface("tools/accept_controlled_sql_qdrant_projection.py", ["rehydrate", "sql_ref"]),
        "response_surface": _surface("src/context/github_project_push_frame.py", ["artifact", "response"]),
        "projection_surface": _surface("tools/accept_controlled_sql_qdrant_projection.py", ["controlled_sql_qdrant_projection_acceptance", "qdrant_payload", "sql_ref"]),
        "integration_contract": {
            "input": "context/query artifact",
            "recall": "Qdrant recall returns sql_ref",
            "rehydration": "SQL authority hydrates sql_ref",
            "output": "response/result artifact",
            "authority": "SQL remains durable authority",
            "projection": "Qdrant remains projection/search/recall only",
        },
        "execution_allowed_by_0214": False,
        "recall_execution_allowed_by_0214": False,
        "qdrant_query_allowed_by_0214": False,
        "sql_record_read_allowed_by_0214": False,
        "sql_write_allowed_by_0214": False,
        "qdrant_write_allowed_by_0214": False,
        "runtime_imports_executed_by_0214": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0214": False,
        "routeproxy_prepared_by_0214": False,
        "read_route_frame_called_by_0214": False,
        "writer_permits_requested_by_0214": False,
        "frames_written_by_0214": False,
        "controlproxy_frames_written_by_0214": False,
        "eventbus_instantiated_by_0214": False,
        "network_used_by_0214": False,
        "sql_record_read_by_0214": False,
        "qdrant_queried_by_0214": False,
        "recall_executed_by_0214": False,
        "sql_written_by_0214": False,
        "qdrant_written_by_0214": False,
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


def _write_repo_surfaces(repo: Path) -> None:
    (repo / "src/context").mkdir(parents=True)
    (repo / "tools").mkdir(parents=True)
    (repo / "src/context/artifact_intake_contract.py").write_text("artifact query\n", encoding="utf-8")
    (repo / "src/context/context_graph_export.py").write_text("Qdrant qdrant recall vector\n", encoding="utf-8")
    (repo / "tools/accept_controlled_sql_qdrant_projection.py").write_text(
        "rehydrate sql_ref controlled_sql_qdrant_projection_acceptance qdrant_payload\n",
        encoding="utf-8",
    )
    (repo / "src/context/github_project_push_frame.py").write_text("artifact response\n", encoding="utf-8")


def test_0215_accepts_controlled_context_recall_integration(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_repo_surfaces(repo)
    plan = _plan_fixture(tmp_path)
    runtime = Path(plan["target_runtime_root"])
    runtime.mkdir(parents=True)
    plan_path = runtime / "context_recall_integration_plan.json"
    output = runtime / "controlled_context_recall_integration_acceptance.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    acceptance = module.accept_controlled_context_recall_integration(
        integration_plan_path=plan_path,
        repo_root=repo,
        output_path=output,
    )

    assert acceptance["controlled_context_recall_integration_accepted"] is True
    assert acceptance["context_recall_integration_contract_accepted"] is True
    assert acceptance["bloc_g_complete"] is True
    assert acceptance["payload_contains_sql_ref"] is True
    assert acceptance["controlled_recall_result"]["sql_ref"] == plan["sql_ref"]
    assert acceptance["controlled_recall_result"]["live_qdrant_query_executed"] is False
    assert acceptance["controlled_rehydrate_result"]["sql_record_read"] is False
    assert acceptance["response_artifact"]["rehydration_required"] is True
    assert acceptance["live_qdrant_query_executed_by_0215"] is False
    assert acceptance["qdrant_queried_by_0215"] is False
    assert acceptance["sql_record_read_by_0215"] is False
    assert acceptance["recall_executed_by_0215"] is False
    assert acceptance["sql_written_by_0215"] is False
    assert acceptance["qdrant_written_by_0215"] is False
    assert acceptance["new_inference_path_added"] is False
    assert acceptance["next_recommended_patch"] == "0216-prototype_readiness_audit"
    assert output.exists()


def test_0215_rejects_unready_context_recall_plan(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_repo_surfaces(repo)
    plan = _plan_fixture(tmp_path, ready=False)
    runtime = Path(plan["target_runtime_root"])
    runtime.mkdir(parents=True)
    plan_path = runtime / "context_recall_integration_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    acceptance = module.accept_controlled_context_recall_integration(
        integration_plan_path=plan_path,
        repo_root=repo,
        output_path=runtime / "controlled_context_recall_integration_acceptance.json",
    )

    assert acceptance["controlled_context_recall_integration_accepted"] is False
    assert acceptance["bloc_g_complete"] is False
    assert "context_recall_integration_plan_ready must be true" in acceptance["issues"]
    assert "p0215_may_execute_controlled_context_recall_acceptance must be true" in acceptance["issues"]
