from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "authorized_route_request_queue.py"
TOOL = ROOT / "tools" / "append_authorized_route_requests_from_context_bus.py"
DOC = ROOT / "doc" / "architecture" / "AUTHORIZED_ROUTE_REQUEST_QUEUE_HANDOFF_0179.md"
RULE = ROOT / "doc" / "code-rules" / "0179_authorized_route_request_queue_handoff_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0179_CHANGED_FILES.md"


def test_0179_module_materializes_authorized_queue_without_execution() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for token in [
        "context.bus.jsonl",
        "read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl",
        "SchedulerRouteRequest.from_mapping",
        "scheduler.route_requests.jsonl",
        "This module requires an explicit policy_decision_id",
        "This module does not call handle_scheduler_route_request",
        "This module does not instantiate Scheduler",
        "This module does not modify Scheduler.run()",
        "This module does not instantiate EventBus",
    ]:
        assert token in source
    assert "handle_scheduler_route_request(" not in source
    assert "from kernel.scheduler import Scheduler" not in source
    assert "from kernel.event_bus import EventBus" not in source


def test_0179_doc_locks_handoff_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0179 is a handoff queue, not route execution",
        "The handoff source is context.bus.jsonl",
        "The output is scheduler.route_requests.jsonl",
        "Every queued item is validated with SchedulerRouteRequest.from_mapping",
        "Only authorized SchedulerRouteRequest mappings are queued",
        "handle_scheduler_route_request is not called",
        "Scheduler.run() is not modified",
    ]:
        assert token in doc


def test_0179_rule_blocks_execution_and_frame_writes() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read from context.bus.jsonl through the 0178 reader",
        "Write only scheduler.route_requests.jsonl handoff entries",
        "Require explicit policy_decision_id",
        "Validate queued items with SchedulerRouteRequest.from_mapping",
        "Do not call handle_scheduler_route_request",
        "Do not modify Scheduler.run()",
        "Do not write ControlProxy or RouteProxy frames",
        "Do not instantiate EventBus",
    ]:
        assert token in rule


def test_0179_tool_is_local_queue_writer_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--context-bus" in source
    assert "--runtime-root" in source
    assert "--policy-decision-id" in source
    assert "append_authorized_route_requests_from_context_bus" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0179_manifest_lists_handoff_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "src/context/authorized_route_request_queue.py",
        "tools/append_authorized_route_requests_from_context_bus.py",
        "tests/context/test_authorized_route_request_queue_handoff_0179.py",
        "tests/tools/test_append_authorized_route_requests_from_context_bus_0179.py",
        "tests/rules/test_authorized_route_request_queue_handoff_0179_rule.py",
    ]:
        assert token in manifest
