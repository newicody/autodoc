from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "accept_isolated_route_pipeline_promotion_readiness.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("accept_isolated_route_pipeline_promotion_readiness_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _promotion_plan_audit_fixture(tmp_path: Path, *, audit_success: bool = True) -> dict:
    return {
        "schema": "missipy.route_pipeline.isolated_promotion_plan_audit.v1",
        "promotion_plan_path": str(tmp_path / "isolated_route_pipeline_promotion_plan.json"),
        "promotion_plan_schema": "missipy.route_pipeline.isolated_promotion_plan.v1",
        "selected_baseline_ref": "baseline:isolated-route-pipeline-write-read-v1:0123456789abcdef",
        "selected_entry_digest": "0123456789abcdef" * 4,
        "accepted_baseline": "isolated-route-pipeline-write-read-v1",
        "source_policy_decision_id": "policy:allow:github-artifact:0196",
        "source_runtime_root": str(tmp_path / "source-runtime"),
        "source_isolated_runtime_root": str(tmp_path / "source-runtime" / "routeproxy-isolated"),
        "target_runtime_root": str(tmp_path / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "dev-controlled" / "routeproxy-isolated"),
        "promotion_target": "controlled-dev-routeproxy-smoke",
        "promotion_ready": audit_success,
        "promotion_allowed_by_0194": False,
        "planned_step_count": 4,
        "required_precondition_count": 7,
        "issues": [] if audit_success else ["promotion_ready must be true"],
        "warnings": [],
        "audit_success": audit_success,
        "existing_surfaces_reused": True,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
        "runtime_imports_executed": False,
        "handler_called": False,
        "routeproxy_prepared": False,
        "read_route_frame_called": False,
        "writer_permits_requested": False,
        "frames_written": False,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "eventbus_instantiated": False,
        "network_used": False,
    }


def test_0196_accepts_clean_promotion_plan_audit(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "isolated_route_pipeline_promotion_plan_audit.json"
    output_path = tmp_path / "isolated_route_pipeline_promotion_readiness_acceptance.json"
    audit_path.write_text(json.dumps(_promotion_plan_audit_fixture(tmp_path), indent=2), encoding="utf-8")

    acceptance = module.accept_isolated_route_pipeline_promotion_readiness(
        promotion_plan_audit_path=audit_path,
        output_path=output_path,
    )

    assert acceptance["promotion_readiness_accepted"] is True
    assert acceptance["controlled_dev_smoke_ready"] is True
    assert acceptance["execution_allowed_by_0196"] is False
    assert acceptance["next_required_patch"] == "0197-bloc_a_coherence_record"
    assert acceptance["issues"] == []
    assert acceptance["existing_surfaces_reused"] is True
    assert acceptance["new_runtime_handler_added"] is False
    assert acceptance["new_adapter_added"] is False
    assert acceptance["handler_called"] is False
    assert acceptance["frames_written"] is False
    assert acceptance["scheduler_modified"] is False
    assert acceptance["network_used"] is False
    assert output_path.exists()


def test_0196_rejects_failed_promotion_plan_audit(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "isolated_route_pipeline_promotion_plan_audit.json"
    audit_path.write_text(
        json.dumps(_promotion_plan_audit_fixture(tmp_path, audit_success=False), indent=2),
        encoding="utf-8",
    )

    acceptance = module.accept_isolated_route_pipeline_promotion_readiness(
        promotion_plan_audit_path=audit_path,
    )

    assert acceptance["promotion_readiness_accepted"] is False
    assert acceptance["controlled_dev_smoke_ready"] is False
    assert "audit_success must be true" in acceptance["issues"]
    assert "promotion_ready must be true" in acceptance["issues"]


def test_0196_cli_outputs_json(tmp_path: Path) -> None:
    audit_path = tmp_path / "isolated_route_pipeline_promotion_plan_audit.json"
    output_path = tmp_path / "isolated_route_pipeline_promotion_readiness_acceptance.json"
    audit_path.write_text(json.dumps(_promotion_plan_audit_fixture(tmp_path), indent=2), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--promotion-plan-audit",
            str(audit_path),
            "--output",
            str(output_path),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    acceptance = json.loads(completed.stdout)
    assert acceptance["schema"] == "missipy.route_pipeline.isolated_promotion_readiness_acceptance.v1"
    assert acceptance["promotion_readiness_accepted"] is True
    assert acceptance["execution_allowed_by_0196"] is False
    assert acceptance["handler_called"] is False
    assert output_path.exists()
