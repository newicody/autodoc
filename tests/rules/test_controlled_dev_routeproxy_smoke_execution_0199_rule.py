from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_controlled_dev_routeproxy_smoke.py"
DOC = ROOT / "doc" / "architecture" / "CONTROLLED_DEV_ROUTE_PROXY_SMOKE_EXECUTION_0199.md"
RULE = ROOT / "doc" / "code-rules" / "0199_controlled_dev_routeproxy_smoke_execution_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0199_CHANGED_FILES.md"


def test_0199_tool_executes_only_existing_pipeline_surface() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0199 is the Bloc B controlled dev RouteProxy smoke execution patch",
        "controlled_dev_routeproxy_smoke_plan.json",
        "controlled_dev_routeproxy_smoke_execution.json",
        "tools/run_isolated_route_pipeline_smoke.py",
        "Execution locks are phase gates, not permanent prohibitions",
        "P0199 explicitly unlocks controlled-dev-routeproxy-smoke execution",
        "It must reuse the existing 0198 plan artifact",
        "It must not",
        "introduce a new runtime handler",
        "execution_unlocked_by_p0199",
        "execution_allowed_by_0199",
        "requires_p0200_post_execution_audit",
        "write RouteProxy frames only under target_isolated_runtime_root",
        "P0199 does not import runtime handler modules directly",
        "P0199 does not modify Scheduler.run",
        "P0199 does not write ControlProxy frames",
        "P0199 does not call GitHub API or use network",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0199_doc_locks_execution_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0199 executes the controlled dev RouteProxy smoke by reusing the existing pipeline tool",
        "The input is controlled_dev_routeproxy_smoke_plan.json",
        "The output is controlled_dev_routeproxy_smoke_execution.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "P0199 explicitly unlocks execution",
        "The execution surface reused is tools/run_isolated_route_pipeline_smoke.py",
        "P0200 must perform post-execution audit and acceptance",
        "docs, graph, changelog, manifest, and rule are updated with the patch",
    ]:
        assert token in doc


def test_0199_rule_requires_reuse_and_followup_audit() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read controlled_dev_routeproxy_smoke_plan.json from 0198",
        "Reuse tools/run_isolated_route_pipeline_smoke.py",
        "Do not add a new runtime handler",
        "Do not add a new adapter",
        "Do not add a new bus",
        "Allow controlled-dev-routeproxy-smoke execution in 0199",
        "Require explicit policy_decision_id",
        "Write RouteProxy frames only under target_isolated_runtime_root",
        "Do not write ControlProxy frames",
        "Do not modify Scheduler.run",
        "Require P0200 post-execution audit",
        "Require P0200 post-audit acceptance",
    ]:
        assert token in rule


def test_0199_manifest_lists_execution_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/run_controlled_dev_routeproxy_smoke.py",
        "tests/tools/test_run_controlled_dev_routeproxy_smoke_0199.py",
        "tests/rules/test_controlled_dev_routeproxy_smoke_execution_0199_rule.py",
        "doc/architecture/CONTROLLED_DEV_ROUTE_PROXY_SMOKE_EXECUTION_0199.md",
        "doc/code-rules/0199_controlled_dev_routeproxy_smoke_execution_rule.md",
    ]:
        assert token in manifest
