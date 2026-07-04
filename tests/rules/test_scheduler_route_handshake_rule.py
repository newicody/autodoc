from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "SCHEDULER_ROUTE_HANDSHAKE.md"
MODULE = ROOT / "src" / "runtime" / "scheduler_route_handshake.py"
SEQUENCE = ROOT / "doc" / "architecture" / "REAL_IMPLEMENTATION_SEQUENCE_0081.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_scheduler_route_handshake_doc_locks_scheduler_facing_no_service_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "Status: 0085 implementation.",
        "Scheduler-facing route handshake functions",
        "prepare_route_for_scheduler(...)",
        "tick_controlproxy(...)",
        "verify active route exists",
        "acquire route lease",
        "activate route lease",
        "return route_handle + lease_id",
        "No service",
        "daemon",
        "service",
        "OpenRC",
        "resident process",
        "watcher",
        "poll loop",
        "CLI",
        "idempotent for the same holder/scope",
        "different holder",
        "different scope",
        "closed lease",
        "does not decide security policy",
        "Scheduler",
        "policy engine",
        "zone/scope rules",
        "These are facts, not commands.",
        "live mmap resize",
        "No CLI",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_scheduler_route_handshake_module_locks_non_goals() -> None:
    text = _read(MODULE)

    required_phrases = [
        "Scheduler-facing route handshake",
        "tick_controlproxy()",
        "acquire route lease",
        "activate route lease",
        "not the Scheduler implementation",
        "already-authorized caller",
        "does not:",
        "create a daemon",
        "start a service",
        "use OpenRC",
        "run forever",
        "watch ControlFS",
        "sleep or poll",
        "implement the Scheduler event loop",
        "decide security policy",
        "bypass zone/scope policy",
        "write RouteMessage frames",
        "notify eventfd",
        "drain routes",
        "resize live mmap routes",
        "implement inter-process locks",
        "implement VisPy",
        "add a CLI",
        "synchronous function boundary",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_real_sequence_mentions_0085_implemented_handshake() -> None:
    text = _read(SEQUENCE)

    assert "0085 Scheduler handshake" in text
    assert "implemented as prepare_route_for_scheduler()" in text
    assert "acquires and activates route lease" in text
    assert "returns route_handle/lease to producer" in text
