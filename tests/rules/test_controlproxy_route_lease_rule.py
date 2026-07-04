from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_ROUTE_LEASE_STATE.md"
MODULE = ROOT / "src" / "runtime" / "controlproxy_route_lease.py"
SEQUENCE = ROOT / "doc" / "architecture" / "REAL_IMPLEMENTATION_SEQUENCE_0081.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_route_lease_doc_locks_state_machine_and_authority_boundary() -> None:
    text = _read(DOC)

    required_phrases = [
        "Status: 0083 implementation.",
        "ControlProxy = ControlFS declarative surface + RouteProxy materializer",
        "active/routes/<route_id>/lease.json",
        "active/routes/<route_id>/status.json",
        "not_leased -> leased -> active -> draining -> closed",
        "leased -> closed",
        "not_leased -> active",
        "active -> leased",
        "closed -> active",
        "missipy.controlproxy.route_lease.v1",
        "lease_state",
        "current_lease_id",
        "current_lease_holder",
        "Security and authorization remain",
        "Scheduler",
        "policy engine",
        "zone/scope rules",
        "No daemon, no service",
        "OpenRC",
        "No CLI",
        "module logic is importable",
        "CLI only when it is a real operator boundary",
        "ControlProxy pump/tick",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_route_lease_module_locks_non_goals() -> None:
    text = _read(MODULE)

    required_phrases = [
        "not_leased -> leased -> active -> draining -> closed",
        "There is no daemon, no service and no CLI.",
        "does not:",
        "create a daemon",
        "start a service",
        "use OpenRC",
        "watch ControlFS",
        "call Scheduler",
        "decide security policy",
        "create mmap routes",
        "write RouteMessage frames",
        "notify eventfd",
        "resize live mmap routes",
        "implement inter-process locks",
        "implement VisPy",
        "lease state only, not the lease authority",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_real_sequence_mentions_0083_lease_state_and_no_service_0084() -> None:
    text = _read(SEQUENCE)

    assert "0083 route lease state" in text
    assert "file-backed lease.json plus active status update" in text
    assert "0084 ControlProxy pump/tick" in text
    assert "no service, no OpenRC, no resident daemon" in text
