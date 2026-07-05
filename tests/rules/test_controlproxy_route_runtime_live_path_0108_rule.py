from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_ROUTE_RUNTIME_LIVE_PATH_0108.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0108.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "98_controlproxy_route_runtime_live_path.dot"
TEST = ROOT / "tests" / "runtime" / "test_controlproxy_route_runtime_live_path.py"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0108_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0108_TEST_REPORT.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0108_live_path_files_are_present() -> None:
    for path in (DOC, PLAN, DOT, TEST, MANIFEST, REPORT):
        assert path.exists(), path


def test_0108_locks_live_path_scope_and_boundaries() -> None:
    text = "\n".join(_read(path) for path in (DOC, PLAN, DOT, TEST, REPORT))
    required = [
        "walking skeleton",
        "Handler -> RouteRuntimeManager",
        "ControlFS + mmap/eventfd data plane",
        "EventBus = observation only",
        "Route mmap/eventfd = data plane, not EventBus",
        "No ControlProxyBus",
        "No RouteBus",
        "No VisualizationBus",
        "No Scheduler.run() modification",
        "Dispatcher = EventType -> Handler only",
        "PolicyEngine = minimal admission before queue",
        "PriorityQueue = deterministic execution order",
        "Specialist branch owns business logic",
        "live_path_status: green",
    ]
    for phrase in required:
        assert phrase in text


def test_0108_manifest_is_runtime_slice_not_kernel_loop_change() -> None:
    manifest = _read(MANIFEST)
    assert "tests/runtime/test_controlproxy_route_runtime_live_path.py" in manifest
    assert "doc/docs/architecture/runtime/98_controlproxy_route_runtime_live_path.dot" in manifest
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/policy/engine.py",
        "src/kernel/event_bus.py",
    ]
    for path in forbidden:
        assert path not in manifest


def test_0108_does_not_introduce_new_runtime_orchestration_module() -> None:
    manifest = _read(MANIFEST)
    forbidden = [
        "src/runtime/controlproxy_route_coordinator.py",
        "src/runtime/controlproxy_bus.py",
        "src/runtime/route_bus.py",
        "src/runtime/visualization_bus.py",
    ]
    for path in forbidden:
        assert path not in manifest
