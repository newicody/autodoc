from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "runtime" / "bus_visualization_adapter.py"
DOC = ROOT / "doc" / "architecture" / "BUS_VISUALIZATION_ADAPTER_0093_R2.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0093_R2_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0093_r2_existing_bus_adapter_locks_operational_intent() -> None:
    text = _read(MODULE) + "\n" + _read(DOC)
    required = [
        "reads existing event.bus/context.bus objects",
        "does not instantiate EventBus",
        "does not create a parallel bus",
        "event_bus.subscribe()",
        "VisPy/browser",
        "EventBus is observation only",
        "Events/bus facts are facts, not commands",
        "No CLI",
        "No OpenRC service and no resident daemon",
        "No watcher",
        "No Scheduler.run() modification",
        "ControlProxy does not decide security",
        "Scheduler/policy/zone remain the authority",
        "No Qdrant",
        "No LLM",
        "No OpenVINO",
        "stdlib only",
    ]
    for phrase in required:
        assert phrase in text


def test_0093_r2_existing_bus_adapter_does_not_create_bus_or_ui_runtime() -> None:
    module = _read(MODULE)
    lowered = module.lower()
    forbidden = [
        "event_bus = eventbus(",
        "eventbus()",
        "asyncio.queue(",
        "import vispy",
        "from vispy",
        "import webbrowser",
        "asyncio.create_task",
        "subprocess",
        "argparse",
        "click",
        "import qdrant",
        "from qdrant",
        "import openvino",
        "from openvino",
    ]
    for phrase in forbidden:
        assert phrase not in lowered


def test_0093_r2_manifest_contains_only_adapter_surface() -> None:
    manifest = _read(MANIFEST)
    assert "src/runtime/bus_visualization_adapter.py" in manifest
    assert "tests/runtime/test_bus_visualization_adapter.py" in manifest
    assert "tests/rules/test_bus_visualization_adapter_rule.py" in manifest
    assert "Scheduler.run" not in manifest
    assert "PriorityQueue" not in manifest
    assert "Dispatcher" not in manifest
    assert "src/kernel/" not in manifest


def test_0093_r2_report_declares_existing_bus_scope() -> None:
    report = _read(ROOT / "PHASE0093_R2_TEST_REPORT.md")
    assert "existing EventBus" in report
    assert "does not instantiate" in report
    assert "does not create a parallel bus" in report
