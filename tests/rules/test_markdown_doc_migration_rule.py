from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_markdown_doc_migration_tool_is_stdlib_local_only() -> None:
    source = _read("tools/markdown_doc_migrate_repo.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "github")
    for token in forbidden:
        assert token not in source


def test_markdown_doc_migration_updates_python_test_references() -> None:
    source = _read("tools/markdown_doc_migrate_repo.py")
    assert "rewrite_python_doc_references" in source
    assert "doc/reports/phase" in source
    assert "doc/manifests" in source
    assert "doc/code-rules/code_rule.md" in source


def test_tools_package_or_sys_path_bootstrap_exists_for_imports() -> None:
    source = _read("tools/markdown_doc_migrate_repo.py")
    assert "sys.path.insert" in source


def test_markdown_doc_migration_does_not_modify_scheduler() -> None:
    manifest = _read("MANIFEST_PHASE7_7_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "tools/markdown_doc_migrate_repo.py" in manifest
