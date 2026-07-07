from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_controlled_dev_routeproxy_smoke.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("plan_controlled_dev_routeproxy_smoke_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _bloc_a_coherence_fixture(tmp_path: Path, *, accepted: bool = True) -> dict:
    return {
        "schema": "missipy.route_pipeline.bloc_a_coherence_record.v1",
        "bloc": "A",
        "bloc_name": "isolated-prototype-stabilization",
        "bloc_patch_limit": 3,
        "bloc_patches": [
            "0195-isolated_route_pipeline_promotion_plan_audit",
            "0196-isolated_route_pipeline_promotion_readiness_acceptance",
            "0197-bloc_a_coherence_record",
        ],
        "readiness_acceptance_path": str(tmp_path / "isolated_route_pipeline_promotion_readiness_acceptance.json"),
        "readiness_acceptance_schema": "missipy.route_pipeline.isolated_promotion_readiness_acceptance.v1",
        "selected_baseline_ref": "baseline:isolated-route-pipeline-write-read-v1:0123456789abcdef",
        "selected_entry_digest": "0123456789abcdef" * 4,
        "accepted_baseline": "isolated-route-pipeline-write-read-v1",
        "source_policy_decision_id": "policy:allow:github-artifact:0197",
        "source_runtime_root": str(tmp_path / "runtime"),
        "source_isolated_runtime_root": str(tmp_path / "runtime" / "routeproxy-isolated"),
        "target_runtime_root": str(tmp_path / "runtime" / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "runtime" / "dev-controlled" / "routeproxy-isolated"),
        "promotion_target": "controlled-dev-routeproxy-smoke",
        "bloc_a_coherence_accepted": accepted,
        "bloc_a_complete": accepted,
        "phase_re_evaluated": True,
        "plan_adjustment_required": False,
        "rules_adjustment_required": False,
        "next_bloc": "B",
        "next_bloc_name": "controlled-dev-smoke",
        "next_recommended_patch": "0198-controlled_dev_smoke_plan",
        "execution_allowed_by_0197": False,
        "future_execution_can_be_unlocked": True,
        "issues": [] if accepted else ["bloc_a_complete must be true"],
        "warnings": [],
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


def test_0198_plans_controlled_dev_smoke_from_clean_bloc_a(tmp_path: Path) -> None:
    module = _load_tool_module()
    coherence_path = tmp_path / "route_pipeline_bloc_a_coherence_record.json"
    output_path = tmp_path / "controlled_dev_routeproxy_smoke_plan.json"
    coherence_path.write_text(json.dumps(_bloc_a_coherence_fixture(tmp_path), indent=2), encoding="utf-8")

    plan = module.plan_controlled_dev_routeproxy_smoke(
        bloc_a_coherence_path=coherence_path,
        policy_decision_id="policy:allow:controlled-dev:manual0199",
        output_path=output_path,
    )

    assert plan["plan_ready"] is True
    assert plan["bloc"] == "B"
    assert plan["execution_allowed_by_0198"] is False
    assert plan["execution_can_be_unlocked_by_p0199"] is True
    assert plan["execution_unlock_planned_for"] == "0199-controlled_dev_routeproxy_smoke_execution"
    assert plan["execution_tool_to_reuse"] == "tools/run_isolated_route_pipeline_smoke.py"
    assert plan["issues"] == []
    assert plan["existing_surfaces_reused"] is True
    assert plan["new_runtime_handler_added"] is False
    assert plan["new_adapter_added"] is False
    assert plan["handler_called"] is False
    assert plan["frames_written"] is False
    assert plan["scheduler_modified"] is False
    assert output_path.exists()


def test_0198_rejects_incomplete_bloc_a(tmp_path: Path) -> None:
    module = _load_tool_module()
    coherence_path = tmp_path / "route_pipeline_bloc_a_coherence_record.json"
    coherence_path.write_text(json.dumps(_bloc_a_coherence_fixture(tmp_path, accepted=False), indent=2), encoding="utf-8")

    plan = module.plan_controlled_dev_routeproxy_smoke(
        bloc_a_coherence_path=coherence_path,
        policy_decision_id="policy:allow:controlled-dev:manual0199",
    )

    assert plan["plan_ready"] is False
    assert plan["execution_can_be_unlocked_by_p0199"] is False
    assert "bloc_a_coherence_accepted must be true" in plan["issues"]
    assert "bloc_a_complete must be true" in plan["issues"]


def test_0198_cli_outputs_json(tmp_path: Path) -> None:
    coherence_path = tmp_path / "route_pipeline_bloc_a_coherence_record.json"
    output_path = tmp_path / "controlled_dev_routeproxy_smoke_plan.json"
    coherence_path.write_text(json.dumps(_bloc_a_coherence_fixture(tmp_path), indent=2), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--bloc-a-coherence",
            str(coherence_path),
            "--policy-decision-id",
            "policy:allow:controlled-dev:manual0199",
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

    plan = json.loads(completed.stdout)
    assert plan["schema"] == "missipy.route_pipeline.controlled_dev_routeproxy_smoke_plan.v1"
    assert plan["plan_ready"] is True
    assert plan["execution_can_be_unlocked_by_p0199"] is True
    assert plan["execution_allowed_by_0198"] is False
    assert output_path.exists()
