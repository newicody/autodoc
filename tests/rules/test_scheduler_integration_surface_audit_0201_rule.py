from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_scheduler_integration_surfaces.py"
DOC = ROOT / "doc" / "architecture" / "SCHEDULER_INTEGRATION_SURFACE_AUDIT_0201.md"
RULE = ROOT / "doc" / "code-rules" / "0201_scheduler_integration_surface_audit_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0201_CHANGED_FILES.md"


def test_0201_tool_is_scheduler_surface_audit_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0201 is the Bloc C Scheduler integration surface audit only",
        "controlled_dev_routeproxy_smoke_post_execution_acceptance.json",
        "scheduler_integration_surface_audit.json",
        "Reuse/adapt existing surfaces first",
        "0201 must audit existing code before any Scheduler hook plan is allowed",
        "0201 must not introduce a new runtime handler",
        "0201 does not execute Scheduler.run",
        "0201 does not import runtime handler modules",
        "0201 does not call handle_scheduler_route_command",
        "0201 does not call handle_scheduler_route_request",
        "0201 does not call prepare_route_proxy_runtime",
        "0201 does not call read_route_frame",
        "0201 does not request writer permits",
        "0201 does not call write_route_frame",
        "0201 does not write ControlProxy or RouteProxy frames",
        "0201 does not call GitHub API or use network",
        "src/runtime/scheduler_route_adapter.py",
        "src/runtime/scheduler_route_handler_minimal.py",
        "src/runtime/scheduler_route_handshake.py",
        "src/runtime/controlproxy_scheduler_handler.py",
        "source_baseline_ref or source_entry_digest missing",
        "0202-scheduler_hook_dry_run_plan",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0201_doc_locks_scheduler_surface_audit_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0201 opens Bloc C with a Scheduler integration surface audit",
        "The input is controlled_dev_routeproxy_smoke_post_execution_acceptance.json",
        "The output is scheduler_integration_surface_audit.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0201 does not hook Scheduler.run",
        "0201 audits existing code before P0202 may plan a hook",
        "The provenance gap from P0200 is kept as a repair item",
        "docs, graph, changelog, manifest, and rule are updated with the patch",
    ]:
        assert token in doc


def test_0201_rule_requires_existing_surface_audit() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read controlled_dev_routeproxy_smoke_post_execution_acceptance.json from 0200",
        "Audit existing Scheduler integration surfaces before planning a hook",
        "Reuse scheduler_route_adapter.py",
        "Reuse scheduler_route_handler_minimal.py",
        "Reuse scheduler_route_handshake.py",
        "Reuse controlproxy_scheduler_handler.py only as an existing surface candidate",
        "Do not add a new runtime handler",
        "Do not add a new adapter",
        "Do not add a new bus",
        "Do not execute Scheduler.run in 0201",
        "Do not write ControlProxy or RouteProxy frames",
        "Preserve missing source_baseline_ref or source_entry_digest as a provenance repair item",
    ]:
        assert token in rule


def test_0201_manifest_lists_surface_audit_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/audit_scheduler_integration_surfaces.py",
        "tests/tools/test_audit_scheduler_integration_surfaces_0201.py",
        "tests/rules/test_scheduler_integration_surface_audit_0201_rule.py",
        "doc/architecture/SCHEDULER_INTEGRATION_SURFACE_AUDIT_0201.md",
        "doc/code-rules/0201_scheduler_integration_surface_audit_rule.md",
    ]:
        assert token in manifest
