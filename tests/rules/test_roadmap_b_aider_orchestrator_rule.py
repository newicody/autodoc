from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_roadmap_b_aider_orchestrator_uses_apply_patch_queue() -> None:
    source = _read("tools/roadmap_b_aider_orchestrator.py")
    assert "apply_patch_queue.py" in source
    assert "--dry-run" in source
    assert "--commit" in source
    assert "--push" in source


def test_roadmap_b_aider_orchestrator_disables_aider_auto_commits() -> None:
    source = _read("tools/roadmap_b_aider_orchestrator.py")
    assert "--no-auto-commits" in source
    assert "--message-file" in source


def test_roadmap_b_aider_orchestrator_requires_validation_for_sensitive_changes() -> None:
    source = _read("tools/roadmap_b_aider_orchestrator.py")
    assert "SENSITIVE_RULE_PATHS" in source
    assert "SENSITIVE_DEPENDENCY_FILES" in source
    assert "SENSITIVE_RUNTIME_PATHS" in source
    assert "operator refused sensitive patch" in source


def test_roadmap_b_aider_orchestrator_keeps_roadmap_b_locked() -> None:
    lock = _read("doc/maintenance/ROADMAP_B_LOCK.md")
    assert "Roadmap B" in lock
    assert "local repository / local server = source of truth" in lock
    assert "GitHub is not the source of truth" in lock


def test_roadmap_b_aider_orchestrator_manifest_uses_post_migration_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART8_0_ROADMAP_B_AIDER_ORCHESTRATOR.md")
    assert "tools/roadmap_b_aider_orchestrator.py" in manifest
    assert "src/kernel/scheduler.py" not in manifest


def test_roadmap_b_aider_orchestrator_does_not_add_dot_or_svg() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART8_0_ROADMAP_B_AIDER_ORCHESTRATOR.md")
    assert ".dot" not in manifest
    assert ".svg" not in manifest
