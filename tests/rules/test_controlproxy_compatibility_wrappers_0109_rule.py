from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/runtime/controlproxy_compatibility_wrappers.py"
DOC = ROOT / "doc/architecture/CONTROLPROXY_COMPATIBILITY_WRAPPERS_0109.md"
PLAN = ROOT / "doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0109.md"
DOT = ROOT / "doc/docs/architecture/runtime/99_controlproxy_compatibility_wrappers.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0109_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0109_TEST_REPORT.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0109_documents_compatibility_cleanup_boundary() -> None:
    text = "\n".join(_read(path) for path in (MODULE, DOC, PLAN, DOT, REPORT))
    required = [
        "0109 compatibility wrapper cleanup",
        "prepare_route_for_scheduler",
        "handle_scheduler_route_request",
        "compatibility wrappers",
        "do not extend legacy wrappers",
        "Handler -> RouteRuntimeManager",
        "No Scheduler.run() modification",
        "Dispatcher = EventType -> Handler only",
        "PolicyEngine = minimal admission before queue",
        "PriorityQueue = deterministic execution order",
        "EventBus = observation only",
        "Route mmap/eventfd = data plane, not EventBus",
        "No ControlProxyBus",
        "No RouteBus",
        "No VisualizationBus",
        "Specialist branch owns business logic",
        "No scheduler-like ControlProxy coordinator",
    ]
    for phrase in required:
        assert phrase in text


def test_0109_manifest_is_additive_and_avoids_kernel_changes() -> None:
    manifest = _read(MANIFEST)

    assert "src/runtime/controlproxy_compatibility_wrappers.py" in manifest
    assert "tests/runtime/test_controlproxy_compatibility_wrappers.py" in manifest
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/kernel/dispatcher.py" not in manifest
    assert "src/kernel/queue.py" not in manifest
    assert "src/policy/engine.py" not in manifest


def test_0109_report_keeps_code_rule_review_block() -> None:
    report = _read(REPORT)

    assert "code_rule_review: done" in report
    assert "code_rule_update_required: false" in report
    assert "live_path_status: cleanup" in report
    assert "external_dependencies_added: false" in report
