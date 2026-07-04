from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "BABY_FORK_RUNTIME_MESSAGE_PROJECTION.md"
MODULE = ROOT / "src" / "context" / "baby_fork_runtime_projection.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_baby_fork_projection_document_locks_adapter_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "This phase connects the baby-fork smoke project",
        "without changing the existing smoke pipeline",
        "baby_fork.retrieval",
        "baby_fork.variant_stub",
        "baby_fork.context_gate",
        "DataHandle",
        "EventBusMessage",
        "ContextBusMessage",
        "RouteMessage",
        "real shared memory",
        "semaphores",
        "RouteProxy daemon",
        "Scheduler wiring",
        "ControlFS mutation",
        "NetworkBridge",
        "HardwareBridge",
        "cluster dispatch",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_baby_fork_projection_module_is_adapter_only() -> None:
    text = _read(MODULE)

    required_phrases = [
        "It only projects an existing baby-fork report",
        "create shared memory",
        "create semaphores",
        "start RouteProxy",
        "call Scheduler",
        "mutate ControlFS",
        "replace the baby-fork smoke project",
    ]

    for phrase in required_phrases:
        assert phrase in text
