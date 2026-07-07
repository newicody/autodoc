from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "record_route_pipeline_bloc_a_coherence.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_PIPELINE_BLOC_A_COHERENCE_RECORD_0197.md"
RULE = ROOT / "doc" / "code-rules" / "0197_route_pipeline_bloc_a_coherence_record_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0197_CHANGED_FILES.md"


def test_0197_tool_is_coherence_record_only_and_reuses_existing_surfaces() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0197 is the Bloc A coherence record only",
        "isolated_route_pipeline_promotion_readiness_acceptance.json",
        "route_pipeline_bloc_a_coherence_record.json",
        "It must reuse the existing 0196 readiness acceptance artifact",
        "introduce a new runtime handler",
        "Execution locks are not permanent",
        "A later execution bloc may unlock execution explicitly",
        "policy_decision_id",
        "future_execution_can_be_unlocked",
        "execution_allowed_by_0197",
        "0198-controlled_dev_smoke_plan",
        "Every bloc must end with re-evaluation and coherence",
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


def test_0197_doc_locks_bloc_a_coherence_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0197 closes Bloc A with a coherence record and phase re-evaluation",
        "The input is isolated_route_pipeline_promotion_readiness_acceptance.json",
        "The output is route_pipeline_bloc_a_coherence_record.json",
        "Execution locks are phase gates, not permanent prohibitions",
        "Bloc B may unlock controlled dev execution explicitly",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "The next recommended patch is P0198 controlled dev smoke plan",
    ]:
        assert token in doc


def test_0197_rule_blocks_runtime_execution_but_allows_future_execution_bloc() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read isolated_route_pipeline_promotion_readiness_acceptance.json from 0196",
        "Close Bloc A as preparation only",
        "Do not execute controlled-dev-routeproxy-smoke in 0197",
        "Record that execution locks are not permanent",
        "Allow Bloc B to unlock execution explicitly when required",
        "Require policy_decision_id for any future execution unlock",
        "Do not add a new runtime handler",
        "Do not add a new adapter",
        "Do not add a new bus",
        "Do not import runtime handler modules",
        "Do not call handle_scheduler_route_command",
        "Do not call prepare_route_proxy_runtime",
        "Do not write ControlProxy or RouteProxy frames",
    ]:
        assert token in rule


def test_0197_manifest_lists_bloc_a_coherence_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/record_route_pipeline_bloc_a_coherence.py",
        "tests/tools/test_record_route_pipeline_bloc_a_coherence_0197.py",
        "tests/rules/test_route_pipeline_bloc_a_coherence_record_0197_rule.py",
        "doc/architecture/ROUTE_PIPELINE_BLOC_A_COHERENCE_RECORD_0197.md",
        "doc/code-rules/0197_route_pipeline_bloc_a_coherence_record_rule.md",
    ]:
        assert token in manifest
