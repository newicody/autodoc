from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "INPROCESS_FRAME_RING_INTEGRATION.md"
MODULE = ROOT / "src" / "runtime" / "inprocess_frame_ring.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_inprocess_frame_ring_doc_locks_integration_only_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "Status: 0078 in-process integration only.",
        "RouteMessage",
        "binary RouteMessage frame",
        "in-process bounded frame ring",
        "validated RouteMessage",
        "total_frame_bytes",
        "max_frame_bytes",
        "reject",
        "drop_oldest",
        "no silent overwrite",
        "real shared memory",
        "mmap",
        "semaphores",
        "eventfd",
        "futex",
        "RouteProxy daemon",
        "ControlFS watcher",
        "Scheduler wiring",
        "zero-copy transport",
        "thread/process safety",
        "NetworkBridge",
        "HardwareBridge",
        "cluster dispatch",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_inprocess_frame_ring_module_is_not_ipc() -> None:
    text = _read(MODULE)

    required_phrases = [
        "It integrates the phase 0077 RouteMessage frame codec",
        "create shared memory",
        "use mmap",
        "create semaphores",
        "use eventfd",
        "use futex",
        "start RouteProxy",
        "watch ControlFS",
        "call Scheduler",
        "provide zero-copy transport",
        "provide thread/process safety",
        "implement NetworkBridge or HardwareBridge",
    ]

    for phrase in required_phrases:
        assert phrase in text
