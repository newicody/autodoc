from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "register_isolated_route_pipeline_baseline.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("register_isolated_route_pipeline_baseline_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _acceptance_fixture(*, accepted: bool = True) -> dict:
    return {
        "schema": "missipy.route_pipeline.isolated_acceptance.v1",
        "acceptance_approved": accepted,
        "accepted_baseline": "isolated-route-pipeline-write-read-v1" if accepted else None,
        "pipeline_report_path": "/tmp/runtime/isolated_route_pipeline_smoke.json",
        "pipeline_schema": "missipy.route_pipeline.isolated_smoke.v1",
        "policy_decision_id": "policy:allow:github-artifact:0193",
        "runtime_root": "/tmp/runtime",
        "isolated_runtime_root": "/tmp/runtime/routeproxy-isolated",
        "issues": [],
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


def test_0193_registers_accepted_baseline(tmp_path: Path) -> None:
    module = _load_tool_module()
    acceptance = tmp_path / "isolated_route_pipeline_acceptance.json"
    registry = tmp_path / "isolated_route_pipeline_baseline_registry.jsonl"
    acceptance.write_text(json.dumps(_acceptance_fixture(), indent=2), encoding="utf-8")

    report = module.register_isolated_route_pipeline_baseline(
        acceptance_path=acceptance,
        output_path=registry,
    )

    assert report["registry_success"] is True
    assert report["registered_count"] == 1
    assert report["accepted_baseline"] == "isolated-route-pipeline-write-read-v1"
    assert report["baseline_ref"].startswith("baseline:isolated-route-pipeline-write-read-v1:")
    assert report["issues"] == []
    line = registry.read_text(encoding="utf-8").strip()
    entry = json.loads(line)
    assert entry["schema"] == "missipy.route_pipeline.isolated_baseline_registry_entry.v1"
    assert entry["entry_digest"] == report["entry_digest"]
    assert entry["safety_flags"]["handler_called"] is False


def test_0193_rejects_unaccepted_baseline_without_writing(tmp_path: Path) -> None:
    module = _load_tool_module()
    acceptance = tmp_path / "isolated_route_pipeline_acceptance.json"
    registry = tmp_path / "isolated_route_pipeline_baseline_registry.jsonl"
    acceptance.write_text(json.dumps(_acceptance_fixture(accepted=False), indent=2), encoding="utf-8")

    report = module.register_isolated_route_pipeline_baseline(
        acceptance_path=acceptance,
        output_path=registry,
    )

    assert report["registry_success"] is False
    assert report["registered_count"] == 0
    assert "acceptance_approved must be true" in report["issues"]
    assert not registry.exists()


def test_0193_cli_outputs_json(tmp_path: Path) -> None:
    acceptance = tmp_path / "isolated_route_pipeline_acceptance.json"
    registry = tmp_path / "isolated_route_pipeline_baseline_registry.jsonl"
    acceptance.write_text(json.dumps(_acceptance_fixture(), indent=2), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--acceptance",
            str(acceptance),
            "--output",
            str(registry),
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
    assert report["schema"] == "missipy.route_pipeline.isolated_baseline_registry.v1"
    assert report["registry_success"] is True
    assert report["registered_count"] == 1
    assert registry.exists()
