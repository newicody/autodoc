from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "write_forward_only_provenance_repair_acceptance.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("write_forward_only_provenance_repair_acceptance_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _plan_fixture(tmp_path: Path, *, ready: bool = True) -> dict:
    runtime = tmp_path / "runtime" / "dev-controlled"
    return {
        "schema": "missipy.provenance.repair_plan.v1",
        "bloc": "E",
        "target_runtime_root": str(runtime),
        "target_isolated_runtime_root": str(runtime / "routeproxy-isolated"),
        "provenance_repair_plan_ready": ready,
        "repair_strategy": "forward_only_artifact",
        "planned_output": "provenance_repair_acceptance.json",
        "planned_next_patch": "0209-forward_only_provenance_repair_acceptance",
        "p0209_may_write_forward_only_provenance_repair": ready,
        "issues": [] if ready else ["provenance_repair_plan_ready must be true"],
        "warnings": [],
        "planned_source_baseline_ref": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5",
        "planned_source_baseline_ref_source": {
            "artifact": "controlled_dev_routeproxy_smoke_post_execution_acceptance.json",
            "field": "controlled_dev_baseline_ref",
        },
        "planned_source_entry_digest": "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855",
        "planned_source_entry_digest_source": {
            "artifact": "controlled_dev_routeproxy_smoke_registry.jsonl",
            "field": "entry_digest",
        },
        "planned_registry_entry_ref": "controlled-dev-registry:bfe63428faeea56a",
        "runtime_history_rewrite_allowed_by_0208": False,
        "execution_allowed_by_0208": False,
        "sql_write_allowed_by_0208": False,
        "qdrant_write_allowed_by_0208": False,
        "provenance_repair_write_allowed_by_0208": False,
        "runtime_imports_executed_by_0208": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0208": False,
        "routeproxy_prepared_by_0208": False,
        "mark_route_frame_stale_called_by_0208": False,
        "read_route_frame_called_by_0208": False,
        "writer_permits_requested_by_0208": False,
        "frames_written_by_0208": False,
        "controlproxy_frames_written_by_0208": False,
        "eventbus_instantiated_by_0208": False,
        "network_used_by_0208": False,
        "sql_written_by_0208": False,
        "qdrant_written_by_0208": False,
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


def _write_runtime_sources(runtime: Path) -> None:
    runtime.mkdir(parents=True)
    (runtime / "controlled_dev_routeproxy_smoke_post_execution_acceptance.json").write_text(
        json.dumps(
            {
                "schema": "missipy.route_pipeline.controlled_dev_post_execution_acceptance.v1",
                "controlled_dev_baseline_ref": "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5",
                "accepted_baseline": "controlled-dev-routeproxy-write-read-v1",
                "source_baseline_ref": "",
                "source_entry_digest": "",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (runtime / "controlled_dev_routeproxy_smoke_registry.jsonl").write_text(
        json.dumps(
            {
                "schema": "missipy.route_pipeline.controlled_dev_registry_entry.v1",
                "entry_ref": "controlled-dev-registry:bfe63428faeea56a",
                "entry_digest": "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_0209_writes_forward_only_provenance_repair_acceptance(tmp_path: Path) -> None:
    module = _load_tool_module()
    plan = _plan_fixture(tmp_path)
    runtime = Path(plan["target_runtime_root"])
    _write_runtime_sources(runtime)
    plan_path = tmp_path / "provenance_repair_plan.json"
    output = runtime / "provenance_repair_acceptance.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    acceptance = module.write_forward_only_provenance_repair_acceptance(
        provenance_repair_plan_path=plan_path,
        output_path=output,
    )

    assert acceptance["forward_only_provenance_repair_accepted"] is True
    assert acceptance["provenance_repair_accepted"] is True
    assert acceptance["bloc_e_complete"] is True
    assert acceptance["source_baseline_ref"] == "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5"
    assert acceptance["source_entry_digest"] == "bfe63428faeea56a7fc90c18e692356f1f1aec60c8d24dd27a62f95edaff3855"
    assert acceptance["registry_entry_ref"] == "controlled-dev-registry:bfe63428faeea56a"
    assert acceptance["repair_digest"]
    assert acceptance["runtime_history_rewritten_by_0209"] is False
    assert acceptance["source_artifact_rewritten_by_0209"] is False
    assert acceptance["sql_written_by_0209"] is False
    assert acceptance["qdrant_written_by_0209"] is False
    assert acceptance["controlproxy_frames_written_by_0209"] is False
    assert acceptance["next_recommended_patch"] == "0210-sql_qdrant_projection_readiness_audit"
    assert output.exists()


def test_0209_rejects_unready_plan_without_repair_acceptance(tmp_path: Path) -> None:
    module = _load_tool_module()
    plan = _plan_fixture(tmp_path, ready=False)
    runtime = Path(plan["target_runtime_root"])
    _write_runtime_sources(runtime)
    plan_path = tmp_path / "provenance_repair_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    acceptance = module.write_forward_only_provenance_repair_acceptance(
        provenance_repair_plan_path=plan_path,
        output_path=runtime / "provenance_repair_acceptance.json",
    )

    assert acceptance["forward_only_provenance_repair_accepted"] is False
    assert acceptance["bloc_e_complete"] is False
    assert "provenance_repair_plan_ready must be true" in acceptance["issues"]
    assert "p0209_may_write_forward_only_provenance_repair must be true" in acceptance["issues"]
