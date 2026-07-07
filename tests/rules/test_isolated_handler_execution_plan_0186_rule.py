from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_isolated_handler_execution_plan.py"
DOC = ROOT / "doc" / "architecture" / "ISOLATED_HANDLER_EXECUTION_PLAN_0186.md"
RULE = ROOT / "doc" / "code-rules" / "0186_isolated_handler_execution_plan_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0186_CHANGED_FILES.md"


def test_0186_tool_is_plan_only_and_does_not_execute_runtime() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0186 is a planning/audit tool only",
        "scheduler_route_handler_command_smoke.jsonl",
        "isolated_handler_execution_plan.jsonl",
        "RouteProxyRuntimePolicy",
        "It does not import runtime handler modules",
        "It does not import route_proxy_runtime_minimal",
        "It does not call handle_scheduler_route_command",
        "It does not call prepare_route_proxy_runtime",
        "It does not request writer permits",
        "It does not write RouteProxy or ControlProxy frames",
        "It does not modify Scheduler.run",
    ]:
        assert token in source
    assert "from runtime.scheduler_route_handler_minimal import" not in source
    assert "from runtime.route_proxy_runtime_minimal import" not in source
    assert "handle_scheduler_route_command(" not in source
    assert "prepare_route_proxy_runtime(" not in source
    assert "request_writer_permit(" not in source
    assert "write_route_frame(" not in source


def test_0186_doc_locks_isolated_execution_plan_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0186 plans isolated handler execution, but does not execute it",
        "The input is scheduler_route_handler_command_smoke.jsonl",
        "The output is isolated_handler_execution_plan.jsonl",
        "It resolves RouteProxyRuntimePolicy by AST only",
        "It does not call prepare_route_proxy_runtime",
        "It does not call handle_scheduler_route_command",
        "A future patch may execute the handler only inside the isolated runtime root",
    ]:
        assert token in doc


def test_0186_rule_blocks_routeproxy_preparation_and_frame_writes() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read scheduler_route_handler_command_smoke.jsonl from 0185",
        "Build only isolated_handler_execution_plan.jsonl",
        "Resolve RouteProxyRuntimePolicy by text/AST only",
        "Do not import route_proxy_runtime_minimal",
        "Do not call prepare_route_proxy_runtime",
        "Do not call handle_scheduler_route_command",
        "Do not request writer permits",
        "Do not write ControlProxy or RouteProxy frames",
    ]:
        assert token in rule


def test_0186_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--smoke" in source
    assert "--isolated-runtime-root" in source
    assert "--output" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0186_manifest_lists_isolated_plan_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/build_isolated_handler_execution_plan.py",
        "tests/tools/test_build_isolated_handler_execution_plan_0186.py",
        "tests/rules/test_isolated_handler_execution_plan_0186_rule.py",
        "doc/architecture/ISOLATED_HANDLER_EXECUTION_PLAN_0186.md",
        "doc/code-rules/0186_isolated_handler_execution_plan_rule.md",
    ]:
        assert token in manifest
