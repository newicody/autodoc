from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_provenance_repair.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("plan_provenance_repair_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _audit_fixture(tmp_path: Path, *, success: bool = True) -> dict:
    return {
        "schema": "missipy.provenance.repair_audit.v1",
        "bloc": "E",
        "bloc_name": "sql-qdrant-provenance-repair",
        "target_runtime_root": str(tmp_path / "runtime" / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "runtime" / "dev-controlled" / "routeproxy-isolated"),
        "provenance_repair_audit_success": success,
        "provenance_repair_required": True,
        "source_baseline_ref_missing": True,
        "source_entry_digest_missing": True,
        "provenance_repair_plan_allowed_next": success,
        "planned_next_patch": "0208-provenance_repair_plan",
        "issues": [] if success else ["provenance_repair_audit_success must be true"],
        "warnings": ["source_baseline_ref or source_entry_digest missing"],
        "repair_items": [
            "repair source_baseline_ref in a forward-only provenance repair artifact",
            "repair source_entry_digest in a forward-only provenance repair artifact",
        ],
        "candidate_provenance_refs": [
            {
                "artifact": "controlled_dev_routeproxy_smoke_post_execution_acceptance.json",
                "field": "controlled_dev_baseline_ref",
                "value": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5",
            },
            {
                "artifact": "controlled_dev_routeproxy_smoke_registry.jsonl",
                "field": "entry_ref",
                "value": "controlled-dev-registry:bfe63428faeea56a",
            },
            {
                "artifact": "controlled_dev_routeproxy_smoke_registry.jsonl",
                "field": "entry_digest",
                "value": "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855",
            },
        ],
        "execution_allowed_by_0207": False,
        "sql_write_allowed_by_0207": False,
        "qdrant_write_allowed_by_0207": False,
        "runtime_history_rewrite_allowed_by_0207": False,
        "runtime_imports_executed_by_0207": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0207": False,
        "routeproxy_prepared_by_0207": False,
        "mark_route_frame_stale_called_by_0207": False,
        "read_route_frame_called_by_0207": False,
        "writer_permits_requested_by_0207": False,
        "frames_written_by_0207": False,
        "controlproxy_frames_written_by_0207": False,
        "eventbus_instantiated_by_0207": False,
        "network_used_by_0207": False,
        "sql_written_by_0207": False,
        "qdrant_written_by_0207": False,
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


def test_0208_plans_forward_only_provenance_repair(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "provenance_repair_audit.json"
    output = tmp_path / "provenance_repair_plan.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path), indent=2), encoding="utf-8")

    plan = module.plan_forward_only_provenance_repair(
        provenance_repair_audit_path=audit_path,
        output_path=output,
    )

    assert plan["provenance_repair_plan_ready"] is True
    assert plan["repair_strategy"] == "forward_only_artifact"
    assert plan["planned_source_baseline_ref"] == "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5"
    assert plan["planned_source_entry_digest"] == "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855"
    assert plan["planned_registry_entry_ref"] == "controlled-dev-registry:bfe63428faeea56a"
    assert plan["runtime_history_rewrite_allowed_by_0208"] is False
    assert plan["sql_write_allowed_by_0208"] is False
    assert plan["qdrant_write_allowed_by_0208"] is False
    assert plan["provenance_repair_write_allowed_by_0208"] is False
    assert plan["p0209_may_write_forward_only_provenance_repair"] is True
    assert plan["planned_next_patch"] == "0209-forward_only_provenance_repair_acceptance"
    assert plan["sql_written_by_0208"] is False
    assert plan["qdrant_written_by_0208"] is False
    assert output.exists()


def test_0208_rejects_failed_audit(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "provenance_repair_audit.json"
    audit_path.write_text(json.dumps(_audit_fixture(tmp_path, success=False), indent=2), encoding="utf-8")

    plan = module.plan_forward_only_provenance_repair(provenance_repair_audit_path=audit_path)

    assert plan["provenance_repair_plan_ready"] is False
    assert plan["p0209_may_write_forward_only_provenance_repair"] is False
    assert "provenance_repair_audit_success must be true" in plan["issues"]
    assert "provenance_repair_plan_allowed_next must be true" in plan["issues"]
