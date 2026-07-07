from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_isolated_handler_execution_plan.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("build_isolated_handler_execution_plan_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_smoke(root: Path, *, command_built: bool = True) -> Path:
    smoke = root / "scheduler_route_handler_command_smoke.jsonl"
    smoke.write_text(
        json.dumps(
            {
                "source_request_id": "request-1",
                "source_route_id": "route-1",
                "source_task_id": "task-1",
                "policy_decision_id": "policy:allow:test",
                "handler_surface": "handle_scheduler_route_command",
                "command_built": command_built,
                "ready_for_later_handler_call": command_built,
                "command_mapping": {
                    "schema": "missipy.scheduler.route_handler_command.v1",
                    "command_ref": "scheduler-command:task-1",
                    "handler_ref": "handler:scheduler-route-minimal",
                    "route_root_ref": "route:runtime/root",
                    "frame_requests": [],
                    "scheduler_run_modified": False,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return smoke


def test_0186_builds_isolated_execution_plan_without_handler_call(tmp_path: Path) -> None:
    module = _load_tool_module()
    _write(
        tmp_path,
        "src/runtime/route_proxy_runtime_minimal.py",
        (
            "from dataclasses import dataclass\n"
            "@dataclass(frozen=True)\n"
            "class RouteProxyRuntimePolicy:\n"
            "    runtime_root: str\n"
            "    create: bool = True\n"
            "def prepare_route_proxy_runtime(policy=None): pass\n"
            "def request_writer_permit(*args, **kwargs): pass\n"
            "def write_route_frame(*args, **kwargs): pass\n"
            "def read_route_frame(*args, **kwargs): pass\n"
        ),
    )
    smoke = _write_smoke(tmp_path)

    report = module.build_isolated_handler_execution_plan(
        smoke_path=smoke,
        repo_root=tmp_path,
        isolated_runtime_root=tmp_path / "runtime-isolated",
        output_path=tmp_path / "isolated_handler_execution_plan.jsonl",
    )

    assert report["item_count"] == 1
    assert report["ready_count"] == 1
    assert report["dry_run_only"] is True
    assert report["handler_called"] is False
    assert report["routeproxy_prepared"] is False
    assert report["frames_written"] is False
    assert report["route_proxy_runtime_surface"]["selected_policy_root_field"] == "runtime_root"
    item = report["items"][0]
    assert item["ready_for_later_isolated_handler_call"] is True
    assert item["runtime_policy_kwargs"] == {"runtime_root": str(tmp_path / "runtime-isolated")}
    assert (tmp_path / "isolated_handler_execution_plan.jsonl").exists()


def test_0186_blocks_when_policy_root_field_is_missing(tmp_path: Path) -> None:
    module = _load_tool_module()
    _write(
        tmp_path,
        "src/runtime/route_proxy_runtime_minimal.py",
        (
            "class RouteProxyRuntimePolicy:\n"
            "    pass\n"
            "def prepare_route_proxy_runtime(policy=None): pass\n"
        ),
    )
    smoke = _write_smoke(tmp_path)

    report = module.build_isolated_handler_execution_plan(
        smoke_path=smoke,
        repo_root=tmp_path,
        isolated_runtime_root=tmp_path / "runtime-isolated",
    )

    assert report["ready_count"] == 0
    assert "no isolated runtime root field found on RouteProxyRuntimePolicy" in report["items"][0]["issues"]


def test_0186_cli_outputs_json(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/runtime/route_proxy_runtime_minimal.py",
        (
            "class RouteProxyRuntimePolicy:\n"
            "    route_root: str\n"
            "def prepare_route_proxy_runtime(policy=None): pass\n"
        ),
    )
    smoke = _write_smoke(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--smoke",
            str(smoke),
            "--repo-root",
            str(tmp_path),
            "--isolated-runtime-root",
            str(tmp_path / "runtime-isolated"),
            "--output",
            str(tmp_path / "isolated_handler_execution_plan.jsonl"),
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
    assert report["schema"] == "missipy.route_handler.isolated_execution_plan.v1"
    assert report["dry_run_only"] is True
    assert report["handler_called"] is False
    assert report["routeproxy_prepared"] is False
    assert report["frames_written"] is False
