from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_route_handler_dry_run_handoff_plan.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_HANDLER_DRY_RUN_HANDOFF_PLAN_0182.md"
RULE = ROOT / "doc" / "code-rules" / "0182_route_handler_dry_run_handoff_plan_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0182_CHANGED_FILES.md"


def test_0182_tool_is_dry_run_plan_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0182 is a planning tool only",
        "scheduler.route_requests.jsonl",
        "route_handler_dry_run_plan.jsonl",
        "It does not import runtime handler modules",
        "It does not call handle_scheduler_route_request",
        "It does not modify Scheduler.run",
        "It does not instantiate Scheduler",
        "It does not instantiate EventBus",
        "It does not write RouteProxy or ControlProxy frames",
        "ast.parse",
    ]:
        assert token in source
    assert "handle_scheduler_route_request(" not in source
    assert "from runtime.scheduler_route_handler_minimal import" not in source
    assert "from kernel.scheduler import Scheduler" not in source
    assert "from kernel.event_bus import EventBus" not in source


def test_0182_doc_locks_handoff_plan_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0182 builds a dry-run handoff plan, not a handler call",
        "The input is scheduler.route_requests.jsonl",
        "The output is route_handler_dry_run_plan.jsonl",
        "It reads the handler file as AST only",
        "It does not import the handler module",
        "It does not call handle_scheduler_route_request",
        "A future patch may consume the plan only after review",
    ]:
        assert token in doc


def test_0182_rule_blocks_execution_and_new_handler() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read scheduler.route_requests.jsonl from 0179",
        "Build only route_handler_dry_run_plan.jsonl",
        "Do not call handle_scheduler_route_request",
        "Do not import runtime handler modules",
        "Do not add a new runtime handler",
        "Do not modify Scheduler.run",
        "Do not write ControlProxy or RouteProxy frames",
    ]:
        assert token in rule


def test_0182_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--queue" in source
    assert "--output" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0182_manifest_lists_handoff_plan_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/build_route_handler_dry_run_handoff_plan.py",
        "tests/tools/test_build_route_handler_dry_run_handoff_plan_0182.py",
        "tests/rules/test_route_handler_dry_run_handoff_plan_0182_rule.py",
        "doc/architecture/ROUTE_HANDLER_DRY_RUN_HANDOFF_PLAN_0182.md",
        "doc/code-rules/0182_route_handler_dry_run_handoff_plan_rule.md",
    ]:
        assert token in manifest
