from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "runtime" / "route_generation_locked_materializer.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_GENERATION_LOCKED_MATERIALIZER_0095.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0095_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0095_locked_materializer_locks_operational_intent() -> None:
    text = _read(MODULE) + "\n" + _read(DOC)
    required = [
        "with acquire_route_generation_lock",
        "load -> verify -> materialize -> persist",
        "route_id -> current_generation",
        "g2/g3",
        "No CLI",
        "No OpenRC service and no resident daemon",
        "No watcher",
        "No Scheduler.run() modification",
        "No live mmap resize",
        "ControlProxy does not decide security",
        "Scheduler/policy/zone remain the authority",
        "Not /dev/shm-only",
        "standard library only",
    ]
    for phrase in required:
        assert phrase in text


def test_0095_locked_materializer_does_not_import_kernel_or_backends() -> None:
    source = _read(MODULE)
    forbidden = [
        "kernel.scheduler",
        "kernel.queue",
        "runtime.dispatcher",
        "openvino",
        "qdrant",
        "subprocess",
        "argparse",
    ]
    for phrase in forbidden:
        assert phrase not in source


def test_0095_manifest_keeps_patch_scope_small() -> None:
    manifest = _read(MANIFEST)
    assert "src/runtime/route_generation_locked_materializer.py" in manifest
    assert "tests/runtime/test_route_generation_locked_materializer.py" in manifest
    assert "tests/rules/test_route_generation_locked_materializer_rule.py" in manifest
    assert "route_generation_table.py" not in manifest
    assert "route_generation_lock.py" not in manifest
