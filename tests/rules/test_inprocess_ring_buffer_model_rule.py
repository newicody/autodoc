from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "INPROCESS_RING_BUFFER_MODEL.md"
MODULE = ROOT / "src" / "runtime" / "inprocess_ring_buffer.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_inprocess_ring_buffer_doc_locks_model_only_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "Status: 0076 model only.",
        "bounded capacity",
        "FIFO ordering",
        "monotonic sequence",
        "explicit overflow behavior",
        "no silent overwrite",
        "validated RouteMessage",
        "reject",
        "drop_oldest",
        "real shared memory",
        "mmap",
        "semaphores",
        "eventfd",
        "futex",
        "RouteProxy daemon",
        "ControlFS watcher",
        "Scheduler wiring",
        "thread/process safety",
        "NetworkBridge",
        "HardwareBridge",
        "cluster dispatch",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_inprocess_ring_buffer_module_is_not_ipc() -> None:
    text = _read(MODULE)

    required_phrases = [
        "It only models bounded ring behavior in-process",
        "create shared memory",
        "use mmap",
        "create semaphores",
        "use eventfd",
        "use futex",
        "implement a RouteProxy daemon",
        "watch ControlFS",
        "call Scheduler",
        "provide thread/process safety",
        "implement NetworkBridge or HardwareBridge",
    ]

    for phrase in required_phrases:
        assert phrase in text
