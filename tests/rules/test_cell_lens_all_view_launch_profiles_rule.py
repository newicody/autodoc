from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_all_view_launch_profiles_declares_versioned_schema() -> None:
    source = _read("tools/cell_lens_all_view_launch_profiles.py")
    assert 'CELL_LENS_ALL_VIEW_LAUNCH_PROFILES_SCHEMA = "missipy.cell_lens_all_view_launch_profiles.v1"' in source
    assert "build_cell_lens_all_view_launch_profiles" in source
    assert "browser-health-canvas" in source


def test_all_view_launch_profiles_has_no_live_or_mutation_path() -> None:
    source = _read("tools/cell_lens_all_view_launch_profiles.py")
    forbidden = ["requests", "urllib", "httpx", "OPENAI_API_KEY", "github", "ThreadingHTTPServer"]
    for token in forbidden:
        assert token not in source


def test_all_view_launch_profiles_docs_include_all_modes() -> None:
    doc = _read("doc/demo/CELL_LENS_ALL_VIEW_LAUNCH_PROFILES.md")
    assert "missipy.cell_lens_all_view_launch_profiles.v1" in doc
    assert "VISPY_APP=pyqt6" in doc
    assert "QT_QPA_PLATFORM=wayland" in doc
    assert "browser Canvas" in doc
    assert "browser health Canvas" in doc
    assert "health-view.html" in doc
    assert "SSE stream" in doc
    assert "read-only" in doc
    assert "127.0.0.1" in doc


def test_all_view_launch_profiles_manifest_has_no_runtime_dependency() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART10_7_CELL_LENS_ALL_VIEW_LAUNCH_PROFILES.md")
    assert "tools/cell_lens_all_view_launch_profiles.py" in manifest
    assert "all view launch profiles" in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
