from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "tests/tools/test_run_love_actions_closed_loop_0287_r7_r15_r2.py"


def test_missing_runtime_configuration_case_is_hermetic() -> None:
    source = TARGET.read_text(encoding="utf-8")
    start = source.index(
        "def test_missing_runtime_configuration_has_operator_facing_error"
    )
    tail = source[start:]
    next_test = tail.find("\ndef test_", 1)
    body = tail if next_test < 0 else tail[:next_test]

    assert 'local = tmp_path / "love.ini"' in body
    assert 'local.write_text("", encoding="utf-8")' in body
    assert "config=str(local)" in body
    assert "config=None" not in body
