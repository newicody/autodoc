from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "FAKE_RUNTIME_RECORDER_INGESTION.md"
MODULE = ROOT / "src" / "runtime" / "fake_runtime_recorder.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_fake_runtime_recorder_doc_locks_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "missipy.recorder.runtime_journal_record.v1",
        "fake runtime surface",
        "recorder journal",
        "7 total records",
        "real shared memory",
        "real semaphores",
        "ring buffer",
        "Recorder daemon",
        "Scheduler wiring",
        "RouteProxy daemon",
        "ControlFS mutation",
        "ZFS requirement",
        "NetworkBridge",
        "HardwareBridge",
        "cluster dispatch",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_fake_runtime_recorder_module_is_not_real_recorder() -> None:
    text = _read(MODULE)

    required_phrases = [
        "It only reads the fake JSONL runtime surface",
        "create shared memory",
        "create semaphores",
        "implement a ring buffer",
        "start a Recorder daemon",
        "call Scheduler",
        "call RouteProxy",
        "mutate ControlFS",
        "require ZFS",
        "implement NetworkBridge or HardwareBridge",
    ]

    for phrase in required_phrases:
        assert phrase in text
