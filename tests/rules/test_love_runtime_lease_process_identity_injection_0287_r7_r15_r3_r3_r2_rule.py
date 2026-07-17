from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "src/context/love_imported_actions_runtime_contract_0287.py"
TOOL = ROOT / "tools/run_love_actions_closed_loop_0287.py"


def test_runtime_lease_contract_has_no_process_transport_dependency() -> None:
    source = CONTRACT.read_text(encoding="utf-8")
    assert "import os" not in source
    assert "os.getpid" not in source
    assert "current_process_id: int" in source
    assert "self.ensure_current_process(current_process_id)" in source


def test_preview_tool_injects_process_identity_and_keeps_port_validation() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for marker in (
        "validate_imported_actions_runtime_ports",
        "current_process_id=os.getpid()",
        "validate_imported_actions_runtime_ports(lease.ports)",
        "_acquire_imported_actions_runtime_lease",
        "_close_tool_bounded_runtime_lease",
    ):
        assert marker in source
