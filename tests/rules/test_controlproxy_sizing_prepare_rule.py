from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_SIZING_PREPARE_PROTOCOL.md"
AUDIT = ROOT / "doc" / "architecture" / "REPOSITORY_ARCHITECTURE_AUDIT_0079_R2.md"
INDEX = ROOT / "doc" / "architecture" / "ARCHITECTURE_INDEX_0079_R2.md"
MANIFEST = ROOT / "src" / "runtime" / "controlfs_manifest.py"
PREPARE = ROOT / "src" / "runtime" / "controlproxy_prepare.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_controlproxy_doc_locks_unified_model_and_protocol() -> None:
    text = _read(DOC)

    required_phrases = [
        "ControlProxy = ControlFS declarative surface + RouteProxy materializer",
        "ControlFS and RouteProxy are treated as one runtime control unit.",
        "short prepare frame with required_frame_bytes",
        "publishes ready/denied state to event.bus and context.bus",
        "route lease / route_handle",
        "reuse_active",
        "create_route_generation",
        "create_next_generation",
        "deny",
        "The old 0079 split ControlFS sizing from the proxy too much.",
        "Bus messages are facts, not commands.",
        "The semaphore does not create SHM and does not size slots.",
        "real shared memory",
        "mmap implementation",
        "Scheduler wiring",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_repository_audit_mentions_0079_replacement_and_remaining_mmap_gap() -> None:
    text = _read(AUDIT)

    required_phrases = [
        "replaces the rejected old `0079`",
        "Scope: repository reconstructed from applied patches `0063-r2` through `0078`.",
        "ControlProxy unit vocabulary.",
        "Route prepare request/status protocol.",
        "Route sizing as part of ControlProxy, not separate ControlFS-only logic.",
        "file-backed fixed-slot mmap route",
        "0080 file-backed fixed-slot mmap route",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_architecture_index_places_next_mmap_after_0079_r2() -> None:
    text = _read(INDEX)

    assert "0079-r2 ControlProxy sizing + prepare handshake + bus visibility" in text
    assert "0080 file-backed fixed-slot mmap route prototype" in text


def test_manifest_and_prepare_module_lock_no_mmap_yet() -> None:
    manifest_text = _read(MANIFEST)
    prepare_text = _read(PREPARE)

    for phrase in [
        "ControlProxy = ControlFS declarative surface + RouteProxy materializer",
        "transport",
        "slot_size",
        "slot_count",
        "max_frame_bytes",
        "observed_frame_bytes",
        "mmap.fixed_slot",
    ]:
        assert phrase in manifest_text

    for phrase in [
        "ControlProxy = ControlFS declarative state + RouteProxy materializer",
        "does not:",
        "implement mmap",
        "resize a live mmap ring",
        "create semaphores",
        "event.bus",
        "context.bus",
    ]:
        assert phrase in prepare_text
