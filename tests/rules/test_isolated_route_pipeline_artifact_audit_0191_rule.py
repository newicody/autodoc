from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_isolated_route_pipeline_artifacts.py"
DOC = ROOT / "doc" / "architecture" / "ISOLATED_ROUTE_PIPELINE_ARTIFACT_AUDIT_0191.md"
RULE = ROOT / "doc" / "code-rules" / "0191_isolated_route_pipeline_artifact_audit_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0191_CHANGED_FILES.md"


def test_0191_tool_is_artifact_audit_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0191 is an artifact audit tool only",
        "isolated_route_pipeline_smoke.json",
        "isolated_route_pipeline_artifact_audit.json",
        "0184 must read policy_scoped_queue",
        "policy_scoped_queued_count",
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


def test_0191_doc_locks_artifact_audit_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0191 audits the isolated route pipeline artifacts without executing the pipeline",
        "The input is isolated_route_pipeline_smoke.json",
        "The output is isolated_route_pipeline_artifact_audit.json",
        "It verifies 0184 read scheduler.route_requests.policy_scoped.jsonl",
        "It does not call the handler",
        "It does not read RouteProxy frames through runtime APIs",
        "This is the baseline acceptance audit for the isolated prototype",
    ]:
        assert token in doc


def test_0191_rule_blocks_runtime_execution() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read isolated_route_pipeline_smoke.json from 0190",
        "Validate artifact files and counters only",
        "Do not import runtime handler modules",
        "Do not call handle_scheduler_route_command",
        "Do not call prepare_route_proxy_runtime",
        "Do not call read_route_frame",
        "Do not request writer permits",
        "Do not call write_route_frame",
        "Do not write ControlProxy or RouteProxy frames",
        "Do not write SQL",
        "Do not write Qdrant",
    ]:
        assert token in rule


def test_0191_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--pipeline-report" in source
    assert "--output" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0191_manifest_lists_artifact_audit_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/audit_isolated_route_pipeline_artifacts.py",
        "tests/tools/test_audit_isolated_route_pipeline_artifacts_0191.py",
        "tests/rules/test_isolated_route_pipeline_artifact_audit_0191_rule.py",
        "doc/architecture/ISOLATED_ROUTE_PIPELINE_ARTIFACT_AUDIT_0191.md",
        "doc/code-rules/0191_isolated_route_pipeline_artifact_audit_rule.md",
    ]:
        assert token in manifest
