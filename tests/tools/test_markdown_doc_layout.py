from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.markdown_doc_layout import (
    apply_markdown_layout_plan,
    build_markdown_layout_plan,
    classify_markdown_path,
)


def test_classify_keeps_root_readme() -> None:
    target, reason = classify_markdown_path(Path("README.md"))

    assert target is None
    assert "root readme" in reason


def test_classify_root_phase_report() -> None:
    target, reason = classify_markdown_path(Path("PHASE3_10_TEST_REPORT.md"))

    assert target == Path("doc/reports/phase3/PHASE3_10_TEST_REPORT.md")
    assert "phase report" in reason


def test_classify_root_manifest() -> None:
    target, _ = classify_markdown_path(Path("MANIFEST_PHASE7_0_CHANGED_FILES.md"))

    assert target == Path("doc/manifests/MANIFEST_PHASE7_0_CHANGED_FILES.md")


def test_classify_doc_changelog() -> None:
    target, _ = classify_markdown_path(Path("doc/CHANGELOG_PHASE7_0_ROOT_README.md"))

    assert target == Path("doc/changelogs/CHANGELOG_PHASE7_0_ROOT_README.md")


def test_layout_plan_skips_patch_readme_and_moves_root_reports(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Root\n", encoding="utf-8")
    (tmp_path / "PHASE1_3_TEST_REPORT.md").write_text("# Report\n", encoding="utf-8")
    (tmp_path / "MANIFEST_CHANGED_FILES.md").write_text("# Manifest\n", encoding="utf-8")
    (tmp_path / "patch" / "0001").mkdir(parents=True)
    (tmp_path / "patch" / "0001" / "README.md").write_text("# Patch\n", encoding="utf-8")

    plan = build_markdown_layout_plan(tmp_path)

    moves = {(move.source.name, move.target.as_posix()) for move in plan.moves}
    assert ("PHASE1_3_TEST_REPORT.md", (tmp_path / "doc/reports/phase1/PHASE1_3_TEST_REPORT.md").as_posix()) in moves
    assert ("MANIFEST_CHANGED_FILES.md", (tmp_path / "doc/manifests/MANIFEST_CHANGED_FILES.md").as_posix()) in moves
    assert any(path.name == "README.md" for path in plan.kept)
    assert any("patch/0001/README.md" in path.as_posix() for path in plan.skipped)


def test_apply_layout_moves_files_and_updates_markdown_references(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "See PHASE1_3_TEST_REPORT.md and MANIFEST_CHANGED_FILES.md\n",
        encoding="utf-8",
    )
    (tmp_path / "PHASE1_3_TEST_REPORT.md").write_text("# Report\n", encoding="utf-8")
    (tmp_path / "MANIFEST_CHANGED_FILES.md").write_text("# Manifest\n", encoding="utf-8")

    plan = build_markdown_layout_plan(tmp_path)
    apply_markdown_layout_plan(plan)

    assert not (tmp_path / "PHASE1_3_TEST_REPORT.md").exists()
    assert (tmp_path / "doc/reports/phase1/PHASE1_3_TEST_REPORT.md").exists()
    assert (tmp_path / "doc/manifests/MANIFEST_CHANGED_FILES.md").exists()

    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "doc/reports/phase1/PHASE1_3_TEST_REPORT.md" in readme
    assert "doc/manifests/MANIFEST_CHANGED_FILES.md" in readme
