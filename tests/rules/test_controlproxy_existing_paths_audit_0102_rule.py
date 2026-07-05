from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_EXISTING_PATHS_AUDIT_0102.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0102.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "92_controlproxy_existing_paths_audit.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0102_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0102_TEST_REPORT.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0102_audit_files_exist() -> None:
    for path in (DOC, PLAN, DOT, MANIFEST, REPORT):
        assert path.exists(), path


def test_0102_locks_existing_path_classification() -> None:
    text = _read(DOC) + "\n" + _read(PLAN)
    required = [
        "0102 is audit and marking only",
        "PolicyEngine = minimal admission gate before queue",
        "PriorityQueue = sole deterministic ordering mechanism",
        "Dispatcher = EventType -> Handler only",
        "Handler = thin adapter",
        "Specialist branch = business logic",
        "EventBus = observation only",
        "mmap/eventfd data plane",
        "compatibility wrapper candidate",
        "runtime primitive",
        "data plane primitive",
        "boundary filter primitive, not security authority",
        "TaskContext / ContextGate = context authority",
        "Qdrant = projection/search index only",
        "RouteRuntimeManager planned next",
    ]
    for phrase in required:
        assert phrase in text


def test_0102_prevents_parallel_scheduler_and_bus_language() -> None:
    text = _read(DOC) + "\n" + _read(PLAN) + "\n" + _read(REPORT)
    required = [
        "No new bus",
        "No ControlProxyRouteCoordinator scheduler-like",
        "No RouteRuntimeManager implementation yet",
        "RouteRuntimeManager does not schedule global work",
        "RouteRuntimeManager does not calculate global priority",
        "RouteRuntimeManager does not create a bus",
        "Dispatcher still resolves EventType -> Handler only",
        "ControlProxy = no global priority calculation",
        "mmap/eventfd = route data plane",
    ]
    for phrase in required:
        assert phrase in text


def test_0102_dot_is_root_attached_overlay_not_isolated_future_claim() -> None:
    dot = _read(DOT)
    required = [
        "root-attached overlay, not an isolated graph",
        "Micro-kernel command path",
        "ControlProxy Scheduler-facing compatibility path",
        "Route runtime primitives",
        "RouteRuntimeManager\\nplanned in 0103\\nnot implemented by 0102",
        "forbidden: EventBus does not command data plane",
        "forbidden: ControlProxy does not calculate global priority",
    ]
    for phrase in required:
        assert phrase in dot


def test_0102_manifest_is_docs_and_rules_only() -> None:
    manifest = _read(MANIFEST)
    assert "tests/rules/test_controlproxy_existing_paths_audit_0102_rule.py" in manifest
    assert "doc/docs/architecture/runtime/92_controlproxy_existing_paths_audit.dot" in manifest
    assert "No runtime code." in manifest
    forbidden = [
        "src/kernel/",
        "src/policy/",
        "src/runtime/",
        "src/contracts/",
        "tools/",
    ]
    for token in forbidden:
        assert token not in manifest
