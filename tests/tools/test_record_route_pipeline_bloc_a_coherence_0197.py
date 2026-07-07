from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "record_route_pipeline_bloc_a_coherence.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("record_route_pipeline_bloc_a_coherence_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _readiness_fixture(tmp_path: Path, *, accepted: bool = True) -> dict:
    return {
        "schema": "missipy.route_pipeline.isolated_promotion_readiness_acceptance.v1",
        "promotion_plan_audit_path": str(tmp_path / "isolated_route_pipeline_promotion_plan_audit.json"),
        "promotion_plan_audit_schema": "missipy.route_pipeline.isolated_promotion_plan_audit.v1",
        "selected_baseline_ref": "baseline:isolated-route-pipeline-write-read-v1:0123456789abcdef",
        "selected_entry_digest": "0123456789abcdef" * 4,
        "accepted_baseline": "isolated-route-pipeline-write-read-v1",
        "source_policy_decision_id": "policy:allow:github-artifact:0197",
        "source_runtime_root": str(tmp_path / "runtime"),
        "source_isolated_runtime_root": str(tmp_path / "runtime" / "routeproxy-isolated"),
        "target_runtime_root": str(tmp_path / "runtime" / "dev-controlled"),
        "target_isolated_runtime_root": str(tmp_path / "runtime" / "dev-controlled" / "routeproxy-isolated"),
        "promotion_target": "controlled-dev-routeproxy-smoke",
        "promotion_readiness_accepted": accepted,
        "controlled_dev_smoke_ready": accepted,
        "execution_allowed_by_0196": False,
        "next_required_patch": "0197-bloc_a_coherence_record",
        "phase_re_evaluation_required_before_execution": True,
        "issues": [] if accepted else ["promotion_readiness_accepted must be true"],
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


def test_0197_records_clean_bloc_a_coherence(tmp_path: Path) -> None:
    module = _load_tool_module()
    readiness_path = tmp_path / "isolated_route_pipeline_promotion_readiness_acceptance.json"
    output_path = tmp_path / "route_pipeline_bloc_a_coherence_record.json"
    readiness_path.write_text(json.dumps(_readiness_fixture(tmp_path), indent=2), encoding="utf-8")

    record = module.record_route_pipeline_bloc_a_coherence(
        readiness_acceptance_path=readiness_path,
        output_path=output_path,
    )

    assert record["bloc_a_coherence_accepted"] is True
    assert record["bloc_a_complete"] is True
    assert record["phase_re_evaluated"] is True
    assert record["next_bloc"] == "B"
    assert record["future_execution_can_be_unlocked"] is True
    assert record["execution_allowed_by_0197"] is False
    assert record["issues"] == []
    assert record["existing_surfaces_reused"] is True
    assert record["new_runtime_handler_added"] is False
    assert record["new_adapter_added"] is False
    assert record["handler_called"] is False
    assert record["frames_written"] is False
    assert record["scheduler_modified"] is False
    assert output_path.exists()


def test_0197_rejects_failed_readiness_acceptance(tmp_path: Path) -> None:
    module = _load_tool_module()
    readiness_path = tmp_path / "isolated_route_pipeline_promotion_readiness_acceptance.json"
    readiness_path.write_text(json.dumps(_readiness_fixture(tmp_path, accepted=False), indent=2), encoding="utf-8")

    record = module.record_route_pipeline_bloc_a_coherence(
        readiness_acceptance_path=readiness_path,
    )

    assert record["bloc_a_coherence_accepted"] is False
    assert record["bloc_a_complete"] is False
    assert "promotion_readiness_accepted must be true" in record["issues"]
    assert "controlled_dev_smoke_ready must be true" in record["issues"]


def test_0197_cli_outputs_json(tmp_path: Path) -> None:
    readiness_path = tmp_path / "isolated_route_pipeline_promotion_readiness_acceptance.json"
    output_path = tmp_path / "route_pipeline_bloc_a_coherence_record.json"
    readiness_path.write_text(json.dumps(_readiness_fixture(tmp_path), indent=2), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--readiness-acceptance",
            str(readiness_path),
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

    record = json.loads(completed.stdout)
    assert record["schema"] == "missipy.route_pipeline.bloc_a_coherence_record.v1"
    assert record["bloc_a_coherence_accepted"] is True
    assert record["next_bloc"] == "B"
    assert record["future_execution_can_be_unlocked"] is True
    assert record["execution_allowed_by_0197"] is False
    assert output_path.exists()
