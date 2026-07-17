from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEST_SOURCE = (
    ROOT / "tests/tools/test_run_love_actions_closed_loop_0287_r7_r15_r2.py"
)
REPORT = (
    ROOT
    / "PHASE0287_R7_R15_R2_R2_R3_PYTHON314_DYNAMIC_TOOL_IMPORT_COMPATIBILITY_FIX_REPORT.md"
)


def test_dynamic_loader_registers_module_before_execution() -> None:
    source = TEST_SOURCE.read_text(encoding="utf-8")
    register = "sys.modules[name] = module"
    execute = "spec.loader.exec_module(module)"
    assert "import sys" in source
    assert register in source
    assert execute in source
    assert source.index(register) < source.index(execute)


def test_dynamic_loader_restores_registry_on_failure() -> None:
    source = TEST_SOURCE.read_text(encoding="utf-8")
    assert "previous = sys.modules.get(name)" in source
    assert "sys.modules.pop(name, None)" in source
    assert "sys.modules[name] = previous" in source


def test_fix_is_declared_as_test_only() -> None:
    report = REPORT.read_text(encoding="utf-8")
    assert "production CLI" in report
    assert "unchanged" in report
    assert "invalid test loader" in report
