from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_sql_qdrant_projection_readiness.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("audit_sql_qdrant_projection_readiness_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _acceptance_fixture(tmp_path: Path, *, accepted: bool = True) -> dict:
    runtime = tmp_path / "runtime" / "dev-controlled"
    return {
        "schema": "missipy.provenance.forward_only_repair_acceptance.v1",
        "forward_only_provenance_repair_accepted": accepted,
        "provenance_repair_accepted": accepted,
        "bloc_e_complete": accepted,
        "next_bloc": "F",
        "accepted_baseline": "forward-only-provenance-repair-v1",
        "source_baseline_ref": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5",
        "source_entry_digest": "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855",
        "repair_digest": "0123456789abcdef",
        "target_runtime_root": str(runtime),
        "target_isolated_runtime_root": str(runtime / "routeproxy-isolated"),
        "issues": [] if accepted else ["not accepted"],
        "warnings": [],
        "existing_surfaces_reused": True,
        "runtime_history_rewritten_by_0209": False,
        "source_artifact_rewritten_by_0209": False,
        "sql_write_allowed_by_0209": False,
        "qdrant_write_allowed_by_0209": False,
        "sql_written_by_0209": False,
        "qdrant_written_by_0209": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0209": False,
        "routeproxy_prepared_by_0209": False,
        "mark_route_frame_stale_called_by_0209": False,
        "read_route_frame_called_by_0209": False,
        "writer_permits_requested_by_0209": False,
        "frames_written_by_0209": False,
        "controlproxy_frames_written_by_0209": False,
        "eventbus_instantiated_by_0209": False,
        "network_used_by_0209": False,
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
    (repo / "src/runtime").mkdir(parents=True, exist_ok=True)
    (repo / "tools").mkdir(parents=True, exist_ok=True)
    (repo / "doc").mkdir(parents=True, exist_ok=True)
    (repo / "src/runtime/sql_context_store.py").write_text(
        "class DbApiSqlContextStore:\n    def get_record(self, sql_ref):\n        return sql_ref\nSQL = 'SQL'\nsqlite = 'sqlite'\n",
        encoding="utf-8",
    )
    (repo / "tools/qdrant_recall.py").write_text(
        "Qdrant = 'Qdrant'\nqdrant = 'qdrant'\ncollection = 'collection'\nvector = 'vector'\nsql_ref = 'sql_ref'\n"
        "def rehydrate(sql_ref):\n    return get_record(sql_ref)\n"
        "def get_record(sql_ref):\n    return sql_ref\n",
        encoding="utf-8",
    )
    (repo / "doc/provenance.md").write_text(
        "provenance_repair_acceptance source_baseline_ref source_entry_digest\n",
        encoding="utf-8",
    )


def test_0210_audits_sql_qdrant_projection_readiness(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_repo_surfaces(repo)
    acceptance = _acceptance_fixture(tmp_path)
    runtime = Path(acceptance["target_runtime_root"])
    runtime.mkdir(parents=True)
    acceptance_path = runtime / "provenance_repair_acceptance.json"
    output = runtime / "sql_qdrant_projection_readiness_audit.json"
    acceptance_path.write_text(json.dumps(acceptance, indent=2), encoding="utf-8")

    audit = module.audit_sql_qdrant_projection_readiness(
        provenance_repair_acceptance_path=acceptance_path,
        repo_root=repo,
        output_path=output,
    )

    assert audit["sql_qdrant_projection_readiness_audit_success"] is True
    assert audit["sql_qdrant_projection_plan_allowed_next"] is True
    assert audit["sql_surface_count"] >= 1
    assert audit["qdrant_surface_count"] >= 1
    assert audit["rehydrate_surface_count"] >= 1
    assert audit["provenance_surface_count"] >= 1
    assert audit["projection_contract"]["sql_role"] == "durable authority"
    assert audit["projection_contract"]["qdrant_role"] == "projection/search/recall only"
    assert audit["planned_next_patch"] == "0211-sql_qdrant_projection_plan"
    assert audit["sql_written_by_0210"] is False
    assert audit["qdrant_written_by_0210"] is False
    assert audit["runtime_imports_executed_by_0210"] is False
    assert output.exists()


def test_0210_rejects_unaccepted_provenance_repair(tmp_path: Path) -> None:
    module = _load_tool_module()
    repo = tmp_path / "repo"
    _write_repo_surfaces(repo)
    acceptance = _acceptance_fixture(tmp_path, accepted=False)
    runtime = Path(acceptance["target_runtime_root"])
    runtime.mkdir(parents=True)
    acceptance_path = runtime / "provenance_repair_acceptance.json"
    acceptance_path.write_text(json.dumps(acceptance, indent=2), encoding="utf-8")

    audit = module.audit_sql_qdrant_projection_readiness(
        provenance_repair_acceptance_path=acceptance_path,
        repo_root=repo,
    )

    assert audit["sql_qdrant_projection_readiness_audit_success"] is False
    assert "forward_only_provenance_repair_accepted must be true" in audit["issues"]
    assert "provenance_repair_accepted must be true" in audit["issues"]
