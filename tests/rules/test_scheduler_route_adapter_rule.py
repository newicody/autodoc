from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "SCHEDULER_ROUTE_ADAPTER.md"
MODULE = ROOT / "src" / "runtime" / "scheduler_route_adapter.py"
SEQUENCE = ROOT / "doc" / "architecture" / "REAL_IMPLEMENTATION_SEQUENCE_0081.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_scheduler_route_adapter_doc_locks_existing_scheduler_boundary_scope() -> None:
    text = _read(DOC)

    required_phrases = [
        "Status: 0086 implementation.",
        "minimal adapter for the existing Scheduler boundary",
        "SchedulerRouteRequest",
        "handle_scheduler_route_request(...)",
        "SchedulerRouteReply",
        "authorized=True",
        "policy_decision_id=<non-empty id>",
        "does not decide security policy",
        "Scheduler",
        "PolicyEngine",
        "zone/scope rules",
        "No service",
        "daemon",
        "service",
        "OpenRC",
        "resident process",
        "watcher",
        "poll loop",
        "CLI",
        "No CLI",
        "Existing Scheduler boundary",
        "Scheduler event loop",
        "PriorityQueue",
        "Dispatcher",
        "PolicyEngine",
        "These are facts, not commands.",
        "live mmap resize",
        "No CLI",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_scheduler_route_adapter_module_locks_non_goals() -> None:
    text = _read(MODULE)

    required_phrases = [
        "Scheduler route adapter",
        "minimal adapter boundary",
        "already-authorized Scheduler route",
        "verify authorized=True and policy_decision_id exists",
        "prepare_route_for_scheduler(...)",
        "not the Scheduler loop itself",
        "does not:",
        "create a daemon",
        "start a service",
        "use OpenRC",
        "run forever",
        "watch ControlFS",
        "sleep or poll",
        "implement the Scheduler event loop",
        "implement PriorityQueue",
        "implement Dispatcher",
        "call PolicyEngine",
        "decide security policy",
        "bypass zone/scope policy",
        "generate desired manifests",
        "write RouteMessage frames",
        "notify eventfd",
        "drain routes",
        "resize live mmap routes",
        "implement inter-process locks",
        "implement VisPy",
        "add a CLI",
        "No CLI.",
        "synchronous adapter function",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_real_sequence_mentions_0086_scheduler_route_adapter() -> None:
    text = _read(SEQUENCE)

    assert "0086 Scheduler route adapter" in text
    assert "implemented as handle_scheduler_route_request()" in text
    assert "already-authorized request/reply boundary" in text
    assert "no Scheduler loop change" in text
