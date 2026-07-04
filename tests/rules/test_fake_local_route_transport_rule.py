from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "FAKE_LOCAL_ROUTE_TRANSPORT.md"
MODULE = ROOT / "src" / "runtime" / "fake_route_transport.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_fake_local_route_transport_doc_locks_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "fake transport",
        "data.index.jsonl",
        "event.bus.jsonl",
        "context.bus.jsonl",
        "routes/<route_id>/messages.jsonl",
        "does not prove performance",
        "real shared memory",
        "real semaphores",
        "ring buffer",
        "RouteProxy daemon",
        "ControlFS watcher",
        "Scheduler wiring",
        "NetworkBridge",
        "HardwareBridge",
        "cluster dispatch",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_fake_local_route_transport_module_is_fake_only() -> None:
    text = _read(MODULE)

    required_phrases = [
        "It stores validated runtime messages as JSONL files",
        "create shared memory",
        "create semaphores",
        "implement a ring buffer",
        "watch ControlFS",
        "call Scheduler",
        "call RouteProxy",
        "access ZFS",
        "implement NetworkBridge or HardwareBridge",
    ]

    for phrase in required_phrases:
        assert phrase in text
