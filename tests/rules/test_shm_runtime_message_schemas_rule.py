from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "SHM_RUNTIME_MESSAGE_SCHEMAS.md"
MODULE = ROOT / "src" / "runtime" / "shm_runtime_schema.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_shm_runtime_schema_document_locks_p3_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "missipy.shm.event_message.v1",
        "missipy.shm.context_message.v1",
        "missipy.shm.data_handle.v1",
        "missipy.shm.route_message.v1",
        "Heavy payloads must be referenced with `DataHandle`.",
        "real shared memory",
        "real semaphores",
        "ring buffers",
        "RouteProxy daemon",
        "Scheduler wiring",
        "NetworkBridge",
        "HardwareBridge",
        "cluster dispatch",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_shm_runtime_schema_module_is_schema_only() -> None:
    text = _read(MODULE)

    required_phrases = [
        "It only validates compact message structures",
        "create shared memory",
        "create semaphores",
        "implement a ring buffer",
        "call Scheduler",
        "call RouteProxy",
        "write ControlFS",
        "access ZFS",
        "implement NetworkBridge or HardwareBridge",
    ]

    for phrase in required_phrases:
        assert phrase in text
