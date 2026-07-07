from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_route_handler_surfaces.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_HANDLER_SURFACE_AUDIT_0181.md"
RULE = ROOT / "doc" / "code-rules" / "0181_route_handler_surface_audit_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0181_CHANGED_FILES.md"


def test_0181_tool_is_read_only_ast_audit() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0181 is an audit tool only",
        "reads Python files as text/AST",
        "does not import runtime handler modules",
        "does not call handle_scheduler_route_request",
        "does not instantiate Scheduler",
        "does not modify Scheduler.run",
        "does not instantiate EventBus",
        "does not write RouteProxy or ControlProxy frames",
        "ast.parse",
        "Path.read_text",
    ]:
        assert token in source
    assert "handle_scheduler_route_request(" not in source
    assert "from runtime.scheduler_route_handler_minimal import" not in source
    assert "from kernel.scheduler import Scheduler" not in source
    assert "from kernel.event_bus import EventBus" not in source


def test_0181_doc_locks_audit_before_execution() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0181 audits existing route handler surfaces before execution",
        "It does not execute the route handler",
        "It does not import handler modules",
        "It reads files as text and AST only",
        "0181 must run before any patch attempts a real handler handoff",
        "Scheduler/policy/zone remain the authority",
    ]:
        assert token in doc


def test_0181_rule_blocks_new_handler_or_runtime_bypass() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Audit existing route handler surfaces before adding or changing handler code",
        "Do not add a new runtime handler in 0181",
        "Do not import handler modules for execution",
        "Do not call handle_scheduler_route_request",
        "Do not modify Scheduler.run",
        "Do not instantiate EventBus",
        "Do not write ControlProxy or RouteProxy frames",
    ]:
        assert token in rule


def test_0181_manifest_lists_audit_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/audit_route_handler_surfaces.py",
        "tests/tools/test_audit_route_handler_surfaces_0181.py",
        "tests/rules/test_route_handler_surface_audit_0181_rule.py",
        "doc/architecture/ROUTE_HANDLER_SURFACE_AUDIT_0181.md",
        "doc/code-rules/0181_route_handler_surface_audit_rule.md",
    ]:
        assert token in manifest
