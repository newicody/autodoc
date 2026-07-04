from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "ROUTE_NOTIFICATION_PRIMITIVE.md"
MODULE = ROOT / "src" / "runtime" / "route_notification.py"
SEQUENCE = ROOT / "doc" / "architecture" / "REAL_IMPLEMENTATION_SEQUENCE_0081.md"
ACTIVE_DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_ACTIVE_ROUTE_MATERIALIZER.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_route_notification_doc_locks_eventfd_and_no_daemon_no_cli() -> None:
    text = _read(DOC)

    required_phrases = [
        "Status: 0082 implementation.",
        "writer writes RouteMessage frame to mmap route",
        "writer calls notifier.notify(1)",
        "reader/select loop sees notifier.fileno() readable",
        "reader drains notifier counter",
        "reader drains mmap route frames",
        "preferred: Python os.eventfd",
        "fallback: libc eventfd through ctypes",
        "fallback: non-blocking pipe",
        "No custom C extension is required.",
        "Why eventfd",
        "No daemon, no service",
        "OpenRC",
        "No CLI",
        "module logic is importable",
        "CLI only when it is a real operator boundary",
        "does not modify slot size",
        "does not resize mmap routes",
        "not a service and not a resident daemon",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_route_notification_module_locks_non_goals_and_backends() -> None:
    text = _read(MODULE)

    required_phrases = [
        "Prefer Linux eventfd through Python's os.eventfd",
        "Fall back to libc eventfd through ctypes",
        "Fall back to a non-blocking pipe",
        "does not",
        "create a daemon",
        "start a service",
        "use OpenRC",
        "watch ControlFS",
        "call Scheduler",
        "issue leases",
        "implement lease handoff",
        "mutate mmap route layout",
        "resize live mmap routes",
        "create POSIX shm_open objects",
        "require /dev/shm",
        "implement inter-process ownership rules",
        "implement VisPy",
        "not a CLI",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_real_sequence_removes_openrc_service_plan() -> None:
    text = _read(SEQUENCE)
    active_doc = _read(ACTIVE_DOC)

    assert "0084 ControlProxy pump/tick" in text
    assert "no service, no OpenRC, no resident daemon" in text
    assert "No OpenRC service and no resident daemon" in active_doc
    assert "ControlProxy daemon / OpenRC service" not in active_doc
