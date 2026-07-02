from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_docs_svg_build_policy_tool_is_local_only() -> None:
    source = _read("tools/docs_svg_build_policy.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "authorization")
    for forbidden_text in forbidden:
        assert forbidden_text not in source


def test_docs_svg_build_policy_tool_targets_context_svgs() -> None:
    source = _read("tools/docs_svg_build_policy.py")
    assert "doc\" / \"docs\" / \"architecture\" / \"context" in source
    assert 'rglob("*.svg")' in source


def test_docs_svg_build_policy_does_not_modify_makefile() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_13_CHANGED_FILES.md")
    assert "doc/makefile" not in manifest.lower()
    assert "makefile" not in manifest.lower()


def test_docs_svg_build_policy_manifest_uses_post_migration_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_13_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "tools/docs_svg_build_policy.py" in manifest
