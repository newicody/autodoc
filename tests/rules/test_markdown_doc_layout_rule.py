from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_markdown_doc_layout_tool_is_stdlib_only() -> None:
    source = _read("tools/markdown_doc_layout.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "git ")
    for token in forbidden:
        assert token not in source


def test_markdown_doc_layout_preserves_root_readme_and_patch_readmes() -> None:
    source = _read("tools/markdown_doc_layout.py")
    assert 'rel == Path("README.md")' in source
    assert 'rel.parts[0] == "patch"' in source


def test_markdown_doc_layout_has_maintenance_doc() -> None:
    assert (ROOT / "doc/maintenance/MARKDOWN_DOC_LAYOUT.md").exists()


def test_markdown_doc_layout_does_not_modify_scheduler() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_6_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "tools/markdown_doc_layout.py" in manifest
