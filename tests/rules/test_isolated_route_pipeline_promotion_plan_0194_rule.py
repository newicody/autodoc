from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_isolated_route_pipeline_promotion.py"
DOC = ROOT / "doc" / "architecture" / "ISOLATED_ROUTE_PIPELINE_PROMOTION_PLAN_0194.md"
RULE = ROOT / "doc" / "code-rules" / "0194_isolated_route_pipeline_promotion_plan_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0194_CHANGED_FILES.md"


def test_0194_tool_is_promotion_plan_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0194 is a promotion planning tool only",
        "isolated_route_pipeline_baseline_registry.jsonl",
        "isolated_route_pipeline_promotion_plan.json",
        "controlled-dev-routeproxy-smoke",
        "promotion_allowed_by_0194",
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


def test_0194_doc_locks_promotion_plan_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0194 plans the next promotion step from the accepted isolated baseline",
        "The input is isolated_route_pipeline_baseline_registry.jsonl",
        "The output is isolated_route_pipeline_promotion_plan.json",
        "It plans controlled-dev-routeproxy-smoke",
        "It does not execute the promotion",
        "It does not call runtime APIs",
        "0194 is not a production promotion",
    ]:
        assert token in doc


def test_0194_rule_blocks_runtime_execution() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read isolated_route_pipeline_baseline_registry.jsonl from 0193",
        "Plan only controlled-dev-routeproxy-smoke",
        "Do not execute the promotion",
        "Do not import runtime handler modules",
        "Do not call handle_scheduler_route_command",
        "Do not call prepare_route_proxy_runtime",
        "Do not call read_route_frame",
        "Do not write ControlProxy or RouteProxy frames",
        "Do not write SQL",
        "Do not write Qdrant",
    ]:
        assert token in rule


def test_0194_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--registry" in source
    assert "--target-runtime-root" in source
    assert "--target-isolated-runtime-root" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0194_manifest_lists_promotion_plan_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/plan_isolated_route_pipeline_promotion.py",
        "tests/tools/test_plan_isolated_route_pipeline_promotion_0194.py",
        "tests/rules/test_isolated_route_pipeline_promotion_plan_0194_rule.py",
        "doc/architecture/ISOLATED_ROUTE_PIPELINE_PROMOTION_PLAN_0194.md",
        "doc/code-rules/0194_isolated_route_pipeline_promotion_plan_rule.md",
    ]:
        assert token in manifest
