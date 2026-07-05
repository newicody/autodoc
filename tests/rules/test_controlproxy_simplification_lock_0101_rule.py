from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_SIMPLIFICATION_LOCK_0101.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0101.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "91_controlproxy_simplification_lock.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0101_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0101_TEST_REPORT.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0101_locks_simplified_responsibilities() -> None:
    text = _read(DOC) + "\n" + _read(PLAN) + "\n" + _read(DOT)
    required = [
        "Scheduler = loop, time, queue, and priority orchestration.",
        "PolicyEngine = minimal admission gate before the queue.",
        "PriorityQueue = the only deterministic execution ordering mechanism.",
        "Dispatcher = EventType -> Handler only.",
        "Handler = thin adapter from kernel event/request to capability boundary.",
        "Specialist branch = business logic, reasoning, transformation, strategy.",
        "ControlProxy / RouteRuntimeManager = runtime transport for route/mmap/controlfs.",
        "EventBus = observation only.",
        "Route mmap/eventfd = data plane, not EventBus.",
        "Qdrant = projection/search, not context authority.",
    ]
    for phrase in required:
        assert phrase in text


def test_0101_rejects_scheduler_like_controlproxy_direction() -> None:
    text = _read(DOC) + "\n" + _read(PLAN)
    required = [
        "ControlProxy must not own global priority calculation.",
        "ControlProxy must not create another bus.",
        "ControlProxy must not become a Scheduler-bis.",
        "Dispatcher remains useful, but only as a micro-kernel boundary.",
        "PolicyEngine remains useful, but only as an admission gate.",
        "The previously proposed scheduler-like ControlProxyRouteCoordinator is not accepted as the next direction.",
        "The next runtime code phase should introduce a narrow `RouteRuntimeManager`, not a scheduler-like coordinator.",
    ]
    for phrase in required:
        assert phrase in text


def test_0101_keeps_bus_and_data_plane_separate() -> None:
    text = _read(DOC) + "\n" + _read(DOT)
    required = [
        "There is one kernel observation EventBus.",
        "The existing EventBus remains the observation path.",
        "The route mmap/eventfd mechanism is a runtime data plane.",
        "it is not EventBus and is not a command bus.",
        "Visualization adapter\\nreads existing bus",
        "mmap/shm + eventfd\\ndata plane, not EventBus",
    ]
    for phrase in required:
        assert phrase in text


def test_0101_priorities_remain_kernel_ordering() -> None:
    text = _read(DOC) + "\n" + _read(PLAN)
    required = [
        "Priorities stay simple for this phase.",
        "Event priority -> PriorityQueue -> Scheduler.run() ordering",
        "ControlProxy does not calculate global priority",
        "Dispatcher does not mutate priority",
        "PolicyEngine = minimal admission gate before queue",
        "PriorityQueue = deterministic ordering",
    ]
    for phrase in required:
        assert phrase in text


def test_0101_manifest_and_report_are_present() -> None:
    manifest = _read(MANIFEST)
    report = _read(REPORT)
    required_manifest_entries = [
        "doc/architecture/CONTROLPROXY_SIMPLIFICATION_LOCK_0101.md",
        "doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0101.md",
        "doc/docs/architecture/runtime/91_controlproxy_simplification_lock.dot",
        "doc/CHANGELOG_0101_CONTROLPROXY_SIMPLIFICATION_LOCK.md",
        "tests/rules/test_controlproxy_simplification_lock_0101_rule.py",
        "PHASE0101_TEST_REPORT.md",
    ]
    for entry in required_manifest_entries:
        assert entry in manifest

    required_report_entries = [
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "search_commands_bounded: n/a",
    ]
    for entry in required_report_entries:
        assert entry in report
