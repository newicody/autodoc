from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "runtime" / "route_runtime_manager.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_RUNTIME_MANAGER_0103.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0103.md"
GRAPH = ROOT / "doc" / "docs" / "architecture" / "runtime" / "93_route_runtime_manager.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0103_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0103_route_runtime_manager_locks_simplified_boundary_language() -> None:
    text = _read(MODULE) + "\n" + _read(DOC) + "\n" + _read(PLAN)
    required = [
        "RouteRuntimeManager is not a scheduler-like coordinator",
        "No CLI",
        "No OpenRC service and no resident daemon",
        "No watcher",
        "No Scheduler.run() modification",
        "No global priority management",
        "No policy decision and no zone authority in ControlProxy",
        "No EventBus creation and no bus duplication",
        "Route mmap/eventfd is a data plane, not EventBus",
        "EventBus remains observation only",
        "Dispatcher remains EventType -> Handler only",
        "PolicyEngine remains minimal admission before queue",
        "Specialist branch owns business logic",
    ]
    for phrase in required:
        assert phrase in text


def test_0103_route_runtime_manager_does_not_import_kernel_or_bus() -> None:
    text = _read(MODULE)
    forbidden = [
        "kernel.scheduler",
        "kernel.dispatcher",
        "kernel.queue",
        "policy.engine",
        "EventBus(",
        "from kernel.event_bus",
        "import argparse",
        "subprocess",
        "openvino",
        "qdrant",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0103_route_runtime_manager_manifest_is_runtime_only() -> None:
    manifest = _read(MANIFEST)
    assert "src/runtime/route_runtime_manager.py" in manifest
    assert "tests/runtime/test_route_runtime_manager.py" in manifest
    assert "tests/rules/test_route_runtime_manager_0103_rule.py" in manifest
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/policy/engine.py",
    ]
    for path in forbidden:
        assert path not in manifest


def test_0103_route_runtime_manager_graph_is_root_attached_runtime_overlay() -> None:
    graph = _read(GRAPH)
    required = [
        "ROOT_GRAPH: doc/docs/architecture/00_global.dot",
        "Scheduler_run -> Dispatcher",
        "Dispatcher -> ControlProxyRouteHandler",
        "ControlProxyRouteHandler -> RouteRuntimeManager",
        "RouteRuntimeManager -> ControlFS",
        "RouteRuntimeManager -> RouteDataPlane",
        "RouteDataPlane [label=\"mmap/eventfd data plane\\nnot EventBus\"]",
        "EventBusObservation [label=\"existing EventBus\\nobservation only\"]",
    ]
    for phrase in required:
        assert phrase in graph
