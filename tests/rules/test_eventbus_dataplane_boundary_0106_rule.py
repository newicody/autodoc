from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "EVENTBUS_DATAPLANE_BOUNDARY_0106.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0106.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "96_eventbus_dataplane_boundary.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0106_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0106_boundary_docs_exist() -> None:
    assert DOC.exists()
    assert PLAN.exists()
    assert DOT.exists()
    assert MANIFEST.exists()


def test_0106_locks_eventbus_as_observation_only() -> None:
    text = _read(DOC) + "\n" + _read(PLAN) + "\n" + _read(DOT)
    required = [
        "EventBus = observation only",
        "Route mmap/eventfd = data plane, not EventBus",
        "RouteMessageJournal = drained route message journal, not EventBus",
        "Visualization adapter = existing EventBus/context reader, not bus owner",
        "Scheduler.emit() -> PolicyEngine.decide() -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler",
    ]
    for phrase in required:
        assert phrase in text


def test_0106_rejects_second_bus_concepts() -> None:
    text = _read(DOC) + "\n" + _read(PLAN) + "\n" + _read(MANIFEST)
    required = [
        "No ControlProxyBus",
        "No RouteBus",
        "No VisualizationBus",
        "No bus created by ControlProxy",
        "No bus created by RouteRuntimeManager",
        "No bus owned by visualization adapters",
        "No mmap/eventfd command bus",
        "No EventBus as command path",
    ]
    for phrase in required:
        assert phrase in text


def test_0106_keeps_scheduler_dispatcher_and_priority_roles_small() -> None:
    text = _read(DOC) + "\n" + _read(PLAN) + "\n" + _read(MANIFEST)
    required = [
        "PolicyEngine = minimal admission before queue",
        "PriorityQueue = deterministic execution order",
        "Dispatcher = EventType -> Handler only",
        "No Dispatcher business logic",
        "No ControlProxy global priority management",
        "No PolicyEngine expansion into business logic",
    ]
    for phrase in required:
        assert phrase in text


def test_0106_graph_shows_observation_and_dataplane_as_separate_paths() -> None:
    dot = _read(DOT)
    required = [
        "cluster_kernel_command_path",
        "cluster_runtime_dataplane",
        "cluster_observation",
        "cluster_context_projection",
        "EventBus\\nobservation only",
        "mmap fixed-slot route",
        "eventfd / pipe notifier",
        "forbidden: command",
        "forbidden: bus",
    ]
    for phrase in required:
        assert phrase in dot


def test_0106_no_runtime_or_kernel_files_added_to_manifest() -> None:
    manifest = _read(MANIFEST)
    forbidden_paths = [
        "src/kernel/",
        "src/policy/",
        "src/runtime/",
        "tests/runtime/",
    ]
    for path in forbidden_paths:
        assert path not in manifest
