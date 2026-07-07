from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "register_isolated_route_pipeline_baseline.py"
DOC = ROOT / "doc" / "architecture" / "ISOLATED_ROUTE_PIPELINE_BASELINE_REGISTRY_0193.md"
RULE = ROOT / "doc" / "code-rules" / "0193_isolated_route_pipeline_baseline_registry_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0193_CHANGED_FILES.md"


def test_0193_tool_is_baseline_registry_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0193 is a baseline registry tool only",
        "isolated_route_pipeline_acceptance.json",
        "isolated_route_pipeline_baseline_registry.jsonl",
        "accepted isolated prototypes",
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


def test_0193_doc_locks_registry_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0193 registers the accepted isolated route pipeline baseline",
        "The input is isolated_route_pipeline_acceptance.json",
        "The output is isolated_route_pipeline_baseline_registry.jsonl",
        "It registers isolated-route-pipeline-write-read-v1",
        "It does not rerun the pipeline",
        "It does not call runtime APIs",
        "This is the baseline registry for accepted isolated prototypes",
    ]:
        assert token in doc


def test_0193_rule_blocks_runtime_execution() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read isolated_route_pipeline_acceptance.json from 0192",
        "Register only when acceptance_approved is true",
        "Write only isolated_route_pipeline_baseline_registry.jsonl",
        "Do not import runtime handler modules",
        "Do not call handle_scheduler_route_command",
        "Do not call prepare_route_proxy_runtime",
        "Do not call read_route_frame",
        "Do not write ControlProxy or RouteProxy frames",
        "Do not write SQL",
        "Do not write Qdrant",
    ]:
        assert token in rule


def test_0193_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--acceptance" in source
    assert "--output" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0193_manifest_lists_registry_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/register_isolated_route_pipeline_baseline.py",
        "tests/tools/test_register_isolated_route_pipeline_baseline_0193.py",
        "tests/rules/test_isolated_route_pipeline_baseline_registry_0193_rule.py",
        "doc/architecture/ISOLATED_ROUTE_PIPELINE_BASELINE_REGISTRY_0193.md",
        "doc/code-rules/0193_isolated_route_pipeline_baseline_registry_rule.md",
    ]:
        assert token in manifest
