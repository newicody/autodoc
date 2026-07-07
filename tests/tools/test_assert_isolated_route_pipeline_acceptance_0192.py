from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "assert_isolated_route_pipeline_acceptance.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("assert_isolated_route_pipeline_acceptance_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _audit_fixture(*, success: bool = True) -> dict:
    issues = [] if success else ["pipeline_success must be true"]
    return {
        "schema": "missipy.route_pipeline.isolated_artifact_audit.v1",
        "audit_success": success,
        "pipeline_success": success,
        "pipeline_report_path": "/tmp/runtime/isolated_route_pipeline_smoke.json",
        "pipeline_schema": "missipy.route_pipeline.isolated_smoke.v1",
        "policy_decision_id": "policy:allow:github-artifact:0192",
        "runtime_root": "/tmp/runtime",
        "isolated_runtime_root": "/tmp/runtime/routeproxy-isolated",
        "issues": issues,
        "warnings": [],
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
        "top_level_counts": {
            "queued_count": 4,
            "policy_scoped_queued_count": 1,
            "command_plan_ready_count": 1,
            "command_built_count": 1,
            "handler_executed_count": 1,
            "frames_written_count": 1,
            "readback_count": 1,
        },
        "artifact_counts": {
            "queue_items": 4,
            "policy_scoped_queue_items": 1,
            "command_plan_items": 1,
            "command_smoke_items": 1,
            "isolated_plan_items": 1,
            "handler_smoke_items": 1,
            "readback_items": 1,
        },
    }


def test_0192_accepts_clean_0191_audit(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "isolated_route_pipeline_artifact_audit.json"
    audit_path.write_text(json.dumps(_audit_fixture(), indent=2), encoding="utf-8")

    verdict = module.assert_isolated_route_pipeline_acceptance(
        audit_path=audit_path,
        output_path=tmp_path / "isolated_route_pipeline_acceptance.json",
    )

    assert verdict["acceptance_approved"] is True
    assert verdict["accepted_baseline"] == "isolated-route-pipeline-write-read-v1"
    assert verdict["issues"] == []
    assert verdict["handler_called"] is False
    assert verdict["frames_written"] is False
    assert verdict["network_used"] is False
    assert (tmp_path / "isolated_route_pipeline_acceptance.json").exists()


def test_0192_rejects_failed_audit(tmp_path: Path) -> None:
    module = _load_tool_module()
    audit_path = tmp_path / "isolated_route_pipeline_artifact_audit.json"
    audit_path.write_text(json.dumps(_audit_fixture(success=False), indent=2), encoding="utf-8")

    verdict = module.assert_isolated_route_pipeline_acceptance(audit_path=audit_path)

    assert verdict["acceptance_approved"] is False
    assert verdict["accepted_baseline"] is None
    assert "audit_success must be true" in verdict["issues"]
    assert "pipeline_success must be true" in verdict["issues"]


def test_0192_cli_outputs_json_and_zero_for_clean_audit(tmp_path: Path) -> None:
    audit_path = tmp_path / "isolated_route_pipeline_artifact_audit.json"
    audit_path.write_text(json.dumps(_audit_fixture(), indent=2), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--audit",
            str(audit_path),
            "--output",
            str(tmp_path / "isolated_route_pipeline_acceptance.json"),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    verdict = json.loads(completed.stdout)
    assert verdict["schema"] == "missipy.route_pipeline.isolated_acceptance.v1"
    assert verdict["acceptance_approved"] is True
    assert verdict["handler_called"] is False
    assert verdict["frames_written"] is False
