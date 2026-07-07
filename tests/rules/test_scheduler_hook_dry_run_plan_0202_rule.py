from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_scheduler_hook_dry_run.py"
DOC = ROOT / "doc" / "architecture" / "SCHEDULER_HOOK_DRY_RUN_PLAN_0202.md"
RULE = ROOT / "doc" / "code-rules" / "0202_scheduler_hook_dry_run_plan_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0202_CHANGED_FILES.md"


def test_0202_tool_is_plan_only_and_reuses_audited_surfaces() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0202 is the Bloc C Scheduler hook dry-run plan only",
        "scheduler_integration_surface_audit.json",
        "scheduler_hook_dry_run_plan.json",
        "Reuse/adapt existing surfaces first",
        "0202 must reuse the 0201 surface audit",
        "0202 must not add a new Scheduler hook implementation",
        "0202 must not introduce a new runtime handler",
        "0202 does not execute Scheduler.run",
        "0202 does not import runtime handler modules",
        "0202 does not call handle_scheduler_route_command",
        "0202 does not call handle_scheduler_route_request",
        "0202 does not call prepare_route_proxy_runtime",
        "0202 does not call read_route_frame",
        "0202 does not request writer permits",
        "0202 does not call write_route_frame",
        "0202 does not write ControlProxy or RouteProxy frames",
        "0202 does not call GitHub API or use network",
        "adapter -> command builder -> minimal handler -> readback",
        "p0203_may_execute_controlled_scheduler_hook",
        "0203-controlled_scheduler_hook_smoke_acceptance",
        "source_baseline_ref or source_entry_digest missing",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0202_doc_locks_scheduler_hook_dry_run_plan_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0202 creates a Scheduler hook dry-run plan from the 0201 surface audit",
        "The input is scheduler_integration_surface_audit.json",
        "The output is scheduler_hook_dry_run_plan.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0202 does not execute Scheduler.run",
        "0202 does not write RouteProxy or ControlProxy frames",
        "P0203 may unlock a controlled Scheduler hook smoke explicitly",
        "The provenance repair item from P0201 is carried forward",
    ]:
        assert token in doc


def test_0202_rule_requires_dry_run_plan_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read scheduler_integration_surface_audit.json from 0201",
        "Reuse the existing audited surfaces before adding new code",
        "Do not add a new Scheduler hook implementation",
        "Do not execute Scheduler.run in 0202",
        "Do not write RouteProxy frames in 0202",
        "Do not write ControlProxy frames in 0202",
        "Allow P0203 to unlock a controlled Scheduler hook smoke explicitly",
        "Require adapter -> command builder -> minimal handler -> readback",
        "Carry provenance repair items forward",
    ]:
        assert token in rule


def test_0202_manifest_lists_scheduler_hook_plan_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/plan_scheduler_hook_dry_run.py",
        "tests/tools/test_plan_scheduler_hook_dry_run_0202.py",
        "tests/rules/test_scheduler_hook_dry_run_plan_0202_rule.py",
        "doc/architecture/SCHEDULER_HOOK_DRY_RUN_PLAN_0202.md",
        "doc/code-rules/0202_scheduler_hook_dry_run_plan_rule.md",
    ]:
        assert token in manifest
