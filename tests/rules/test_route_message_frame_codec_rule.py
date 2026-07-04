from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "ROUTE_MESSAGE_FRAME_CODEC.md"
MODULE = ROOT / "src" / "runtime" / "route_frame_codec.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_route_message_frame_codec_doc_locks_codec_only_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "Status: 0077 codec only.",
        "RouteMessage object",
        "deterministic payload bytes",
        "binary frame",
        "validated RouteMessage object",
        "magic",
        "payload SHA-256",
        "RouteMessage schema validation",
        "real shared memory",
        "mmap",
        "semaphores",
        "eventfd",
        "futex",
        "ring buffer implementation",
        "RouteProxy daemon",
        "ControlFS watcher",
        "Scheduler wiring",
        "zero-copy transport",
        "NetworkBridge",
        "HardwareBridge",
        "cluster dispatch",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_route_message_frame_codec_module_is_codec_only() -> None:
    text = _read(MODULE)

    required_phrases = [
        "It only encodes a validated RouteMessage",
        "create shared memory",
        "use mmap",
        "create semaphores",
        "use eventfd",
        "use futex",
        "implement a ring buffer",
        "start RouteProxy",
        "watch ControlFS",
        "call Scheduler",
        "provide zero-copy transport",
        "implement NetworkBridge or HardwareBridge",
    ]

    for phrase in required_phrases:
        assert phrase in text
