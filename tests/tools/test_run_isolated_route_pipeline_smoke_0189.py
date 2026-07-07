from pathlib import Path
import importlib.util
import json
import subprocess
import sys

from context.github_artifact_dataset_bus_observation import append_github_artifact_dataset_bus_observation


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_isolated_route_pipeline_smoke.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("run_isolated_route_pipeline_smoke_tool", TOOL)
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
            "report_ref": "report:github-artifact:0189",
            "repository": "newicody/autodoc-ideas",
            "run_id": "run0189",
            "artifact_id": "artifact0189",
            "status": "queued",
            "dataset_root_ref": "server-dataset:github-artifacts",
            "raw_count": 1,
            "queued_count": 1,
            "failed_count": 0,
            "occurred_at": "2026-07-07T00:00:00Z",
        },
    )
    return root / "context.bus.jsonl"


def test_0189_runs_isolated_pipeline_end_to_end(tmp_path: Path) -> None:
    module = _load_tool_module()
    context_bus = _write_context_bus(tmp_path / "runtime")

    report = module.run_isolated_route_pipeline_smoke(
        context_bus_path=context_bus,
        runtime_root=tmp_path / "runtime",
        policy_decision_id="policy:allow:github-artifact:0189",
        isolated_runtime_root=tmp_path / "runtime" / "routeproxy-isolated",
        output_path=tmp_path / "runtime" / "isolated_route_pipeline_smoke.json",
    )

    assert report["pipeline_success"] is True
    assert report["queued_count"] == 1
    assert report["command_built_count"] == 1
    assert report["handler_executed_count"] == 1
    assert report["frames_written_count"] == 1
    assert report["readback_count"] == 1
    assert report["scheduler_modified"] is False
    assert report["eventbus_instantiated"] is False
    assert report["controlproxy_frames_written"] is False
    assert report["network_used"] is False
    for artifact in report["artifacts"].values():
        assert Path(artifact).exists()
    assert (tmp_path / "runtime" / "isolated_route_pipeline_smoke.json").exists()


def test_0189_requires_absolute_isolated_runtime_root(tmp_path: Path) -> None:
    module = _load_tool_module()
    context_bus = _write_context_bus(tmp_path / "runtime")

    try:
        module.run_isolated_route_pipeline_smoke(
            context_bus_path=context_bus,
            runtime_root=tmp_path / "runtime",
            policy_decision_id="policy:allow:github-artifact:0189",
            isolated_runtime_root=Path("relative-root"),
        )
    except module.IsolatedRoutePipelineSmokeError as exc:
        assert "isolated_runtime_root must be absolute" in str(exc)
    else:
        raise AssertionError("expected absolute isolated runtime root error")


def test_0189_cli_outputs_json(tmp_path: Path) -> None:
    context_bus = _write_context_bus(tmp_path / "runtime")
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--context-bus",
            str(context_bus),
            "--runtime-root",
            str(tmp_path / "runtime"),
            "--policy-decision-id",
            "policy:allow:github-artifact:0189-cli",
            "--isolated-runtime-root",
            str(tmp_path / "runtime" / "routeproxy-isolated"),
            "--output",
            str(tmp_path / "runtime" / "isolated_route_pipeline_smoke.json"),
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
    assert report["schema"] == "missipy.route_pipeline.isolated_smoke.v1"
    assert report["pipeline_success"] is True
    assert report["readback_count"] == 1
    assert report["network_used"] is False
