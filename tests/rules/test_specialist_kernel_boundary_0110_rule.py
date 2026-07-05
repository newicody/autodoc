from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "runtime" / "specialist_kernel_boundary.py"
DOC = ROOT / "doc" / "architecture" / "SPECIALIST_KERNEL_BOUNDARY_0110.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0110.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "100_specialist_kernel_boundary.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0110_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0110_specialist_boundary_locks_kernel_path() -> None:
    text = _read(MODULE) + "\n" + _read(DOC) + "\n" + _read(PLAN) + "\n" + _read(DOT)
    required = [
        "Specialist branch owns business logic",
        "SpecialistKernelCommand -> Scheduler.emit()",
        "PolicyEngine.decide()",
        "PriorityQueue",
        "Scheduler.run()",
        "Dispatcher",
        "Handler",
        "Handler -> RouteRuntimeManager",
        "RouteRuntimeManager owns route runtime work",
        "No direct Specialist -> RouteRuntimeManager call",
        "No Scheduler.run() modification",
        "Dispatcher = EventType -> Handler only",
        "PolicyEngine = minimal admission before queue",
        "EventBus = observation only",
        "Route mmap/eventfd = data plane, not EventBus",
        "No ControlProxyBus",
        "No RouteBus",
        "No VisualizationBus",
    ]
    for phrase in required:
        assert phrase in text


def test_0110_specialist_boundary_does_not_modify_kernel_files() -> None:
    manifest = _read(MANIFEST)
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/kernel/event_bus.py",
        "src/policy/engine.py",
    ]
    for path in forbidden:
        assert path not in manifest


def test_0110_specialist_boundary_is_not_a_bus_or_scheduler() -> None:
    text = _read(MODULE)
    forbidden = [
        "class ControlProxyBus",
        "class RouteBus",
        "class VisualizationBus",
        "class Scheduler",
        "def run(",
        "def dispatch(",
        "EventBus(",
        "RouteRuntimeManager(",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0110_code_rule_report_is_present() -> None:
    text = _read(DOC)
    required = [
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "external_dependencies_added: false",
    ]
    for phrase in required:
        assert phrase in text
