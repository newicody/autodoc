from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/runtime/route_bridge_boundary.py"
DOC = ROOT / "doc/architecture/ROUTE_BRIDGE_BOUNDARY_0112.md"
PLAN = ROOT / "doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0112.md"
DOT = ROOT / "doc/docs/architecture/runtime/102_route_bridge_boundary.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0112_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0112_bridge_boundary_locks_no_runtime_io_intent() -> None:
    text = _read(MODULE) + "\n" + _read(DOC) + "\n" + _read(PLAN)
    required = [
        "NetworkBridge/HardwareBridge are future adapters behind Handler -> RouteRuntimeManager",
        "does not bypass Scheduler, PolicyEngine, PriorityQueue, Dispatcher or Handler",
        "does not calculate priority and does not decide policy/zone",
        "Route mmap/eventfd remains the data plane, not EventBus",
        "EventBus remains observation only",
        "No ControlProxyBus",
        "No RouteBus",
        "No VisualizationBus",
        "No sockets opened",
        "No devices opened",
        "No CLI",
        "No OpenRC service and no resident daemon",
        "No watcher",
        "stdlib only",
    ]
    for phrase in required:
        assert phrase in text


def test_0112_graph_is_root_attached_not_parallel_runtime() -> None:
    dot = _read(DOT)
    required = [
        "ROOT_GRAPH: doc/docs/architecture/00_global.dot",
        "root-attached runtime overlay",
        "Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler",
        "Handler -> RouteRuntimeManager",
        "RouteRuntimeManager -> RouteBridgeBoundary",
        "future NetworkBridge",
        "future HardwareBridge",
        "no active I/O in 0112",
        "EventBus observation only",
    ]
    for phrase in required:
        assert phrase in dot


def test_0112_manifest_excludes_kernel_and_bus_code() -> None:
    manifest = _read(MANIFEST)
    assert "src/runtime/route_bridge_boundary.py" in manifest
    assert "tests/runtime/test_route_bridge_boundary.py" in manifest
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/kernel/event_bus.py",
        "src/policy/engine.py",
    ]
    for path in forbidden:
        assert path not in manifest


def test_0112_rule_has_no_active_transport_claim() -> None:
    text = _read(DOC) + "\n" + _read(PLAN)
    forbidden = [
        "opens sockets",
        "opens devices",
        "starts daemon",
        "starts watcher",
        "creates EventBus",
        "ControlProxyBus",
        "RouteBus",
        "VisualizationBus",
    ]
    for phrase in forbidden:
        assert phrase not in text.replace("No ControlProxyBus", "").replace("No RouteBus", "").replace("No VisualizationBus", "")
