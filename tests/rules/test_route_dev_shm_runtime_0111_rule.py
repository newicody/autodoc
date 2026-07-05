from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "runtime" / "route_dev_shm_runtime.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_DEV_SHM_RUNTIME_0111.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0111.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "101_route_dev_shm_runtime.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0111_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0111_TEST_REPORT.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0111_dev_shm_runtime_locks_data_plane_boundary() -> None:
    text = "\n".join(_read(path) for path in (MODULE, DOC, PLAN, DOT))
    required = [
        "explicit /dev/shm runtime root",
        "real inter-process data plane",
        "no implicit file fallback",
        "Route mmap/eventfd is data plane, not EventBus",
        "EventBus remains observation only",
        "No ControlProxyBus",
        "No RouteBus",
        "No VisualizationBus",
        "builds RouteRuntimeManager",
        "does not modify Scheduler.run()",
        "PolicyEngine remains minimal admission before queue",
        "PriorityQueue remains deterministic execution order",
        "Dispatcher remains EventType -> Handler only",
        "stdlib only",
    ]
    for phrase in required:
        assert phrase in text


def test_0111_dev_shm_runtime_does_not_import_kernel_or_eventbus() -> None:
    module = _read(MODULE)
    forbidden = [
        "from kernel",
        "import kernel",
        "EventBus(",
        "from kernel.event_bus",
        "from kernel.scheduler",
        "from policy.engine",
        "from kernel.queue",
        "from kernel.dispatcher",
        "Dispatcher(",
    ]
    for phrase in forbidden:
        assert phrase not in module


def test_0111_manifest_is_additive_and_avoids_kernel_files() -> None:
    manifest = _read(MANIFEST)
    assert "src/runtime/route_dev_shm_runtime.py" in manifest
    assert "tests/runtime/test_route_dev_shm_runtime.py" in manifest
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/policy/engine.py",
        "src/kernel/event_bus.py",
    ]
    for path in forbidden:
        assert path not in manifest


def test_0111_report_contains_code_rule_review() -> None:
    report = _read(REPORT)
    assert "code_rule_review: done" in report
    assert "code_rule_update_required: false" in report
    assert "live_path_status: transition" in report
