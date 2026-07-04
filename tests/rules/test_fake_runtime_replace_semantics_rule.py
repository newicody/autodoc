from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "FAKE_RUNTIME_REPLACE_SEMANTICS.md"
MODULE = ROOT / "src" / "runtime" / "fake_route_transport.py"
TOOL = ROOT / "tools" / "write_baby_fork_fake_runtime.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_fake_runtime_replace_semantics_doc_locks_bug_and_fix() -> None:
    text = _read(DOC)

    required_phrases = [
        "route_message_count = 6",
        "record_count = 10",
        "route_message_count = 3",
        "record_count = 7",
        "replaces route files by default",
        "--append-routes",
        "real shared memory",
        "RouteProxy daemon",
        "Scheduler wiring",
        "ControlFS mutation",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_fake_route_transport_defaults_to_replacing_routes() -> None:
    text = _read(MODULE)

    required_phrases = [
        "replace_routes: bool = True",
        "shutil.rmtree(routes_root)",
        "repeated end-to-end",
        "remain deterministic",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_write_baby_fork_fake_runtime_exposes_append_routes_flag() -> None:
    text = _read(TOOL)

    assert "--append-routes" in text
    assert "replace_routes=not args.append_routes" in text
