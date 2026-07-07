from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "resolve_route_handler_surfaces.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_HANDLER_SURFACE_RESOLVER_0183.md"
RULE = ROOT / "doc" / "code-rules" / "0183_route_handler_surface_resolver_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0183_CHANGED_FILES.md"


def test_0183_tool_resolves_real_surfaces_without_execution() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0183 is a resolver/audit tool only",
        "scheduler adapter request surface",
        "scheduler route command handler surface",
        "handle_scheduler_route_command",
        "build_single_frame_route_command",
        "It does not import runtime handler modules",
        "It does not call handle_scheduler_route_request",
        "It does not call handle_scheduler_route_command",
        "It does not modify Scheduler.run",
        "It does not instantiate Scheduler",
        "It does not instantiate EventBus",
        "It does not write RouteProxy or ControlProxy frames",
        "ast.parse",
    ]:
        assert token in source
    assert "handle_scheduler_route_request(" not in source
    assert "handle_scheduler_route_command(" not in source
    assert "from runtime.scheduler_route_handler_minimal import" not in source
    assert "from runtime.scheduler_route_adapter import" not in source


def test_0183_doc_locks_resolver_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0183 resolves the real route handler surfaces, not guessed symbols",
        "The real minimal handler surface is handle_scheduler_route_command",
        "The adapter request surface is handle_scheduler_route_request",
        "0183 does not execute either surface",
        "A future patch must consume this resolver report before any handler call",
        "Scheduler/policy/zone remain the authority",
    ]:
        assert token in doc


def test_0183_rule_blocks_execution_and_parallel_handler() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Resolve existing route handler surfaces before execution",
        "Prefer handle_scheduler_route_command when available",
        "Do not add a new runtime handler in 0183",
        "Do not import runtime handler modules",
        "Do not call handle_scheduler_route_request",
        "Do not call handle_scheduler_route_command",
        "Do not modify Scheduler.run",
        "Do not write ControlProxy or RouteProxy frames",
    ]:
        assert token in rule


def test_0183_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--repo-root" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0183_manifest_lists_resolver_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/resolve_route_handler_surfaces.py",
        "tests/tools/test_resolve_route_handler_surfaces_0183.py",
        "tests/rules/test_route_handler_surface_resolver_0183_rule.py",
        "doc/architecture/ROUTE_HANDLER_SURFACE_RESOLVER_0183.md",
        "doc/code-rules/0183_route_handler_surface_resolver_rule.md",
    ]:
        assert token in manifest
