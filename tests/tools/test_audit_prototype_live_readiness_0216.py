from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_prototype_live_readiness.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("audit_prototype_live_readiness_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _surface(path: str, tokens: list[str]) -> dict:
    return {"path": path, "matched_tokens": tokens, "use_before_new_code": True}


def _acceptance_fixture(tmp_path: Path, *, accepted: bool = True) -> dict:
    runtime = tmp_path / "runtime" / "dev-controlled"
    sql_ref = "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5"
    return {
        "schema": "missipy.context_recall.controlled_integration_acceptance.v1",
        "controlled_context_recall_integration_accepted": accepted,
        "context_recall_integration_contract_accepted": accepted,
        "bloc_g_complete": accepted,
        "next_bloc": "H",
        "accepted_baseline": "controlled-context-recall-integration-contract-v1",
        "integration_digest": "db7ec32ee5de42c32850d77d4c2cffa42c8125f4354c3ca4397391ea619a1bd1",
        "projection_digest": "664d37d9325811349ade719e09a089df43759c439a2dc01b998e7c8365f5caca",
        "sql_ref": sql_ref,
        "qdrant_payload": {"sql_ref": sql_ref},
        "payload_contains_sql_ref": True,
        "rehydration_required": True,
        "target_runtime_root": str(runtime),
        "target_isolated_runtime_root": str(runtime / "routeproxy-isolated"),
        "issues": [] if accepted else ["not accepted"],
        "warnings": [],
        "existing_surfaces_reused": True,
        "selected_surfaces": {
            "context_query_surface": _surface("src/context/artifact_intake_contract.py", ["artifact", "query"]),
            "recall_surface": _surface("src/context/context_graph_export.py", ["Qdrant", "qdrant", "recall", "vector"]),
            "rehydrate_surface": _surface("tools/accept_controlled_sql_qdrant_projection.py", ["rehydrate", "sql_ref"]),
            "response_surface": _surface("src/context/github_project_push_frame.py", ["artifact", "response"]),
            "projection_surface": _surface("tools/accept_controlled_sql_qdrant_projection.py", ["controlled_sql_qdrant_projection_acceptance", "qdrant_payload", "sql_ref"]),
        },
        "live_qdrant_query_executed_by_0215": False,
        "qdrant_queried_by_0215": False,
        "sql_record_read_by_0215": False,
        "recall_executed_by_0215": False,
        "sql_write_allowed_by_0215": False,
        "qdrant_write_allowed_by_0215": False,
        "sql_written_by_0215": False,
        "qdrant_written_by_0215": False,
        "runtime_imports_executed_by_0215": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0215": False,
        "routeproxy_prepared_by_0215": False,
        "read_route_frame_called_by_0215": False,
        "writer_permits_requested_by_0215": False,
        "frames_written_by_0215": False,
        "controlproxy_frames_written_by_0215": False,
        "eventbus_instantiated_by_0215": False,
        "network_used_by_0215": False,
        "runtime_history_rewritten_by_0215": False,
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


def test_0216_audits_prototype_live_readiness_without_writes(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_repo_surfaces(repo)
    acceptance = _acceptance_fixture(tmp_path)
    runtime = Path(acceptance["target_runtime_root"])
    runtime.mkdir(parents=True)
    acceptance_path = runtime / "controlled_context_recall_integration_acceptance.json"
    output = runtime / "prototype_live_readiness_audit.json"
    acceptance_path.write_text(json.dumps(acceptance, indent=2), encoding="utf-8")

    audit = module.audit_prototype_live_readiness(
        context_recall_acceptance_path=acceptance_path,
        repo_root=repo,
        output_path=output,
        qdrant_url="http://127.0.0.1:6333",
        probe_local_qdrant=False,
    )

    assert audit["prototype_live_readiness_audit_success"] is True
    assert audit["prototype_live_execution_plan_allowed_next"] is True
    assert audit["planned_next_patch"] == "0217-prototype_live_execution_plan"
    assert audit["target_path"] == "context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact"
    assert audit["live_requirements"]["must_write_sql_by_p0218"] is True
    assert audit["live_requirements"]["must_upsert_qdrant_by_p0218"] is True
    assert audit["live_requirements"]["must_query_qdrant_by_p0218"] is True
    assert audit["live_requirements"]["must_read_sql_by_p0218"] is True
    assert audit["live_requirements"]["must_rehydrate_by_p0218"] is True
    assert audit["live_requirements"]["must_write_response_artifact_by_p0218"] is True
    assert audit["p0218_required_true_flags"] == [
        "sql_written_by_0218",
        "qdrant_written_by_0218",
        "qdrant_queried_by_0218",
        "sql_record_read_by_0218",
        "rehydration_executed_by_0218",
        "response_artifact_written_by_0218",
        "prototype_success",
    ]
    assert audit["qdrant_local_probe_executed_by_0216"] is False
    assert audit["sql_written_by_0216"] is False
    assert audit["qdrant_written_by_0216"] is False
    assert output.exists()


def test_0216_rejects_non_local_qdrant_url(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_repo_surfaces(repo)
    acceptance = _acceptance_fixture(tmp_path)
    runtime = Path(acceptance["target_runtime_root"])
    runtime.mkdir(parents=True)
    acceptance_path = runtime / "controlled_context_recall_integration_acceptance.json"
    acceptance_path.write_text(json.dumps(acceptance, indent=2), encoding="utf-8")

    audit = module.audit_prototype_live_readiness(
        context_recall_acceptance_path=acceptance_path,
        repo_root=repo,
        qdrant_url="https://example.com:6333",
        probe_local_qdrant=False,
    )

    assert audit["prototype_live_readiness_audit_success"] is False
    assert "qdrant_url must target localhost or 127.0.0.1 for controlled prototype" in audit["issues"]


def test_0216_rejects_unaccepted_context_recall_acceptance(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_repo_surfaces(repo)
    acceptance = _acceptance_fixture(tmp_path, accepted=False)
    runtime = Path(acceptance["target_runtime_root"])
    runtime.mkdir(parents=True)
    acceptance_path = runtime / "controlled_context_recall_integration_acceptance.json"
    acceptance_path.write_text(json.dumps(acceptance, indent=2), encoding="utf-8")

    audit = module.audit_prototype_live_readiness(
        context_recall_acceptance_path=acceptance_path,
        repo_root=repo,
    )

    assert audit["prototype_live_readiness_audit_success"] is False
    assert "controlled_context_recall_integration_accepted must be true" in audit["issues"]
    assert "context_recall_integration_contract_accepted must be true" in audit["issues"]
