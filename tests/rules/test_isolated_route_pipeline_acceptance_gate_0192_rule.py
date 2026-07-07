from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "assert_isolated_route_pipeline_acceptance.py"
DOC = ROOT / "doc" / "architecture" / "ISOLATED_ROUTE_PIPELINE_ACCEPTANCE_GATE_0192.md"
RULE = ROOT / "doc" / "code-rules" / "0192_isolated_route_pipeline_acceptance_gate_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0192_CHANGED_FILES.md"


def test_0192_tool_is_acceptance_gate_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0192 is an acceptance gate only",
        "isolated_route_pipeline_artifact_audit.json",
        "isolated_route_pipeline_acceptance.json",
        "accepted_baseline",
        "isolated-route-pipeline-write-read-v1",
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


def test_0192_doc_locks_acceptance_gate_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0192 accepts or rejects the isolated route pipeline baseline",
        "The input is isolated_route_pipeline_artifact_audit.json",
        "The output is isolated_route_pipeline_acceptance.json",
        "It accepts isolated-route-pipeline-write-read-v1",
        "It does not rerun the pipeline",
        "It does not call runtime APIs",
        "This is the CI-style gate for the first isolated prototype",
    ]:
        assert token in doc


def test_0192_rule_blocks_runtime_execution() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read isolated_route_pipeline_artifact_audit.json from 0191",
        "Approve only when audit_success is true and issues are empty",
        "Approve only when policy_scoped_queued_count matches downstream counts",
        "Do not import runtime handler modules",
        "Do not call handle_scheduler_route_command",
        "Do not call prepare_route_proxy_runtime",
        "Do not call read_route_frame",
        "Do not write ControlProxy or RouteProxy frames",
        "Do not write SQL",
        "Do not write Qdrant",
    ]:
        assert token in rule


def test_0192_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--audit" in source
    assert "--output" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0192_manifest_lists_acceptance_gate_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/assert_isolated_route_pipeline_acceptance.py",
        "tests/tools/test_assert_isolated_route_pipeline_acceptance_0192.py",
        "tests/rules/test_isolated_route_pipeline_acceptance_gate_0192_rule.py",
        "doc/architecture/ISOLATED_ROUTE_PIPELINE_ACCEPTANCE_GATE_0192.md",
        "doc/code-rules/0192_isolated_route_pipeline_acceptance_gate_rule.md",
    ]:
        assert token in manifest
