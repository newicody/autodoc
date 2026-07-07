from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "github_artifact_scheduler_intake.py"
TOOL = ROOT / "tools" / "build_github_artifact_scheduler_intake.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_ARTIFACT_SCHEDULER_INTAKE_CONTRACT_0177.md"
RULE = ROOT / "doc" / "code-rules" / "0177_github_artifact_scheduler_intake_contract_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0177_CHANGED_FILES.md"


def test_0177_module_reuses_existing_scheduler_route_adapter() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for token in [
        "from runtime.scheduler_route_adapter import",
        "scheduler_route_request_mapping",
        "SCHEDULER_ROUTE_REQUEST_SCHEMA",
        "A candidate is not authorized work",
        "policy_decision_id",
        "This module does not call handle_scheduler_route_request",
        "without modifying Scheduler.run()",
        "without bypassing policy",
    ]:
        assert token in source
    assert "handle_scheduler_route_request(" not in source
    assert "from kernel.scheduler import Scheduler" not in source
    assert "from kernel.event_bus import EventBus" not in source


def test_0177_doc_locks_scheduler_intake_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0177 is a scheduler intake contract, not a Scheduler implementation",
        "It reuses scheduler_route_request_mapping",
        "It does not call handle_scheduler_route_request",
        "It does not modify Scheduler.run()",
        "A candidate is not authorized work",
        "A SchedulerRouteRequest is emitted only with an explicit policy_decision_id",
        "Scheduler/policy/zone remain the authority",
    ]:
        assert token in doc


def test_0177_rule_blocks_scheduler_bypass() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Reuse runtime.scheduler_route_adapter.scheduler_route_request_mapping",
        "Do not call handle_scheduler_route_request",
        "Do not modify Scheduler.run()",
        "Do not instantiate Scheduler",
        "Do not instantiate EventBus",
        "Do not bypass Scheduler/policy/zone",
        "Do not emit authorized SchedulerRouteRequest without policy_decision_id",
    ]:
        assert token in rule


def test_0177_tool_is_local_builder_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--policy-decision-id" in source
    assert "--authorized" in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "handle_scheduler_route_request" not in source


def test_0177_manifest_lists_intake_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "src/context/github_artifact_scheduler_intake.py",
        "tools/build_github_artifact_scheduler_intake.py",
        "tests/context/test_github_artifact_scheduler_intake_0177.py",
        "tests/tools/test_build_github_artifact_scheduler_intake_0177.py",
        "tests/rules/test_github_artifact_scheduler_intake_contract_0177_rule.py",
    ]:
        assert token in manifest
