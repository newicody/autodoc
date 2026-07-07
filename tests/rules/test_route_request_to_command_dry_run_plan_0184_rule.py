from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_route_request_to_command_dry_run_plan.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_REQUEST_TO_COMMAND_DRY_RUN_PLAN_0184.md"
RULE = ROOT / "doc" / "code-rules" / "0184_route_request_to_command_dry_run_plan_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0184_CHANGED_FILES.md"


def test_0184_tool_is_request_to_command_plan_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0184 is a planning tool only",
        "scheduler.route_requests.jsonl",
        "route_request_to_command_dry_run_plan.jsonl",
        "build_single_frame_route_command",
        "handle_scheduler_route_command",
        "It does not import runtime handler modules",
        "It does not call build_single_frame_route_command",
        "It does not call handle_scheduler_route_command",
        "It does not call handle_scheduler_route_request",
        "It does not modify Scheduler.run",
        "It does not instantiate Scheduler",
        "It does not instantiate EventBus",
        "It does not write RouteProxy or ControlProxy frames",
    ]:
        assert token in source
    assert "from runtime.scheduler_route_handler_minimal import" not in source
    assert "handle_scheduler_route_command(" not in source
    assert "handle_scheduler_route_request(" not in source
    assert "build_single_frame_route_command(" not in source


def test_0184_doc_locks_request_to_command_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0184 maps SchedulerRouteRequest data into command-builder kwargs",
        "The input is scheduler.route_requests.jsonl",
        "The output is route_request_to_command_dry_run_plan.jsonl",
        "It targets build_single_frame_route_command",
        "It does not call build_single_frame_route_command",
        "It does not call handle_scheduler_route_command",
        "A future patch may consume this plan only after review",
    ]:
        assert token in doc


def test_0184_rule_blocks_execution_and_handler_import() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read scheduler.route_requests.jsonl from 0179",
        "Build only route_request_to_command_dry_run_plan.jsonl",
        "Normalize typed refs for the existing command builder",
        "Do not import runtime handler modules",
        "Do not call build_single_frame_route_command",
        "Do not call handle_scheduler_route_command",
        "Do not modify Scheduler.run",
        "Do not write ControlProxy or RouteProxy frames",
    ]:
        assert token in rule


def test_0184_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--queue" in source
    assert "--output" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0184_manifest_lists_plan_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/build_route_request_to_command_dry_run_plan.py",
        "tests/tools/test_build_route_request_to_command_dry_run_plan_0184.py",
        "tests/rules/test_route_request_to_command_dry_run_plan_0184_rule.py",
        "doc/architecture/ROUTE_REQUEST_TO_COMMAND_DRY_RUN_PLAN_0184.md",
        "doc/code-rules/0184_route_request_to_command_dry_run_plan_rule.md",
    ]:
        assert token in manifest
