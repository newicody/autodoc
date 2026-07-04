from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "ROUTEPROXY_DRY_RUN_RECONCILER.md"
MODULE = ROOT / "src" / "runtime" / "routeproxy_reconciler.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_routeproxy_dry_run_document_locks_p2_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "The RouteProxy is passive.",
        "It does not call the Scheduler.",
        "It does not decide security.",
        "real RouteProxy daemon",
        "inotify watcher",
        "real shm",
        "semaphores",
        "Scheduler wiring",
        "NetworkBridge",
        "HardwareBridge",
        "cluster dispatch",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_routeproxy_dry_run_module_is_not_runtime_daemon() -> None:
    text = _read(MODULE)

    required_phrases = [
        "It only compares desired/routes and active/routes",
        "create shared memory",
        "create semaphores",
        "watch with inotify",
        "run as a daemon",
        "call Scheduler",
        "decide security",
        "mutate ControlFS",
    ]

    for phrase in required_phrases:
        assert phrase in text
