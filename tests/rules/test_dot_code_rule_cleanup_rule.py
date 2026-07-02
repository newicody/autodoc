from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_dot_code_rule_cleanup_tool_is_local_only() -> None:
    source = _read("tools/dot_remove_code_rule_references.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "token", "authorization")
    for token in forbidden:
        assert token not in source


def test_dot_code_rule_cleanup_tool_targets_dot_only() -> None:
    source = _read("tools/dot_remove_code_rule_references.py")
    assert 'rglob("*.dot")' in source
    assert ".svg" not in source


def test_dot_code_rule_cleanup_uses_post_migration_manifest_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_10_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "tools/dot_remove_code_rule_references.py" in manifest
