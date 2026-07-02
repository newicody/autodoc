from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.markdown_doc_migrate_repo import (  # noqa: E402
    apply_markdown_doc_layout_migration,
    rewrite_python_doc_reference_text,
)


def test_rewrite_python_doc_reference_text_updates_known_markdown_paths() -> None:
    text = """
def test_docs(ROOT):
    assert (ROOT / "PHASE6_10_TEST_REPORT.md").exists()
    assert (ROOT / "MANIFEST_PHASE7_5_CHANGED_FILES.md").exists()
    assert (ROOT / "doc/code_rule.md").exists()
    assert (ROOT / "CHANGELOG_PHASE7_5_GITHUB_EXPORT_BUNDLE.md").exists()
"""

    updated = rewrite_python_doc_reference_text(text, {})

    assert '"doc/reports/phase6/PHASE6_10_TEST_REPORT.md"' in updated
    assert '"doc/manifests/MANIFEST_PHASE7_5_CHANGED_FILES.md"' in updated
    assert '"doc/code-rules/code_rule.md"' in updated
    assert '"doc/changelogs/CHANGELOG_PHASE7_5_GITHUB_EXPORT_BUNDLE.md"' in updated


def test_migration_apply_moves_markdown_and_updates_tests(tmp_path: Path) -> None:
    (tmp_path / "tests" / "rules").mkdir(parents=True)
    (tmp_path / "doc").mkdir()
    (tmp_path / "README.md").write_text("# Root\n", encoding="utf-8")
    (tmp_path / "PHASE6_10_TEST_REPORT.md").write_text("# Report\n", encoding="utf-8")
    (tmp_path / "MANIFEST_PHASE7_5_CHANGED_FILES.md").write_text("# Manifest\n", encoding="utf-8")
    (tmp_path / "doc" / "code_rule.md").write_text("# Rules\n", encoding="utf-8")

    test_file = tmp_path / "tests" / "rules" / "test_docs.py"
    test_file.write_text(
        'assert (ROOT / "PHASE6_10_TEST_REPORT.md").exists()\n'
        'assert (ROOT / "MANIFEST_PHASE7_5_CHANGED_FILES.md").exists()\n'
        'assert (ROOT / "doc/code_rule.md").exists()\n',
        encoding="utf-8",
    )

    result = apply_markdown_doc_layout_migration(
        tmp_path,
        report_path=tmp_path / "doc" / "maintenance" / "migration.json",
        apply=True,
    )

    assert result.move_count == 3
    assert result.test_file_update_count == 1
    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "doc/reports/phase6/PHASE6_10_TEST_REPORT.md").exists()
    assert (tmp_path / "doc/manifests/MANIFEST_PHASE7_5_CHANGED_FILES.md").exists()
    assert (tmp_path / "doc/code-rules/code_rule.md").exists()

    updated = test_file.read_text(encoding="utf-8")
    assert "doc/reports/phase6/PHASE6_10_TEST_REPORT.md" in updated
    assert "doc/manifests/MANIFEST_PHASE7_5_CHANGED_FILES.md" in updated
    assert "doc/code-rules/code_rule.md" in updated
