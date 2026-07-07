from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_isolated_route_pipeline_promotion_plan.py"
DOC = ROOT / "doc" / "architecture" / "ISOLATED_ROUTE_PIPELINE_PROMOTION_PLAN_AUDIT_0195.md"
RULE = ROOT / "doc" / "code-rules" / "0195_isolated_route_pipeline_promotion_plan_audit_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0195_CHANGED_FILES.md"


def test_0195_tool_is_audit_only_and_reuses_existing_surfaces() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0195 is a promotion plan audit tool only",
        "isolated_route_pipeline_promotion_plan.json",
        "isolated_route_pipeline_promotion_plan_audit.json",
        "It must reuse the existing 0194 promotion plan artifact",
        "It must not introduce a new runtime handler",
        "new_adapter_added",
        "new_bus_added",
        "new_sql_backend_added",
        "new_qdrant_backend_added",
        "new_github_client_added",
        "controlled-dev-routeproxy-smoke",
        "promotion_allowed_by_0194 must remain false",
        "dev-smoke-run must reuse tools/run_isolated_route_pipeline_smoke.py",
        "It does not execute the promotion",
        "It does not import runtime handler modules",
        "It does not call handle_scheduler_route_command",
        "It does not call prepare_route_proxy_runtime",
        "It does not call read_route_frame",
        "It does not request writer permits",
        "It does not call write_route_frame",
        "It does not modify Scheduler.run",
        "It does not instantiate Scheduler",
        "It does not instantiate EventBus",
        "It does not write ControlProxy or RouteProxy frames",
        "It does not call GitHub API or use network",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "handle_scheduler_route_command(" not in source
    assert "prepare_route_proxy_runtime(" not in source
    assert "read_route_frame(" not in source
    assert "write_route_frame(" not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0195_doc_locks_plan_audit_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0195 audits the 0194 promotion plan before any controlled dev smoke is executed",
        "The input is isolated_route_pipeline_promotion_plan.json",
        "The output is isolated_route_pipeline_promotion_plan_audit.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "It verifies promotion_allowed_by_0194 remains false",
        "It does not execute the promotion",
        "It does not call runtime APIs",
        "docs, graph, changelog, manifest, and rule are updated with the patch",
    ]:
        assert token in doc


def test_0195_rule_blocks_new_runtime_surfaces() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read isolated_route_pipeline_promotion_plan.json from 0194",
        "Reuse the existing 0194 promotion plan artifact",
        "Do not add a new runtime handler",
        "Do not add a new adapter",
        "Do not add a new bus",
        "Do not add a new SQL backend",
        "Do not add a new Qdrant backend",
        "Do not execute controlled-dev-routeproxy-smoke",
        "Do not import runtime handler modules",
        "Do not call handle_scheduler_route_command",
        "Do not call prepare_route_proxy_runtime",
        "Do not write ControlProxy or RouteProxy frames",
    ]:
        assert token in rule


def test_0195_manifest_lists_promotion_plan_audit_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/audit_isolated_route_pipeline_promotion_plan.py",
        "tests/tools/test_audit_isolated_route_pipeline_promotion_plan_0195.py",
        "tests/rules/test_isolated_route_pipeline_promotion_plan_audit_0195_rule.py",
        "doc/architecture/ISOLATED_ROUTE_PIPELINE_PROMOTION_PLAN_AUDIT_0195.md",
        "doc/code-rules/0195_isolated_route_pipeline_promotion_plan_audit_rule.md",
    ]:
        assert token in manifest
