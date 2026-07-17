from pathlib import Path


def test_readiness_tool_exists_and_has_no_mutation_flag() -> None:
    path = Path("tools/check_love_installed_runtime_0287.py")
    text = path.read_text(encoding="utf-8")
    assert "inspect_manual_runtime_readiness" in text
    assert "--execute" not in text
    assert "--commit" not in text
