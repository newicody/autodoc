from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_controlled_dev_routeproxy_smoke.py"
DOC = ROOT / "doc" / "architecture" / "CONTROLLED_DEV_ROUTE_PROXY_SMOKE_PLAN_0198.md"
RULE = ROOT / "doc" / "code-rules" / "0198_controlled_dev_routeproxy_smoke_plan_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0198_CHANGED_FILES.md"


def test_0198_tool_is_plan_only_and_reuses_existing_execution_surface() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0198 is the Bloc B controlled dev smoke plan only",
        "route_pipeline_bloc_a_coherence_record.json",
        "controlled_dev_routeproxy_smoke_plan.json",
        "It must reuse the existing 0197 Bloc A coherence artifact",
        "tools/run_isolated_route_pipeline_smoke.py",
        "introduce a new runtime handler",
        "Execution locks are phase gates, not permanent prohibitions",
        "P0199 may unlock controlled-dev-routeproxy-smoke explicitly",
        "P0198 itself does not execute controlled-dev-routeproxy-smoke",
        "execution_allowed_by_0198",
        "execution_can_be_unlocked_by_p0199",
        "0199-controlled_dev_routeproxy_smoke_execution",
        "policy_decision_id",
        "reuse tools/run_isolated_route_pipeline_smoke.py before adding new execution code",
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


def test_0198_doc_locks_controlled_dev_plan_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0198 opens Bloc B with a controlled dev RouteProxy smoke plan",
        "The input is route_pipeline_bloc_a_coherence_record.json",
        "The output is controlled_dev_routeproxy_smoke_plan.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "P0198 plans execution but keeps execution_allowed_by_0198 false",
        "P0199 may explicitly unlock controlled-dev-routeproxy-smoke",
        "The execution surface to reuse is tools/run_isolated_route_pipeline_smoke.py",
        "docs, graph, changelog, manifest, and rule are updated with the patch",
    ]:
        assert token in doc


def test_0198_rule_blocks_new_execution_surface() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read route_pipeline_bloc_a_coherence_record.json from 0197",
        "Reuse tools/run_isolated_route_pipeline_smoke.py",
        "Do not add a new runtime handler",
        "Do not add a new adapter",
        "Do not add a new bus",
        "Do not execute controlled-dev-routeproxy-smoke in 0198",
        "Keep execution_allowed_by_0198 false",
        "Allow P0199 to unlock controlled dev execution explicitly",
        "Require explicit policy_decision_id",
        "Do not import runtime handler modules",
        "Do not call handle_scheduler_route_command",
        "Do not call prepare_route_proxy_runtime",
        "Do not write ControlProxy or RouteProxy frames",
    ]:
        assert token in rule


def test_0198_manifest_lists_controlled_dev_plan_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/plan_controlled_dev_routeproxy_smoke.py",
        "tests/tools/test_plan_controlled_dev_routeproxy_smoke_0198.py",
        "tests/rules/test_controlled_dev_routeproxy_smoke_plan_0198_rule.py",
        "doc/architecture/CONTROLLED_DEV_ROUTE_PROXY_SMOKE_PLAN_0198.md",
        "doc/code-rules/0198_controlled_dev_routeproxy_smoke_plan_rule.md",
    ]:
        assert token in manifest
