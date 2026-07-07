from pathlib import Path
import importlib.util
import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_route_handler_surfaces.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("audit_route_handler_surfaces_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_surface(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_0181_audits_fake_handler_surfaces_without_importing_runtime(tmp_path: Path) -> None:
    module = _load_tool_module()

    _write_surface(
        tmp_path,
        "src/runtime/scheduler_route_adapter.py",
        (
            "SCHEDULER_ROUTE_REQUEST_SCHEMA = 'x'\n"
            "class SchedulerRouteRequest: pass\n"
            "def scheduler_route_request_mapping(): pass\n"
        ),
    )
    _write_surface(
        tmp_path,
        "src/runtime/scheduler_route_handler_minimal.py",
        (
            "class SchedulerRouteHandlerCommand: pass\n"
            "def handle_scheduler_route_request(): pass\n"
        ),
    )

    report = module.audit_route_handler_surfaces(
        tmp_path,
        expected_surfaces=(
            (
                "src/runtime/scheduler_route_adapter.py",
                (
                    "SCHEDULER_ROUTE_REQUEST_SCHEMA",
                    "SchedulerRouteRequest",
                    "scheduler_route_request_mapping",
                ),
            ),
            (
                "src/runtime/scheduler_route_handler_minimal.py",
                (
                    "SchedulerRouteHandlerCommand",
                    "handle_scheduler_route_request",
                ),
            ),
        ),
    )

    assert report.file_count == 2
    assert report.ready_count == 2
    assert report.runtime_imports_executed is False
    assert report.handler_called is False
    assert report.scheduler_modified is False
    assert report.frames_written is False


def test_0181_reports_missing_symbols_and_files(tmp_path: Path) -> None:
    module = _load_tool_module()
    _write_surface(
        tmp_path,
        "src/runtime/scheduler_route_adapter.py",
        "class SchedulerRouteRequest: pass\n",
    )

    report = module.audit_route_handler_surfaces(
        tmp_path,
        expected_surfaces=(
            (
                "src/runtime/scheduler_route_adapter.py",
                ("SchedulerRouteRequest", "scheduler_route_request_mapping"),
            ),
            ("src/runtime/missing.py", ("missing_symbol",)),
        ),
    )

    assert report.file_count == 2
    assert report.ready_count == 0
    assert report.missing_count == 1
    assert report.files[0].symbols_missing == ("scheduler_route_request_mapping",)
    assert report.files[1].exists is False


def test_0181_cli_outputs_json(tmp_path: Path) -> None:
    _write_surface(
        tmp_path,
        "src/runtime/scheduler_route_adapter.py",
        (
            "SCHEDULER_ROUTE_REQUEST_SCHEMA = 'x'\n"
            "class SchedulerRouteRequest: pass\n"
            "def scheduler_route_request_mapping(): pass\n"
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
    assert report["schema"] == "missipy.route_handler.surface_audit.v1"
    assert report["dry_run_only"] is True
    assert report["runtime_imports_executed"] is False
    assert report["handler_called"] is False
