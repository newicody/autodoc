from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_scheduler_route_handler_command_smoke.py"
DOC = ROOT / "doc" / "architecture" / "SCHEDULER_ROUTE_HANDLER_COMMAND_BUILDER_SMOKE_0185.md"
RULE = ROOT / "doc" / "code-rules" / "0185_scheduler_route_handler_command_builder_smoke_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0185_CHANGED_FILES.md"


def test_0185_tool_imports_only_builder_surface_and_never_handler() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0185 is a command-builder smoke only",
        "route_request_to_command_dry_run_plan.jsonl",
        "scheduler_route_handler_command_smoke.jsonl",
        "build_single_frame_route_command",
        "SchedulerRouteHandlerCommand",
        "It does not call handle_scheduler_route_command",
        "It does not call handle_scheduler_route_request",
        "It does not prepare RouteProxyRuntime",
        "It does not write RouteProxy or ControlProxy frames",
        "builder_called",
        "handler_called",
    ]:
        assert token in source
    assert "handle_scheduler_route_command(" not in source
    assert "handle_scheduler_route_request(" not in source
    assert "prepare_route_proxy_runtime(" not in source
    assert "write_route_frame(" not in source
    assert "request_writer_permit(" not in source


def test_0185_doc_locks_builder_smoke_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0185 calls the existing command builder, not the route handler",
        "The input is route_request_to_command_dry_run_plan.jsonl",
        "The output is scheduler_route_handler_command_smoke.jsonl",
        "It may import build_single_frame_route_command",
        "It must not call handle_scheduler_route_command",
        "It must not prepare RouteProxyRuntime",
        "A future patch may execute the handler only after this smoke is reviewed",
    ]:
        assert token in doc


def test_0185_rule_blocks_handler_execution_and_frame_writes() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read route_request_to_command_dry_run_plan.jsonl from 0184",
        "Call only build_single_frame_route_command",
        "Do not call handle_scheduler_route_command",
        "Do not call handle_scheduler_route_request",
        "Do not prepare RouteProxyRuntime",
        "Do not write ControlProxy or RouteProxy frames",
        "Do not modify Scheduler.run",
        "Do not instantiate EventBus",
    ]:
        assert token in rule


def test_0185_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--plan" in source
    assert "--output" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0185_manifest_lists_builder_smoke_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/build_scheduler_route_handler_command_smoke.py",
        "tests/tools/test_build_scheduler_route_handler_command_smoke_0185.py",
        "tests/rules/test_scheduler_route_handler_command_builder_smoke_0185_rule.py",
        "doc/architecture/SCHEDULER_ROUTE_HANDLER_COMMAND_BUILDER_SMOKE_0185.md",
        "doc/code-rules/0185_scheduler_route_handler_command_builder_smoke_rule.md",
    ]:
        assert token in manifest
