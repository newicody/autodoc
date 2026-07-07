from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_provenance_repair.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("audit_provenance_repair_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _acceptance_fixture(tmp_path: Path, *, accepted: bool = True) -> dict:
    runtime = tmp_path / "runtime" / "dev-controlled"
    return {
        "schema": "missipy.controlproxy.routeproxy_coherence_acceptance.v1",
        "controlproxy_routeproxy_coherence_accepted": accepted,
        "stale_priority_zone_contract_accepted": accepted,
        "bloc_d_complete": accepted,
        "next_bloc": "E",
        "accepted_baseline": "controlproxy-routeproxy-stale-priority-zone-coherence-v1",
        "policy_decision_id": "policy:allow:stale-priority-zone:manual0206",
        "target_runtime_root": str(runtime),
        "target_isolated_runtime_root": str(runtime / "routeproxy-isolated"),
        "issues": [] if accepted else ["not accepted"],
        "warnings": ["source_baseline_ref or source_entry_digest missing from P0200 acceptance"],
        "existing_surfaces_reused": True,
        "frames_written_count": 1,
        "readback_count": 1,
        "provenance_repair_items": [
            "source_baseline_ref or source_entry_digest missing from P0200 acceptance; preserve this as a provenance repair item"
        ],
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "eventbus_instantiated": False,
        "network_used": False,
        "mark_route_frame_stale_called_by_0206": False,
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


def test_0207_audits_missing_source_provenance_without_repairing(tmp_path: Path) -> None:
    module = _load_tool_module()
    acceptance = _acceptance_fixture(tmp_path)
    runtime = Path(acceptance["target_runtime_root"])
    runtime.mkdir(parents=True)
    coherence = runtime / "controlproxy_routeproxy_coherence_acceptance.json"
    p0200 = runtime / "controlled_dev_routeproxy_smoke_post_execution_acceptance.json"
    registry = runtime / "controlled_dev_routeproxy_smoke_registry.jsonl"

    coherence.write_text(json.dumps(acceptance, indent=2), encoding="utf-8")
    p0200.write_text(
        json.dumps(
            {
                "schema": "missipy.route_pipeline.controlled_dev_post_execution_acceptance.v1",
                "source_baseline_ref": "",
                "source_entry_digest": "",
                "controlled_dev_baseline_ref": "baseline:controlled-dev-routeproxy-write-read-v1:abc",
                "accepted_baseline": "controlled-dev-routeproxy-write-read-v1",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    registry.write_text(
        json.dumps(
            {
                "schema": "missipy.route_pipeline.controlled_dev_registry_entry.v1",
                "entry_ref": "controlled-dev-registry:def",
                "entry_digest": "def",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    output = runtime / "provenance_repair_audit.json"

    audit = module.audit_provenance_repair(
        coherence_acceptance_path=coherence,
        output_path=output,
    )

    assert audit["provenance_repair_audit_success"] is True
    assert audit["provenance_repair_required"] is True
    assert audit["source_baseline_ref_missing"] is True
    assert audit["source_entry_digest_missing"] is True
    assert audit["provenance_repair_plan_allowed_next"] is True
    assert audit["execution_allowed_by_0207"] is False
    assert audit["sql_write_allowed_by_0207"] is False
    assert audit["qdrant_write_allowed_by_0207"] is False
    assert audit["runtime_history_rewrite_allowed_by_0207"] is False
    assert audit["planned_next_patch"] == "0208-provenance_repair_plan"
    assert audit["candidate_provenance_refs"]
    assert audit["sql_written_by_0207"] is False
    assert audit["qdrant_written_by_0207"] is False
    assert output.exists()


def test_0207_rejects_unaccepted_bloc_d(tmp_path: Path) -> None:
    module = _load_tool_module()
    acceptance = _acceptance_fixture(tmp_path, accepted=False)
    runtime = Path(acceptance["target_runtime_root"])
    runtime.mkdir(parents=True)
    coherence = runtime / "controlproxy_routeproxy_coherence_acceptance.json"
    coherence.write_text(json.dumps(acceptance, indent=2), encoding="utf-8")

    audit = module.audit_provenance_repair(coherence_acceptance_path=coherence)

    assert audit["provenance_repair_audit_success"] is False
    assert "controlproxy_routeproxy_coherence_accepted must be true" in audit["issues"]
    assert "stale_priority_zone_contract_accepted must be true" in audit["issues"]
