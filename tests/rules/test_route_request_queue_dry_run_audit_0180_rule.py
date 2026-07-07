from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "authorized_route_request_queue_dry_run.py"
TOOL = ROOT / "tools" / "audit_authorized_route_request_queue_dry_run.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_REQUEST_QUEUE_DRY_RUN_AUDIT_0180.md"
RULE = ROOT / "doc" / "code-rules" / "0180_route_request_queue_dry_run_audit_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0180_CHANGED_FILES.md"


def test_0180_module_is_dry_run_only() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for token in [
        "scheduler.route_requests.jsonl",
        "iter_authorized_route_request_queue",
        "SchedulerRouteRequest objects",
        "readiness/audit report",
        "This module does not call handle_scheduler_route_request",
        "This module does not instantiate Scheduler",
        "This module does not modify Scheduler.run()",
        "This module does not instantiate EventBus",
        "This module does not write ControlProxy or RouteProxy frames",
    ]:
        assert token in source
    assert "handle_scheduler_route_request(" not in source
    assert "from kernel.scheduler import Scheduler" not in source
    assert "from kernel.event_bus import EventBus" not in source


def test_0180_doc_locks_dry_run_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0180 is a dry-run audit, not route execution",
        "The input is scheduler.route_requests.jsonl",
        "The output is a readiness report",
        "It validates queued items through SchedulerRouteRequest.from_mapping",
        "It does not call handle_scheduler_route_request",
        "It does not modify Scheduler.run()",
        "It does not write ControlProxy or RouteProxy frames",
    ]:
        assert token in doc


def test_0180_rule_blocks_execution() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read only scheduler.route_requests.jsonl",
        "Produce only a dry-run readiness report",
        "Validate queued items with SchedulerRouteRequest.from_mapping",
        "Do not call handle_scheduler_route_request",
        "Do not modify Scheduler.run()",
        "Do not instantiate Scheduler",
        "Do not instantiate EventBus",
        "Do not write ControlProxy or RouteProxy frames",
    ]:
        assert token in rule


def test_0180_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--queue" in source
    assert "audit_authorized_route_request_queue_dry_run" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0180_manifest_lists_dry_run_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "src/context/authorized_route_request_queue_dry_run.py",
        "tools/audit_authorized_route_request_queue_dry_run.py",
        "tests/context/test_authorized_route_request_queue_dry_run_0180.py",
        "tests/tools/test_audit_authorized_route_request_queue_dry_run_0180.py",
        "tests/rules/test_route_request_queue_dry_run_audit_0180_rule.py",
    ]:
        assert token in manifest
