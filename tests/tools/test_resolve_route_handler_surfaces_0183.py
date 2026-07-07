from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "resolve_route_handler_surfaces.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("resolve_route_handler_surfaces_tool", TOOL)
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


def test_0183_resolves_command_handler_as_real_surface(tmp_path: Path) -> None:
    module = _load_tool_module()
    _write(
        tmp_path,
        "src/runtime/scheduler_route_handler_minimal.py",
        (
            "class SchedulerRouteHandlerCommand: pass\n"
            "def handle_scheduler_route_command(command, *, runtime_state=None): pass\n"
            "class SchedulerRouteHandlerReadbackResult: pass\n"
            "def handle_scheduler_route_command_with_readback(command, *, runtime_state=None): pass\n"
            "class SchedulerRouteFrameRequest: pass\n"
            "def build_single_frame_route_command(*, route_ref, owner_ref): pass\n"
        ),
    )
    _write(
        tmp_path,
        "src/runtime/scheduler_route_adapter.py",
        (
            "class SchedulerRouteRequest: pass\n"
            "def handle_scheduler_route_request(*, controlfs_root, runtime_root, request): pass\n"
            "def scheduler_route_request_mapping(): pass\n"
        ),
    )

    report = module.resolve_route_handler_surfaces(tmp_path)

    by_ref = {surface["surface_ref"]: surface for surface in report["surfaces"]}
    assert by_ref["minimal-command-handler"]["available"] is True
    assert by_ref["minimal-command-handler"]["symbol_details"]["handle_scheduler_route_command"]["signature"]["positional"] == ["command"]
    assert by_ref["scheduler-adapter-request"]["available"] is True
    assert report["recommended_next_surface"]["surface_ref"] == "minimal-command-handler"
    assert report["dry_run_only"] is True
    assert report["handler_called"] is False
    assert report["frames_written"] is False


def test_0183_reports_missing_surfaces_without_failure(tmp_path: Path) -> None:
    module = _load_tool_module()
    report = module.resolve_route_handler_surfaces(tmp_path)
    assert report["surface_count"] >= 4
    assert report["available_count"] == 0
    assert report["missing_count"] == report["surface_count"]
    assert report["recommended_next_surface"] is None


def test_0183_cli_outputs_json(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/runtime/scheduler_route_handler_minimal.py",
        (
            "class SchedulerRouteHandlerCommand: pass\n"
            "def handle_scheduler_route_command(command, *, runtime_state=None): pass\n"
        ),
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--repo-root",
            str(tmp_path),
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
    assert report["schema"] == "missipy.route_handler.surface_resolver.v1"
    assert report["dry_run_only"] is True
    assert report["runtime_imports_executed"] is False
    assert report["handler_called"] is False
