from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_GRAPH_ROOT_ALIGNMENT_0107.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0107.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "97_controlproxy_root_alignment.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0107_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0107_graph_root_alignment_files_exist() -> None:
    for path in (DOC, PLAN, DOT, MANIFEST):
        assert path.exists(), path


def test_0107_graph_is_root_attached_not_isolated() -> None:
    text = _read(DOC) + "\n" + _read(PLAN) + "\n" + _read(DOT)
    required = [
        "ROOT_GRAPH: doc/docs/architecture/00_global.dot",
        "root-attached runtime overlay",
        "not an isolated graph",
        "Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler",
        "0101 -> 0102 -> 0103 -> 0104 -> 0105 -> 0106 -> 0107",
    ]
    for phrase in required:
        assert phrase in text


def test_0107_locks_microkernel_responsibilities() -> None:
    text = _read(DOC) + "\n" + _read(PLAN) + "\n" + _read(DOT)
    required = [
        "PolicyEngine = minimal admission before queue",
        "PriorityQueue = deterministic execution order",
        "Dispatcher = EventType -> Handler only",
        "Handler = thin adapter",
        "Specialist branch owns business logic",
        "RouteRuntimeManager = runtime data-plane boundary",
        "ControlProxy does not manage global priorities",
        "EventBus = observation only",
        "Route mmap/eventfd = data plane, not EventBus",
    ]
    for phrase in required:
        assert phrase in text


def test_0107_rejects_second_bus_and_scheduler_like_controlproxy() -> None:
    text = _read(DOC) + "\n" + _read(PLAN) + "\n" + _read(DOT)
    required = [
        "No ControlProxyBus",
        "No RouteBus",
        "No VisualizationBus",
        "No scheduler-like ControlProxy coordinator",
        "No Dispatcher business logic",
        "No PolicyEngine business logic",
        "No EventBus command path",
    ]
    for phrase in required:
        assert phrase in text


def test_0107_manifest_stays_documentation_only() -> None:
    manifest = _read(MANIFEST)
    assert "doc/docs/architecture/runtime/97_controlproxy_root_alignment.dot" in manifest
    assert "tests/rules/test_controlproxy_graph_root_alignment_0107_rule.py" in manifest
    for forbidden in (
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/policy/engine.py",
        "src/kernel/event_bus.py",
        "src/runtime/route_runtime_manager.py",
    ):
        assert forbidden not in manifest
