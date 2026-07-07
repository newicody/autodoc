from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "accept_isolated_route_pipeline_promotion_readiness.py"
DOC = ROOT / "doc" / "architecture" / "ISOLATED_ROUTE_PIPELINE_PROMOTION_READINESS_ACCEPTANCE_0196.md"
RULE = ROOT / "doc" / "code-rules" / "0196_isolated_route_pipeline_promotion_readiness_acceptance_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0196_CHANGED_FILES.md"


def test_0196_tool_is_acceptance_only_and_reuses_existing_surfaces() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0196 is a promotion readiness acceptance gate only",
        "isolated_route_pipeline_promotion_plan_audit.json",
        "isolated_route_pipeline_promotion_readiness_acceptance.json",
        "It must reuse the existing 0195 promotion plan audit artifact",
        "It must not",
        "introduce a new runtime handler",
        "new_adapter_added",
        "new_bus_added",
        "new_sql_backend_added",
        "new_qdrant_backend_added",
        "new_github_client_added",
        "controlled-dev-routeproxy-smoke",
        "execution_allowed_by_0196",
        "0197-bloc_a_coherence_record",
        "phase_re_evaluation_required_before_execution",
        "It does not execute controlled-dev-routeproxy-smoke",
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


def test_0196_doc_locks_readiness_acceptance_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0196 accepts the clean 0195 promotion plan audit as ready for a later controlled dev smoke",
        "The input is isolated_route_pipeline_promotion_plan_audit.json",
        "The output is isolated_route_pipeline_promotion_readiness_acceptance.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "It accepts readiness but keeps execution_allowed_by_0196 false",
        "It does not execute controlled-dev-routeproxy-smoke",
        "It does not call runtime APIs",
        "The next required patch is P0197 Bloc A coherence record",
    ]:
        assert token in doc


def test_0196_rule_blocks_runtime_execution() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read isolated_route_pipeline_promotion_plan_audit.json from 0195",
        "Reuse the existing 0195 promotion plan audit artifact",
        "Do not add a new runtime handler",
        "Do not add a new adapter",
        "Do not add a new bus",
        "Do not add a new SQL backend",
        "Do not add a new Qdrant backend",
        "Do not execute controlled-dev-routeproxy-smoke",
        "Keep execution_allowed_by_0196 false",
        "Require phase re-evaluation before execution",
        "Do not import runtime handler modules",
        "Do not call handle_scheduler_route_command",
        "Do not call prepare_route_proxy_runtime",
        "Do not write ControlProxy or RouteProxy frames",
    ]:
        assert token in rule


def test_0196_manifest_lists_readiness_acceptance_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/accept_isolated_route_pipeline_promotion_readiness.py",
        "tests/tools/test_accept_isolated_route_pipeline_promotion_readiness_0196.py",
        "tests/rules/test_isolated_route_pipeline_promotion_readiness_acceptance_0196_rule.py",
        "doc/architecture/ISOLATED_ROUTE_PIPELINE_PROMOTION_READINESS_ACCEPTANCE_0196.md",
        "doc/code-rules/0196_isolated_route_pipeline_promotion_readiness_acceptance_rule.md",
    ]:
        assert token in manifest
