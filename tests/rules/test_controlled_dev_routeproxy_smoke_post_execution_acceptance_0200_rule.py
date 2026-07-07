from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "accept_controlled_dev_routeproxy_smoke_post_execution.py"
DOC = ROOT / "doc" / "architecture" / "CONTROLLED_DEV_ROUTE_PROXY_SMOKE_POST_EXECUTION_ACCEPTANCE_0200.md"
RULE = ROOT / "doc" / "code-rules" / "0200_controlled_dev_routeproxy_smoke_post_execution_acceptance_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0200_CHANGED_FILES.md"


def test_0200_tool_is_post_execution_acceptance_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0200 is the Bloc B post-execution audit, acceptance, registry, and coherence",
        "controlled_dev_routeproxy_smoke_execution.json",
        "controlled_dev_routeproxy_smoke_post_execution_acceptance.json",
        "controlled_dev_routeproxy_smoke_registry.jsonl",
        "It must reuse the existing 0199 execution report and existing pipeline artifacts",
        "introduce a new runtime handler",
        "0200 does not execute controlled-dev-routeproxy-smoke",
        "0200 does not import runtime handler modules",
        "0200 does not call handle_scheduler_route_command",
        "0200 does not call prepare_route_proxy_runtime",
        "0200 does not call read_route_frame",
        "0200 does not request writer permits",
        "0200 does not call write_route_frame",
        "0200 does not modify Scheduler.run",
        "0200 does not instantiate Scheduler",
        "0200 does not instantiate EventBus",
        "0200 does not write ControlProxy or RouteProxy frames",
        "0200 does not call GitHub API or use network",
        "controlled-dev-routeproxy-write-read-v1",
        "0201-scheduler_integration_surface_audit",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0200_doc_locks_bloc_b_acceptance_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0200 closes Bloc B with post-execution audit, acceptance, registry, and coherence",
        "The input is controlled_dev_routeproxy_smoke_execution.json",
        "The output is controlled_dev_routeproxy_smoke_post_execution_acceptance.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0200 does not execute controlled-dev-routeproxy-smoke",
        "Bloc B is complete only when the execution is accepted",
        "The next recommended patch is P0201 scheduler integration surface audit",
        "docs, graph, changelog, manifest, and rule are updated with the patch",
    ]:
        assert token in doc


def test_0200_rule_requires_post_execution_acceptance() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read controlled_dev_routeproxy_smoke_execution.json from 0199",
        "Reuse existing pipeline artifacts from P0199",
        "Do not execute controlled-dev-routeproxy-smoke in 0200",
        "Do not add a new runtime handler",
        "Do not add a new adapter",
        "Do not add a new bus",
        "Require execution_success true",
        "Require pipeline_success true",
        "Require frames_written_count 1",
        "Require readback_count 1",
        "Require ControlProxy frames false",
        "Require Scheduler modified false",
        "Require network used false",
        "Append controlled_dev_routeproxy_smoke_registry.jsonl when requested",
        "Open Bloc C only after acceptance",
    ]:
        assert token in rule


def test_0200_manifest_lists_acceptance_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/accept_controlled_dev_routeproxy_smoke_post_execution.py",
        "tests/tools/test_accept_controlled_dev_routeproxy_smoke_post_execution_0200.py",
        "tests/rules/test_controlled_dev_routeproxy_smoke_post_execution_acceptance_0200_rule.py",
        "doc/architecture/CONTROLLED_DEV_ROUTE_PROXY_SMOKE_POST_EXECUTION_ACCEPTANCE_0200.md",
        "doc/code-rules/0200_controlled_dev_routeproxy_smoke_post_execution_acceptance_rule.md",
    ]:
        assert token in manifest
