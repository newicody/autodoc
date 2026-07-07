from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "accept_controlled_sql_qdrant_projection.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("accept_controlled_sql_qdrant_projection_tool", TOOL)
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
        "schema": "missipy.sql_qdrant.projection_plan.v1",
        "bloc": "F",
        "target_runtime_root": str(tmp_path / "runtime" / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "runtime" / "dev-controlled" / "routeproxy-isolated"),
        "source_baseline_ref": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5",
        "source_entry_digest": "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855",
        "repair_digest": "00750a169d8d765968a6aee28a5d26a9342aa53f2922bb3b865a13bf3a320b88",
        "sql_qdrant_projection_plan_ready": ready,
        "projection_strategy": "sql_authority_qdrant_projection_sql_ref_rehydrate",
        "p0212_may_execute_controlled_projection_acceptance": ready,
        "planned_next_patch": "0212-controlled_sql_qdrant_projection_acceptance",
        "issues": [] if ready else ["sql_qdrant_projection_plan_ready must be true"],
        "warnings": [],
        "existing_surfaces_reused": True,
        "sql_authority_surface": _surface("src/context/artifact_intake_contract.py", ["SQL", "sql_ref"]),
        "qdrant_projection_surface": _surface("src/context/artifact_intake_contract.py", ["Qdrant", "vector", "collection"]),
        "rehydrate_surface": _surface("src/context/artifact_intake_contract.py", ["sql_ref"]),
        "provenance_surface": _surface("tools/audit_sql_qdrant_projection_readiness.py", ["provenance_repair_acceptance", "source_baseline_ref"]),
        "projection_contract": {
            "sql_role": "durable authority",
            "qdrant_role": "projection/search/recall only",
            "payload_contract": "Qdrant payloads carry sql_ref",
            "rehydration_contract": "hydrate returned sql_ref from SQL authority",
        },
        "execution_allowed_by_0211": False,
        "sql_write_allowed_by_0211": False,
        "qdrant_write_allowed_by_0211": False,
        "projection_write_allowed_by_0211": False,
        "runtime_imports_executed_by_0211": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0211": False,
        "routeproxy_prepared_by_0211": False,
        "read_route_frame_called_by_0211": False,
        "writer_permits_requested_by_0211": False,
        "frames_written_by_0211": False,
        "controlproxy_frames_written_by_0211": False,
        "eventbus_instantiated_by_0211": False,
        "network_used_by_0211": False,
        "sql_written_by_0211": False,
        "qdrant_written_by_0211": False,
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
    (repo / "src/context/artifact_intake_contract.py").write_text(
        "SQL = 'SQL'\nsql_ref = 'sql_ref'\nQdrant = 'Qdrant'\nvector = 'vector'\ncollection = 'collection'\n",
        encoding="utf-8",
    )
    (repo / "tools/audit_sql_qdrant_projection_readiness.py").write_text(
        "provenance_repair_acceptance source_baseline_ref source_entry_digest\n",
        encoding="utf-8",
    )


def test_0212_accepts_controlled_sql_qdrant_projection_contract(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_repo_surfaces(repo)
    plan = _plan_fixture(tmp_path)
    runtime = Path(plan["target_runtime_root"])
    runtime.mkdir(parents=True)
    plan_path = runtime / "sql_qdrant_projection_plan.json"
    output = runtime / "controlled_sql_qdrant_projection_acceptance.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    acceptance = module.accept_controlled_sql_qdrant_projection(
        projection_plan_path=plan_path,
        repo_root=repo,
        output_path=output,
    )

    assert acceptance["controlled_sql_qdrant_projection_accepted"] is True
    assert acceptance["sql_qdrant_projection_contract_accepted"] is True
    assert acceptance["bloc_f_complete"] is True
    assert acceptance["payload_contains_sql_ref"] is True
    assert acceptance["qdrant_payload"]["sql_ref"] == plan["source_baseline_ref"]
    assert acceptance["rehydration_required"] is True
    assert acceptance["sql_written_by_0212"] is False
    assert acceptance["qdrant_written_by_0212"] is False
    assert acceptance["new_sql_backend_added"] is False
    assert acceptance["new_qdrant_backend_added"] is False
    assert acceptance["runtime_history_rewritten_by_0212"] is False
    assert acceptance["next_recommended_patch"] == "0213-context_recall_integration_audit"
    assert output.exists()


def test_0212_rejects_unready_projection_plan(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_repo_surfaces(repo)
    plan = _plan_fixture(tmp_path, ready=False)
    runtime = Path(plan["target_runtime_root"])
    runtime.mkdir(parents=True)
    plan_path = runtime / "sql_qdrant_projection_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    acceptance = module.accept_controlled_sql_qdrant_projection(
        projection_plan_path=plan_path,
        repo_root=repo,
        output_path=runtime / "controlled_sql_qdrant_projection_acceptance.json",
    )

    assert acceptance["controlled_sql_qdrant_projection_accepted"] is False
    assert acceptance["bloc_f_complete"] is False
    assert "sql_qdrant_projection_plan_ready must be true" in acceptance["issues"]
    assert "p0212_may_execute_controlled_projection_acceptance must be true" in acceptance["issues"]
