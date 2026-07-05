from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "SCHEDULER_PRIORITY_ADMISSION_0105.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0105.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "95_scheduler_priority_admission.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0105_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0105_locks_priority_and_admission_responsibilities() -> None:
    text = _read(DOC) + "\n" + _read(PLAN)
    required = [
        "PriorityQueue is the only deterministic execution ordering mechanism",
        "PolicyEngine is minimal admission before queue",
        "Dispatcher is EventType -> Handler only",
        "ControlProxy / RouteRuntimeManager does not compute global priorities",
        "ControlProxy / RouteRuntimeManager does not decide policy/zone admission",
        "EventBus is observation only",
        "Route mmap/eventfd is data plane, not EventBus",
        "Specialist branch = business reasoning / transformation / strategy",
    ]
    for phrase in required:
        assert phrase in text


def test_0105_keeps_future_priority_policy_before_enqueue() -> None:
    text = _read(DOC) + "\n" + _read(PLAN)
    assert "EventClassPolicy + bounded GlobalContextSnapshot -> explicit priority value" in text
    assert "must stay before enqueue" in text
    assert "must not be hidden inside the Dispatcher, ControlProxy, EventBus" in text


def test_0105_graph_keeps_dispatcher_and_data_plane_separate() -> None:
    graph = _read(DOT)
    assert "Dispatcher\\nEventType -> Handler only" in graph
    assert "PriorityQueue\\nonly deterministic execution ordering" in graph
    assert "EventBus\\nobservation only" in graph
    assert "mmap/eventfd\\ndata plane, not EventBus" in graph
    assert "RouteRuntimeManager\\nControlFS + mmap/eventfd runtime" in graph
    assert "no direct runtime logic" in graph


def test_0105_manifest_does_not_touch_kernel_or_runtime_code() -> None:
    manifest = _read(MANIFEST)
    assert "tests/rules/test_scheduler_priority_admission_0105_rule.py" in manifest
    assert "doc/architecture/SCHEDULER_PRIORITY_ADMISSION_0105.md" in manifest
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/policy/engine.py",
        "src/kernel/event_bus.py",
        "src/runtime/route_runtime_manager.py",
    ]
    for item in forbidden:
        assert item not in manifest


def test_0105_phase_review_marks_architecture_only() -> None:
    text = _read(ROOT / "PHASE0105_TEST_REPORT.md")
    assert "code_rule_review: done" in text
    assert "code_rule_update_required: false" in text
    assert "live_path_status: n/a" in text
    assert "No Scheduler.run() modification" in text
    assert "No EventBus duplication" in text
