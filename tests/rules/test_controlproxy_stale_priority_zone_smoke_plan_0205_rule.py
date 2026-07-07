from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_controlproxy_stale_priority_zone_smoke.py"
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_STALE_PRIORITY_ZONE_SMOKE_PLAN_0205.md"
RULE = ROOT / "doc" / "code-rules" / "0205_controlproxy_stale_priority_zone_smoke_plan_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0205_CHANGED_FILES.md"


def test_0205_tool_is_stale_priority_zone_plan_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0205 is the Bloc D ControlProxy stale priority zone smoke plan only",
        "controlproxy_contract_audit.json",
        "controlproxy_stale_priority_zone_smoke_plan.json",
        "Reuse/adapt existing surfaces first",
        "0205 must reuse the 0204 ControlProxy contract audit",
        "0205 must not introduce a new runtime handler",
        "0205 does not execute Scheduler.run",
        "0205 does not modify Scheduler.run",
        "0205 does not import runtime handler modules",
        "0205 does not call handle_scheduler_route_command",
        "0205 does not call handle_scheduler_route_request",
        "0205 does not call prepare_route_proxy_runtime",
        "0205 does not call mark_route_frame_stale",
        "0205 does not call read_route_frame",
        "0205 does not request writer permits",
        "0205 does not call write_route_frame",
        "0205 does not write ControlProxy or RouteProxy frames",
        "0205 does not call GitHub API or use network",
        "ControlProxy remains a coordination and contract surface, not business authority",
        "Scheduler/policy/zone remain authority",
        "RouteProxy remains the fast data-plane frame surface",
        "0205 plans stale priority zone behavior only",
        "0206-controlproxy_routeproxy_coherence_acceptance",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0205_doc_locks_stale_priority_zone_plan_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0205 creates a ControlProxy stale priority zone smoke plan",
        "The input is controlproxy_contract_audit.json",
        "The output is controlproxy_stale_priority_zone_smoke_plan.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0205 does not write ControlProxy or RouteProxy frames",
        "ControlProxy remains coordination, not authority",
        "Scheduler/policy/zone remain authority",
        "P0206 may execute the controlled stale priority zone smoke explicitly",
    ]:
        assert token in doc


def test_0205_rule_requires_plan_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read controlproxy_contract_audit.json from 0204",
        "Plan stale priority zone behavior only",
        "Reuse existing ControlProxy and RouteProxy contract surfaces",
        "Do not write ControlProxy frames in 0205",
        "Do not write RouteProxy frames in 0205",
        "Do not call mark_route_frame_stale in 0205",
        "Do not add a new ControlProxy runtime",
        "ControlProxy remains coordination, not business authority",
        "Scheduler/policy/zone remain authority",
        "Allow P0206 to unlock controlled stale priority zone smoke explicitly",
    ]:
        assert token in rule


def test_0205_manifest_lists_stale_priority_zone_plan_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/plan_controlproxy_stale_priority_zone_smoke.py",
        "tests/tools/test_plan_controlproxy_stale_priority_zone_smoke_0205.py",
        "tests/rules/test_controlproxy_stale_priority_zone_smoke_plan_0205_rule.py",
        "doc/architecture/CONTROLPROXY_STALE_PRIORITY_ZONE_SMOKE_PLAN_0205.md",
        "doc/code-rules/0205_controlproxy_stale_priority_zone_smoke_plan_rule.md",
    ]:
        assert token in manifest
