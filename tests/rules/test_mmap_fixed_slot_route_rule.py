from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "MMAP_FIXED_SLOT_ROUTE.md"
MODULE = ROOT / "src" / "runtime" / "mmap_fixed_slot_route.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_mmap_fixed_slot_doc_locks_scope_and_no_cli_rule() -> None:
    text = _read(DOC)

    required_phrases = [
        "Status: 0080 prototype.",
        "ControlProxy decision",
        "file-backed fixed-slot mmap route",
        "ring.bin",
        "status.json",
        "slot header 64 bytes",
        "fixed frame area slot_size bytes",
        "validate frame",
        "write slot header as EMPTY",
        "write slot header as COMMITTED",
        "verify frame checksum",
        "No CLI",
        "module logic is importable",
        "CLI only when it is a real operator boundary",
        "POSIX shm_open",
        "mandatory /dev/shm",
        "semaphores",
        "eventfd",
        "futex",
        "Scheduler wiring",
        "lease handoff",
        "live mmap resize",
        "inter-process safety",
        "VisPy renderer",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_mmap_fixed_slot_module_locks_non_goals() -> None:
    text = _read(MODULE)

    required_phrases = [
        "file-backed mmap ring with fixed-size slots",
        "does not:",
        "create POSIX shared memory with shm_open",
        "require /dev/shm",
        "create semaphores",
        "create eventfd",
        "create futex",
        "start a ControlProxy daemon",
        "watch ControlFS",
        "call Scheduler",
        "implement lease handoff",
        "implement live mmap resize",
        "implement inter-process safety",
        "implement VisPy",
    ]

    for phrase in required_phrases:
        assert phrase in text
