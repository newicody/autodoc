from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_controlproxy_contract_surfaces.py"
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_CONTRACT_AUDIT_0204.md"
RULE = ROOT / "doc" / "code-rules" / "0204_controlproxy_contract_audit_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0204_CHANGED_FILES.md"


def test_0204_tool_is_controlproxy_contract_audit_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0204 is the Bloc D ControlProxy contract audit only",
        "controlled_scheduler_hook_smoke_acceptance.json",
        "controlproxy_contract_audit.json",
        "Reuse/adapt existing surfaces first",
        "0204 must audit existing ControlProxy and RouteProxy contract surfaces",
        "0204 must not introduce a new runtime handler",
        "0204 does not execute Scheduler.run",
        "0204 does not import runtime handler modules",
        "0204 does not call handle_scheduler_route_command",
        "0204 does not call handle_scheduler_route_request",
        "0204 does not call prepare_route_proxy_runtime",
        "0204 does not call read_route_frame",
        "0204 does not request writer permits",
        "0204 does not call write_route_frame",
        "0204 does not write ControlProxy or RouteProxy frames",
        "0204 does not call GitHub API or use network",
        "ControlProxy remains a contract and coordination surface, not business authority",
        "Scheduler/policy/zone remain authority",
        "RouteProxy remains the fast data-plane frame surface",
        "src/runtime/controlproxy_scheduler_handler.py",
        "src/runtime/route_proxy_runtime_minimal.py",
        "0205-controlproxy_stale_priority_zone_smoke_plan",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0204_doc_locks_controlproxy_contract_audit_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0204 opens Bloc D with a ControlProxy contract audit",
        "The input is controlled_scheduler_hook_smoke_acceptance.json",
        "The output is controlproxy_contract_audit.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0204 does not write ControlProxy or RouteProxy frames",
        "ControlProxy is not business authority",
        "Scheduler/policy/zone remain authority",
        "The next recommended patch is P0205 ControlProxy stale priority zone smoke plan",
    ]:
        assert token in doc


def test_0204_rule_requires_controlproxy_contract_audit_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read controlled_scheduler_hook_smoke_acceptance.json from 0203",
        "Audit existing ControlProxy and RouteProxy contract surfaces before planning stale priority zone behavior",
        "Reuse controlproxy_scheduler_handler.py",
        "Reuse route_proxy_runtime_minimal.py",
        "ControlProxy is a coordination surface, not business authority",
        "Scheduler/policy/zone remain authority",
        "Do not add a new ControlProxy runtime",
        "Do not add a new runtime handler",
        "Do not write ControlProxy frames in 0204",
        "Do not write RouteProxy frames in 0204",
        "Allow P0205 to plan stale priority zone behavior only after audit",
    ]:
        assert token in rule


def test_0204_manifest_lists_controlproxy_contract_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/audit_controlproxy_contract_surfaces.py",
        "tests/tools/test_audit_controlproxy_contract_surfaces_0204.py",
        "tests/rules/test_controlproxy_contract_audit_0204_rule.py",
        "doc/architecture/CONTROLPROXY_CONTRACT_AUDIT_0204.md",
        "doc/code-rules/0204_controlproxy_contract_audit_rule.md",
    ]:
        assert token in manifest
