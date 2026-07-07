from pathlib import Path
import importlib.util
import json
import subprocess
import sys

from context.github_artifact_dataset_bus_observation import append_github_artifact_dataset_bus_observation


ROOT = Path(__file__).resolve().parents[2]
PIPELINE_TOOL = ROOT / "tools" / "run_isolated_route_pipeline_smoke.py"
TOOL = ROOT / "tools" / "audit_isolated_route_pipeline_artifacts.py"


def _load_tool_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_context_bus(root: Path) -> Path:
    append_github_artifact_dataset_bus_observation(
        runtime_root=root,
        raw={
            "report_ref": "report:github-artifact:0191",
            "repository": "newicody/autodoc-ideas",
            "run_id": "run0191",
            "artifact_id": "artifact0191",
            "status": "queued",
            "dataset_root_ref": "server-dataset:github-artifacts",
            "raw_count": 1,
            "queued_count": 1,
            "failed_count": 0,
            "occurred_at": "2026-07-07T00:00:00Z",
        },
    )
    return root / "context.bus.jsonl"


def _write_pipeline_report(root: Path) -> Path:
    pipeline = _load_tool_module(PIPELINE_TOOL, "run_isolated_route_pipeline_smoke_tool_0191")
    context_bus = _write_context_bus(root)
    report_path = root / "isolated_route_pipeline_smoke.json"
    pipeline.run_isolated_route_pipeline_smoke(
        context_bus_path=context_bus,
        runtime_root=root,
        policy_decision_id="policy:allow:github-artifact:0191",
        isolated_runtime_root=root / "routeproxy-isolated",
        output_path=report_path,
    )
    return report_path


def test_0191_audits_successful_policy_scoped_pipeline_artifacts(tmp_path: Path) -> None:
    module = _load_tool_module(TOOL, "audit_isolated_route_pipeline_artifacts_tool")
    report_path = _write_pipeline_report(tmp_path / "runtime")

    audit = module.audit_isolated_route_pipeline_artifacts(
        pipeline_report_path=report_path,
        output_path=tmp_path / "runtime" / "isolated_route_pipeline_artifact_audit.json",
    )

    assert audit["audit_success"] is True
    assert audit["issues"] == []
    assert audit["pipeline_success"] is True
    assert audit["artifact_counts"]["policy_scoped_queue_items"] == 1
    assert audit["artifact_counts"]["handler_smoke_items"] == 1
    assert audit["artifact_counts"]["readback_items"] == 1
    assert audit["handler_called"] is False
    assert audit["frames_written"] is False
    assert audit["scheduler_modified"] is False
    assert audit["network_used"] is False
    assert (tmp_path / "runtime" / "isolated_route_pipeline_artifact_audit.json").exists()


def test_0191_detects_unscoped_0184_queue_path(tmp_path: Path) -> None:
    module = _load_tool_module(TOOL, "audit_isolated_route_pipeline_artifacts_tool_unscoped")
    report_path = _write_pipeline_report(tmp_path / "runtime")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["stage_reports"]["0184_route_request_to_command_plan"]["queue_path"] = report["artifacts"]["queue"]
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    audit = module.audit_isolated_route_pipeline_artifacts(pipeline_report_path=report_path)

    assert audit["audit_success"] is False
    assert "0184 must read policy_scoped_queue" in audit["issues"]


def test_0191_cli_outputs_json(tmp_path: Path) -> None:
    report_path = _write_pipeline_report(tmp_path / "runtime")
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--pipeline-report",
            str(report_path),
            "--output",
            str(tmp_path / "runtime" / "isolated_route_pipeline_artifact_audit.json"),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    audit = json.loads(completed.stdout)
    assert audit["schema"] == "missipy.route_pipeline.isolated_artifact_audit.v1"
    assert audit["audit_success"] is True
    assert audit["handler_called"] is False
    assert audit["frames_written"] is False
    assert audit["network_used"] is False
