from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from local_ai_dormant_cleanup import (  # noqa: E402
    GITIGNORE_BLOCK,
    apply_cleanup_plan,
    build_cleanup_plan,
)


def test_cleanup_plan_detects_aider_generated_files(tmp_path: Path) -> None:
    artifact = tmp_path / "doc" / "maintenance" / "roadmap_b_aider_prompt.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("generated", encoding="utf-8")

    plan = build_cleanup_plan(tmp_path)

    assert Path("doc/maintenance/roadmap_b_aider_prompt.md") in plan.files_to_remove


def test_cleanup_plan_detects_failed_aider_patch_dir(tmp_path: Path) -> None:
    patch_dir = tmp_path / "patch" / "0039-part8_roadmap_b_part8_1_local_data_contract"
    patch_dir.mkdir(parents=True)

    plan = build_cleanup_plan(tmp_path)

    assert Path("patch/0039-part8_roadmap_b_part8_1_local_data_contract") in plan.directories_to_remove


def test_cleanup_apply_removes_files_and_directories(tmp_path: Path) -> None:
    artifact = tmp_path / "doc" / "maintenance" / "roadmap_b_aider_orchestrator_run_report.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    patch_dir = tmp_path / "patch" / "0039-part8_roadmap_b_part8_1_local_data_contract"
    patch_dir.mkdir(parents=True)
    (patch_dir / "patch.diff").write_text("", encoding="utf-8")

    plan = build_cleanup_plan(tmp_path)
    apply_cleanup_plan(tmp_path, plan)

    assert not artifact.exists()
    assert not patch_dir.exists()


def test_cleanup_updates_gitignore_idempotently(tmp_path: Path) -> None:
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n", encoding="utf-8")

    plan = build_cleanup_plan(tmp_path, update_gitignore=True)
    apply_cleanup_plan(tmp_path, plan, update_gitignore=True)
    first = gitignore.read_text(encoding="utf-8")

    plan = build_cleanup_plan(tmp_path, update_gitignore=True)
    apply_cleanup_plan(tmp_path, plan, update_gitignore=True)
    second = gitignore.read_text(encoding="utf-8")

    assert GITIGNORE_BLOCK in first
    assert first == second
