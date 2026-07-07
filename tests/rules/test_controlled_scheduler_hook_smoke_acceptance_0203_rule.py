from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_controlled_scheduler_hook_smoke_acceptance.py"
DOC = ROOT / "doc" / "architecture" / "CONTROLLED_SCHEDULER_HOOK_SMOKE_ACCEPTANCE_0203.md"
RULE = ROOT / "doc" / "code-rules" / "0203_controlled_scheduler_hook_smoke_acceptance_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0203_CHANGED_FILES.md"


def test_0203_tool_executes_controlled_hook_smoke_without_scheduler_run() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0203 is the Bloc C controlled Scheduler hook smoke and acceptance patch",
        "scheduler_hook_dry_run_plan.json",
        "controlled_scheduler_hook_smoke_acceptance.json",
        "tools/run_isolated_route_pipeline_smoke.py",
        "Reuse/adapt existing surfaces first",
        "0203 explicitly unlocks controlled Scheduler hook smoke execution",
        "0203 must not add a new Scheduler hook implementation",
        "0203 must not introduce a new runtime handler",
        "0203 does not execute Scheduler.run",
        "0203 does not modify Scheduler.run",
        "0203 does not import runtime handler modules directly",
        "0203 does not write ControlProxy frames",
        "0203 does not call GitHub API or use network",
        "0203 requires RouteProxy writes to stay inside target_isolated_runtime_root",
        "controlled-scheduler-hook-routeproxy-write-read-v1",
        "0204-controlproxy_contract_audit",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0203_doc_locks_controlled_scheduler_hook_smoke_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0203 closes Bloc C with a controlled Scheduler hook smoke and acceptance",
        "The input is scheduler_hook_dry_run_plan.json",
        "The output is controlled_scheduler_hook_smoke_acceptance.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0203 unlocks controlled Scheduler hook smoke execution",
        "0203 still does not execute Scheduler.run",
        "The execution surface reused is tools/run_isolated_route_pipeline_smoke.py",
        "The next recommended patch is P0204 ControlProxy contract audit",
    ]:
        assert token in doc


def test_0203_rule_requires_controlled_hook_smoke_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read scheduler_hook_dry_run_plan.json from 0202",
        "Reuse tools/run_isolated_route_pipeline_smoke.py",
        "Allow controlled Scheduler hook smoke execution in 0203",
        "Do not execute Scheduler.run in 0203",
        "Do not modify Scheduler.run in 0203",
        "Do not add a new Scheduler hook implementation",
        "Do not add a new runtime handler",
        "Require explicit policy_decision_id",
        "Require RouteProxy writes to stay inside target_isolated_runtime_root",
        "Require ControlProxy frames false",
        "Require Scheduler modified false",
        "Open Bloc D only after acceptance",
    ]:
        assert token in rule


def test_0203_manifest_lists_controlled_scheduler_hook_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/run_controlled_scheduler_hook_smoke_acceptance.py",
        "tests/tools/test_run_controlled_scheduler_hook_smoke_acceptance_0203.py",
        "tests/rules/test_controlled_scheduler_hook_smoke_acceptance_0203_rule.py",
        "doc/architecture/CONTROLLED_SCHEDULER_HOOK_SMOKE_ACCEPTANCE_0203.md",
        "doc/code-rules/0203_controlled_scheduler_hook_smoke_acceptance_rule.md",
    ]:
        assert token in manifest
