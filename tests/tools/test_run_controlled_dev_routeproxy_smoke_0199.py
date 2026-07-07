from pathlib import Path
import importlib.util
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_controlled_dev_routeproxy_smoke.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("run_controlled_dev_routeproxy_smoke_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _plan_fixture(tmp_path: Path, *, ready: bool = True) -> dict:
    runtime = tmp_path / "runtime" / "dev-controlled"
    return {
        "schema": "missipy.route_pipeline.controlled_dev_routeproxy_smoke_plan.v1",
        "bloc": "B",
        "bloc_name": "controlled-dev-smoke",
        "bloc_patch_limit": 3,
        "target_runtime_root": str(runtime),
        "target_isolated_runtime_root": str(runtime / "routeproxy-isolated"),
        "policy_decision_id": "policy:allow:controlled-dev:manual0199",
        "plan_ready": ready,
        "execution_allowed_by_0198": False,
        "execution_can_be_unlocked_by_p0199": ready,
        "execution_unlock_planned_for": "0199-controlled_dev_routeproxy_smoke_execution",
        "execution_tool_to_reuse": "tools/run_isolated_route_pipeline_smoke.py",
        "issues": [] if ready else ["plan_ready must be true"],
        "warnings": [],
        "existing_surfaces_reused": True,
    }


class _Completed:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.stdout = '{"pipeline_success": true}'
        self.stderr = ""


def test_0199_runs_existing_pipeline_tool_from_clean_plan(tmp_path: Path, monkeypatch) -> None:
    module = _load_tool_module()
    runtime = tmp_path / "runtime" / "dev-controlled"
    runtime.mkdir(parents=True)
    plan_path = tmp_path / "controlled_dev_routeproxy_smoke_plan.json"
    context_bus = tmp_path / "context.bus.jsonl"
    output_path = runtime / "controlled_dev_routeproxy_smoke_execution.json"
    plan_path.write_text(json.dumps(_plan_fixture(tmp_path), indent=2), encoding="utf-8")
    context_bus.write_text("{}", encoding="utf-8")

    captured = {}

    def fake_run(command, cwd, text, stdout, stderr, check):
        captured["command"] = command
        pipeline_output = Path(command[command.index("--output") + 1])
        pipeline_output.parent.mkdir(parents=True, exist_ok=True)
        pipeline_output.write_text(
            json.dumps(
                {
                    "pipeline_success": True,
                    "queued_count": 1,
                    "policy_scoped_queued_count": 1,
                    "command_plan_ready_count": 1,
                    "command_built_count": 1,
                    "handler_executed_count": 1,
                    "frames_written_count": 1,
                    "readback_count": 1,
                    "controlproxy_frames_written": False,
                    "scheduler_modified": False,
                    "eventbus_instantiated": False,
                    "network_used": False,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return _Completed()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    report = module.run_controlled_dev_routeproxy_smoke(
        controlled_dev_plan_path=plan_path,
        context_bus_path=context_bus,
        output_path=output_path,
        repo_root=ROOT,
    )

    assert report["execution_success"] is True
    assert report["execution_unlocked_by_p0199"] is True
    assert report["execution_allowed_by_0199"] is True
    assert report["execution_tool_reused"] == "tools/run_isolated_route_pipeline_smoke.py"
    assert "tools/run_isolated_route_pipeline_smoke.py" in captured["command"][1]
    assert report["frames_written_count"] == 1
    assert report["readback_count"] == 1
    assert report["handler_called"] is True
    assert report["frames_written"] is True
    assert report["controlproxy_frames_written"] is False
    assert report["scheduler_modified"] is False
    assert report["network_used"] is False
    assert report["requires_p0200_post_execution_audit"] is True
    assert output_path.exists()


def test_0199_rejects_unready_plan_without_subprocess(tmp_path: Path, monkeypatch) -> None:
    module = _load_tool_module()
    runtime = tmp_path / "runtime" / "dev-controlled"
    runtime.mkdir(parents=True)
    plan_path = tmp_path / "controlled_dev_routeproxy_smoke_plan.json"
    context_bus = tmp_path / "context.bus.jsonl"
    plan_path.write_text(json.dumps(_plan_fixture(tmp_path, ready=False), indent=2), encoding="utf-8")
    context_bus.write_text("{}", encoding="utf-8")

    called = {"value": False}

    def fake_run(*args, **kwargs):
        called["value"] = True
        return _Completed()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    report = module.run_controlled_dev_routeproxy_smoke(
        controlled_dev_plan_path=plan_path,
        context_bus_path=context_bus,
        repo_root=ROOT,
    )

    assert report["execution_success"] is False
    assert called["value"] is False
    assert "plan_ready must be true" in report["issues"]
    assert "execution_can_be_unlocked_by_p0199 must be true" in report["issues"]
