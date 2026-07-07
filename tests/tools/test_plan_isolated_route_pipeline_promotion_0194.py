from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_isolated_route_pipeline_promotion.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("plan_isolated_route_pipeline_promotion_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _registry_entry() -> dict:
    return {
        "schema": "missipy.route_pipeline.isolated_baseline_registry_entry.v1",
        "accepted_baseline": "isolated-route-pipeline-write-read-v1",
        "baseline_ref": "baseline:isolated-route-pipeline-write-read-v1:0123456789abcdef",
        "entry_digest": "0123456789abcdef" * 4,
        "policy_decision_id": "policy:allow:github-artifact:0194",
        "runtime_root": "/tmp/runtime",
        "isolated_runtime_root": "/tmp/runtime/routeproxy-isolated",
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
        "safety_flags": {
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
        },
    }


def _write_registry(path: Path) -> Path:
    registry = path / "isolated_route_pipeline_baseline_registry.jsonl"
    registry.write_text(json.dumps(_registry_entry(), sort_keys=True) + "\n", encoding="utf-8")
    return registry


def test_0194_builds_promotion_plan_without_runtime_execution(tmp_path: Path) -> None:
    module = _load_tool_module()
    registry = _write_registry(tmp_path)

    plan = module.build_isolated_route_pipeline_promotion_plan(
        registry_path=registry,
        target_runtime_root=tmp_path / "dev-runtime",
        target_isolated_runtime_root=tmp_path / "dev-runtime" / "routeproxy-isolated",
        output_path=tmp_path / "isolated_route_pipeline_promotion_plan.json",
    )

    assert plan["promotion_ready"] is True
    assert plan["promotion_allowed_by_0194"] is False
    assert plan["selected_baseline_ref"].startswith("baseline:isolated-route-pipeline-write-read-v1")
    assert plan["issues"] == []
    assert plan["handler_called"] is False
    assert plan["frames_written"] is False
    assert plan["network_used"] is False
    assert len(plan["planned_steps"]) == 4
    assert (tmp_path / "isolated_route_pipeline_promotion_plan.json").exists()


def test_0194_rejects_relative_target_roots(tmp_path: Path) -> None:
    module = _load_tool_module()
    registry = _write_registry(tmp_path)

    plan = module.build_isolated_route_pipeline_promotion_plan(
        registry_path=registry,
        target_runtime_root=Path("relative-runtime"),
        target_isolated_runtime_root=Path("relative-runtime/routeproxy-isolated"),
    )

    assert plan["promotion_ready"] is False
    assert "target_runtime_root must be absolute" in plan["issues"]
    assert "target_isolated_runtime_root must be absolute" in plan["issues"]


def test_0194_cli_outputs_json(tmp_path: Path) -> None:
    registry = _write_registry(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--registry",
            str(registry),
            "--target-runtime-root",
            str(tmp_path / "dev-runtime"),
            "--target-isolated-runtime-root",
            str(tmp_path / "dev-runtime" / "routeproxy-isolated"),
            "--output",
            str(tmp_path / "isolated_route_pipeline_promotion_plan.json"),
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
    assert plan["schema"] == "missipy.route_pipeline.isolated_promotion_plan.v1"
    assert plan["promotion_ready"] is True
    assert plan["promotion_allowed_by_0194"] is False
    assert plan["handler_called"] is False
