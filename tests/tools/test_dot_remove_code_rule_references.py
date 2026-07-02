from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.dot_remove_code_rule_references import (  # noqa: E402
    assert_dot_code_rule_references_absent,
    build_dot_code_rule_cleanup_report,
    remove_code_rule_reference_lines,
)


def test_remove_code_rule_reference_lines_removes_only_matching_lines() -> None:
    source = """digraph x {
  input -> processor;
  code_rule [label="code_rule"];
  processor -> code_rule;
  processor -> output;
}
"""

    cleaned, removed = remove_code_rule_reference_lines(source)

    assert removed == 2
    assert "code_rule" not in cleaned
    assert "input -> processor;" in cleaned
    assert "processor -> output;" in cleaned


def test_dot_cleanup_report_can_apply_to_fixture(tmp_path: Path) -> None:
    dot_dir = tmp_path / "doc" / "docs" / "architecture"
    dot_dir.mkdir(parents=True)
    target = dot_dir / "sample.dot"
    target.write_text(
        """digraph sample {
  source -> gate;
  gate -> code_rule;
  gate -> report;
}
""",
        encoding="utf-8",
    )

    report = build_dot_code_rule_cleanup_report(tmp_path, apply=True)

    assert report.checked_file_count == 1
    assert report.changed_file_count == 1
    assert report.removed_line_count == 1
    assert "code_rule" not in target.read_text(encoding="utf-8")


def test_dot_cleanup_assertion_reports_remaining_references(tmp_path: Path) -> None:
    dot_dir = tmp_path / "doc" / "docs" / "architecture"
    dot_dir.mkdir(parents=True)
    (dot_dir / "sample.dot").write_text("digraph sample { code_rule -> report; }\n", encoding="utf-8")

    try:
        assert_dot_code_rule_references_absent(tmp_path)
    except AssertionError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected code_rule assertion failure")

    assert "sample.dot" in message
    assert "code_rule" in message


def test_dot_cleanup_assertion_passes_after_apply(tmp_path: Path) -> None:
    dot_dir = tmp_path / "doc" / "docs" / "architecture"
    dot_dir.mkdir(parents=True)
    (dot_dir / "sample.dot").write_text("digraph sample { code_rule -> report; }\n", encoding="utf-8")

    build_dot_code_rule_cleanup_report(tmp_path, apply=True)

    assert_dot_code_rule_references_absent(tmp_path)
