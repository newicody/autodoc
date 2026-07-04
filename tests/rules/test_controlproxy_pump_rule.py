from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_PUMP_TICK.md"
MODULE = ROOT / "src" / "runtime" / "controlproxy_pump.py"
SEQUENCE = ROOT / "doc" / "architecture" / "REAL_IMPLEMENTATION_SEQUENCE_0081.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_controlproxy_pump_doc_locks_no_service_no_cli_and_tick_shape() -> None:
    text = _read(DOC)

    required_phrases = [
        "Status: 0084 implementation.",
        "ControlProxy = ControlFS declarative surface + RouteProxy materializer",
        "No service",
        "daemon",
        "service",
        "OpenRC",
        "resident process",
        "watcher",
        "poll loop",
        "CLI",
        "tick_controlproxy(controlfs_root, runtime_root)",
        "read ControlFS desired/active routes",
        "build RouteProxy dry-run plan",
        "materialize missing desired routes",
        "write mmap route files",
        "write ControlFS active route state",
        "publish event.bus/context.bus facts",
        "live mmap resize",
        "implicit update of active route",
        "delete/drain cleanup",
        "lease issuing",
        "security policy decision",
        "Scheduler call",
        "These are facts, not commands.",
        "module logic is importable",
        "CLI only when it is a real operator boundary",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_controlproxy_pump_module_locks_importable_non_daemon_scope() -> None:
    text = _read(MODULE)

    required_phrases = [
        "explicit importable pump, not a service",
        "tick_controlproxy(controlfs_root, runtime_root)",
        "does not:",
        "create a daemon",
        "start a service",
        "use OpenRC",
        "run forever",
        "watch ControlFS",
        "sleep or poll",
        "call Scheduler",
        "decide security policy",
        "grant leases",
        "implement lease handoff",
        "live resize mmap routes",
        "perform delete/drain cleanup",
        "implement inter-process locks",
        "implement VisPy",
        "add a CLI",
        "synchronous tick function",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_real_sequence_mentions_0084_as_pump_not_service() -> None:
    text = _read(SEQUENCE)

    assert "0084 ControlProxy pump/tick" in text
    assert "implemented as tick_controlproxy()" in text
    assert "no service, no OpenRC, no resident daemon" in text
