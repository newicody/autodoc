from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "doc" / "architecture" / "CONTROLPROXY_MICROKERNEL_DIRECTION_AUDIT_0100.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0100.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "91_controlproxy_microkernel_direction.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0100_CHANGED_FILES.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing expected file: {path}"
    return path.read_text(encoding="utf-8")


def test_0100_records_parallel_lane_issue_without_claiming_deviation() -> None:
    text = _read(AUDIT) + "\n" + _read(PLAN)
    required = [
        "The repository has not fully deviated",
        "two parallel ControlProxy lanes",
        "legacy active-route lane",
        "newer generation lane",
        "not yet unified",
        "ControlProxyRouteCoordinator",
        "planned, not current",
    ]
    for phrase in required:
        assert phrase in text


def test_0100_preserves_microkernel_authority_and_loop_boundary() -> None:
    text = _read(AUDIT) + "\n" + _read(DOT) + "\n" + _read(MANIFEST)
    required = [
        "Scheduler.emit()",
        "PolicyEngine.decide()",
        "PriorityQueue",
        "Scheduler.run()",
        "Dispatcher.dispatch()",
        "Handler",
        "Scheduler.run()\\nunchanged",
        "not a second scheduler",
        "not policy authority",
        "No Scheduler.run() modification",
    ]
    for phrase in required:
        assert phrase in text


def test_0100_graph_shows_controlproxy_under_handler_boundary() -> None:
    dot = _read(DOT)
    required = [
        "cluster_microkernel",
        "cluster_handler_boundary",
        "cluster_legacy_lane",
        "cluster_generation_lane",
        "cluster_unification",
        "Dispatcher -> RouteHandler",
        "RouteHandler -> DispatchFilter",
        "DispatchFilter -> SchedulerAdapter",
        "DispatchFilter -> Coordinator [style=dashed, label=\"next integration\"]",
        "Coordinator -> GenerationTable [style=dashed, label=\"create first/next generation\"]",
    ]
    for phrase in required:
        assert phrase in dot


def test_0100_keeps_bus_observation_only() -> None:
    text = _read(AUDIT) + "\n" + _read(DOT) + "\n" + _read(MANIFEST)
    required = [
        "event.bus\\nfacts only",
        "existing-bus visualization adapter",
        "read tap only",
        "facts, not commands",
        "No event.bus command path",
        "No context.bus command path",
    ]
    for phrase in required:
        assert phrase in text
