from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "runtime" / "controlproxy_route_runtime_handler.py"
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_ROUTE_RUNTIME_HANDLER_0104.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0104.md"
GRAPH = ROOT / "doc" / "docs" / "architecture" / "runtime" / "94_controlproxy_route_runtime_handler.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0104_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0104_route_runtime_handler_locks_thin_handler_language() -> None:
    text = _read(MODULE) + "\n" + _read(DOC) + "\n" + _read(PLAN)
    required = [
        "Handler remains an adapter thin enough to call RouteRuntimeManager",
        "RouteRuntimeManager owns route runtime work",
        "Dispatcher remains EventType -> Handler only",
        "No Scheduler.run() modification",
        "No PriorityQueue, Dispatcher or PolicyEngine modification",
        "ControlProxy does not manage global priorities",
        "ControlProxy does not decide policy or zone authority",
        "No EventBus creation and no bus duplication",
        "Route mmap/eventfd is a data plane, not EventBus",
        "Specialist branch owns business logic",
        "Compatibility wrappers remain temporary adapters",
    ]
    for phrase in required:
        assert phrase in text


def test_0104_route_runtime_handler_does_not_import_kernel_or_bus() -> None:
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


def test_0104_route_runtime_handler_manifest_avoids_kernel_files() -> None:
    manifest = _read(MANIFEST)
    required = [
        "src/runtime/controlproxy_route_runtime_handler.py",
        "tests/runtime/test_controlproxy_route_runtime_handler.py",
        "tests/rules/test_controlproxy_route_runtime_handler_0104_rule.py",
    ]
    for path in required:
        assert path in manifest
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/policy/engine.py",
    ]
    for path in forbidden:
        assert path not in manifest


def test_0104_route_runtime_handler_graph_is_not_scheduler_bis() -> None:
    graph = _read(GRAPH)
    required = [
        "ROOT_GRAPH: doc/docs/architecture/00_global.dot",
        "SchedulerRun -> Dispatcher",
        "Dispatcher -> ThinHandler",
        "ThinHandler -> RuntimeBinding",
        "RuntimeBinding -> RouteRuntimeManager",
        "RouteRuntimeManager -> DataPlane",
        "DataPlane [label=\"mmap/eventfd data plane\\nnot EventBus\"]",
        "EventBusObservation [label=\"existing EventBus\\nobservation only\"]",
        "SpecialistBranch [label=\"specialist branch\\nbusiness logic\"]",
    ]
    for phrase in required:
        assert phrase in graph
