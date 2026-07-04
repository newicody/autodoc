from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_ACTIVE_ROUTE_MATERIALIZER.md"
MODULE = ROOT / "src" / "runtime" / "controlproxy_active_routes.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_active_route_materializer_doc_locks_real_implementation_path() -> None:
    text = _read(DOC)

    required_phrases = [
        "Status: 0081 implementation bridge.",
        "ControlProxy = ControlFS declarative surface + RouteProxy materializer",
        "desired RouteManifest",
        "mmap route files",
        "ControlFS active/routes/<route_id>/manifest.json",
        "ControlFS active/routes/<route_id>/status.json",
        "missipy.controlproxy.active_route_status.v1",
        "not_leased",
        "Real implementation path",
        "ControlProxy daemon / OpenRC service",
        "No CLI",
        "module logic is importable",
        "CLI only when it is a real operator boundary",
        "POSIX shm_open",
        "mandatory /dev/shm",
        "semaphores",
        "eventfd",
        "futex",
        "Scheduler wiring",
        "route lease issuing",
        "lease handoff",
        "live mmap resize",
        "inter-process safety",
        "VisPy renderer",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_active_route_materializer_module_locks_non_goals() -> None:
    text = _read(MODULE)

    required_phrases = [
        "ControlProxy = ControlFS declarative surface + RouteProxy materializer",
        "mmap runtime route files",
        "ControlFS active route manifest",
        "ControlFS active route status",
        "does not:",
        "create POSIX shared memory with shm_open",
        "require /dev/shm",
        "create semaphores",
        "create eventfd",
        "create futex",
        "start a ControlProxy daemon",
        "watch ControlFS with inotify",
        "call Scheduler",
        "issue route leases",
        "implement lease handoff",
        "resize live mmap routes",
        "implement inter-process safety",
        "implement VisPy",
        "not a CLI",
    ]

    for phrase in required_phrases:
        assert phrase in text
