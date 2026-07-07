from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_context_recall_integration.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("audit_context_recall_integration_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _acceptance_fixture(tmp_path: Path, *, accepted: bool = True) -> dict:
    runtime = tmp_path / "runtime" / "dev-controlled"
    return {
        "schema": "missipy.sql_qdrant.controlled_projection_acceptance.v1",
        "controlled_sql_qdrant_projection_accepted": accepted,
        "sql_qdrant_projection_contract_accepted": accepted,
        "bloc_f_complete": accepted,
        "next_bloc": "G",
        "accepted_baseline": "controlled-sql-qdrant-projection-contract-v1",
        "projection_digest": "664d37d9325811349ade719e09a089df43759c439a2dc01b998e7c8365f5caca",
        "sql_ref": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5",
        "qdrant_payload": {
            "sql_ref": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5",
            "source_entry_digest": "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855",
            "repair_digest": "00750a169d8d765968a6aee28a5d26a9342aa53f2922bb3b865a13bf3a320b88",
        },
        "payload_contains_sql_ref": True,
        "rehydration_required": True,
        "source_entry_digest": "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855",
        "repair_digest": "00750a169d8d765968a6aee28a5d26a9342aa53f2922bb3b865a13bf3a320b88",
        "target_runtime_root": str(runtime),
        "target_isolated_runtime_root": str(runtime / "routeproxy-isolated"),
        "issues": [] if accepted else ["not accepted"],
        "warnings": [],
        "existing_surfaces_reused": True,
        "sql_write_allowed_by_0212": False,
        "qdrant_write_allowed_by_0212": False,
        "sql_written_by_0212": False,
        "qdrant_written_by_0212": False,
        "runtime_imports_executed_by_0212": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0212": False,
        "routeproxy_prepared_by_0212": False,
        "read_route_frame_called_by_0212": False,
        "writer_permits_requested_by_0212": False,
        "frames_written_by_0212": False,
        "controlproxy_frames_written_by_0212": False,
        "eventbus_instantiated_by_0212": False,
        "network_used_by_0212": False,
        "runtime_history_rewritten_by_0212": False,
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
    (repo / "doc").mkdir(parents=True)
    (repo / "src/context/context_recall_contract.py").write_text(
        "context = 'context'\nquery = 'query'\nartifact = 'artifact'\n"
        "Qdrant = 'Qdrant'\nrecall = 'recall'\nvector = 'vector'\ncollection = 'collection'\n"
        "sql_ref = 'sql_ref'\nrehydrate = 'rehydrate'\ndef get_record(sql_ref):\n    return sql_ref\n"
        "response = 'response'\nresult = 'result'\ndef to_mapping():\n    return {}\n",
        encoding="utf-8",
    )
    (repo / "tools/projection_acceptance.py").write_text(
        "controlled_sql_qdrant_projection_acceptance qdrant_payload sql_ref\n",
        encoding="utf-8",
    )
    (repo / "doc/context.md").write_text(
        "Context context query artifact response result recall rehydrate sql_ref\n",
        encoding="utf-8",
    )


def test_0213_audits_context_recall_integration_readiness(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_repo_surfaces(repo)
    acceptance = _acceptance_fixture(tmp_path)
    runtime = Path(acceptance["target_runtime_root"])
    runtime.mkdir(parents=True)
    acceptance_path = runtime / "controlled_sql_qdrant_projection_acceptance.json"
    output = runtime / "context_recall_integration_audit.json"
    acceptance_path.write_text(json.dumps(acceptance, indent=2), encoding="utf-8")

    audit = module.audit_context_recall_integration(
        projection_acceptance_path=acceptance_path,
        repo_root=repo,
        output_path=output,
    )

    assert audit["context_recall_integration_audit_success"] is True
    assert audit["context_recall_integration_plan_allowed_next"] is True
    assert audit["context_surface_count"] >= 1
    assert audit["recall_surface_count"] >= 1
    assert audit["rehydrate_surface_count"] >= 1
    assert audit["response_surface_count"] >= 1
    assert audit["projection_surface_count"] >= 1
    assert audit["target_path"] == "context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact"
    assert audit["planned_next_patch"] == "0214-context_recall_integration_plan"
    assert audit["recall_executed_by_0213"] is False
    assert audit["sql_record_read_by_0213"] is False
    assert audit["qdrant_queried_by_0213"] is False
    assert audit["sql_written_by_0213"] is False
    assert audit["qdrant_written_by_0213"] is False
    assert output.exists()


def test_0213_rejects_unaccepted_projection_acceptance(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_repo_surfaces(repo)
    acceptance = _acceptance_fixture(tmp_path, accepted=False)
    runtime = Path(acceptance["target_runtime_root"])
    runtime.mkdir(parents=True)
    acceptance_path = runtime / "controlled_sql_qdrant_projection_acceptance.json"
    acceptance_path.write_text(json.dumps(acceptance, indent=2), encoding="utf-8")

    audit = module.audit_context_recall_integration(
        projection_acceptance_path=acceptance_path,
        repo_root=repo,
    )

    assert audit["context_recall_integration_audit_success"] is False
    assert "controlled_sql_qdrant_projection_accepted must be true" in audit["issues"]
    assert "sql_qdrant_projection_contract_accepted must be true" in audit["issues"]
