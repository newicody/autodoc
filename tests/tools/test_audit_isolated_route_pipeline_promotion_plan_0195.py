from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_isolated_route_pipeline_promotion_plan.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("audit_isolated_route_pipeline_promotion_plan_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _promotion_plan_fixture(tmp_path: Path, *, ready: bool = True) -> dict:
    return {
        "schema": "missipy.route_pipeline.isolated_promotion_plan.v1",
        "registry_path": str(tmp_path / "isolated_route_pipeline_baseline_registry.jsonl"),
        "selected_baseline_ref": "baseline:isolated-route-pipeline-write-read-v1:0123456789abcdef",
        "selected_entry_digest": "0123456789abcdef" * 4,
        "accepted_baseline": "isolated-route-pipeline-write-read-v1",
        "source_policy_decision_id": "policy:allow:github-artifact:0195",
        "source_runtime_root": str(tmp_path / "source-runtime"),
        "source_isolated_runtime_root": str(tmp_path / "source-runtime" / "routeproxy-isolated"),
        "target_runtime_root": str(tmp_path / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "dev-controlled" / "routeproxy-isolated"),
        "promotion_target": "controlled-dev-routeproxy-smoke",
        "promotion_allowed_by_0194": False,
        "promotion_ready": ready,
        "issues": [],
        "warnings": [],
        "required_preconditions": [
            "Use an explicit new policy_decision_id for the controlled dev smoke.",
            "Use a fresh scheduler.route_requests.policy_scoped.jsonl for the target run.",
            "Keep scheduler.route_requests.jsonl append-only.",
            "Run the 0189 pipeline only against target_runtime_root and target_isolated_runtime_root.",
            "Run 0191 artifact audit after the controlled dev smoke.",
            "Run 0192 acceptance gate after audit.",
            "Do not promote to production route roots from 0194.",
        ],
        "planned_steps": [
            {
                "step": "dev-smoke-run",
                "tool": "tools/run_isolated_route_pipeline_smoke.py",
                "runtime_writes_allowed": True,
                "routeproxy_frames_allowed": "target_isolated_runtime_root only",
                "scheduler_run_modified": False,
                "controlproxy_frames_written": False,
            },
            {
                "step": "artifact-audit",
                "tool": "tools/audit_isolated_route_pipeline_artifacts.py",
                "runtime_writes_allowed": False,
                "routeproxy_frames_allowed": False,
                "scheduler_run_modified": False,
                "controlproxy_frames_written": False,
            },
            {
                "step": "acceptance-gate",
                "tool": "tools/assert_isolated_route_pipeline_acceptance.py",
                "runtime_writes_allowed": False,
                "routeproxy_frames_allowed": False,
                "scheduler_run_modified": False,
                "controlproxy_frames_written": False,
            },
            {
                "step": "baseline-registry",
                "tool": "tools/register_isolated_route_pipeline_baseline.py",
                "runtime_writes_allowed": False,
                "routeproxy_frames_allowed": False,
                "scheduler_run_modified": False,
                "controlproxy_frames_written": False,
            },
        ],
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


def test_0195_audits_clean_promotion_plan(tmp_path: Path) -> None:
    module = _load_tool_module()
    plan = tmp_path / "isolated_route_pipeline_promotion_plan.json"
    audit = tmp_path / "isolated_route_pipeline_promotion_plan_audit.json"
    plan.write_text(json.dumps(_promotion_plan_fixture(tmp_path), indent=2), encoding="utf-8")

    report = module.audit_isolated_route_pipeline_promotion_plan(
        promotion_plan_path=plan,
        output_path=audit,
    )

    assert report["audit_success"] is True
    assert report["issues"] == []
    assert report["promotion_ready"] is True
    assert report["promotion_allowed_by_0194"] is False
    assert report["existing_surfaces_reused"] is True
    assert report["new_runtime_handler_added"] is False
    assert report["new_adapter_added"] is False
    assert report["handler_called"] is False
    assert report["frames_written"] is False
    assert report["scheduler_modified"] is False
    assert report["network_used"] is False
    assert audit.exists()


def test_0195_rejects_promotion_execution_permission(tmp_path: Path) -> None:
    module = _load_tool_module()
    fixture = _promotion_plan_fixture(tmp_path)
    fixture["promotion_allowed_by_0194"] = True
    plan = tmp_path / "isolated_route_pipeline_promotion_plan.json"
    plan.write_text(json.dumps(fixture, indent=2), encoding="utf-8")

    report = module.audit_isolated_route_pipeline_promotion_plan(promotion_plan_path=plan)

    assert report["audit_success"] is False
    assert "promotion_allowed_by_0194 must remain false" in report["issues"]


def test_0195_cli_outputs_json(tmp_path: Path) -> None:
    plan = tmp_path / "isolated_route_pipeline_promotion_plan.json"
    audit = tmp_path / "isolated_route_pipeline_promotion_plan_audit.json"
    plan.write_text(json.dumps(_promotion_plan_fixture(tmp_path), indent=2), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--promotion-plan",
            str(plan),
            "--output",
            str(audit),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    report = json.loads(completed.stdout)
    assert report["schema"] == "missipy.route_pipeline.isolated_promotion_plan_audit.v1"
    assert report["audit_success"] is True
    assert report["promotion_ready"] is True
    assert report["handler_called"] is False
    assert report["frames_written"] is False
