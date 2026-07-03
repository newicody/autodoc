from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cell_lens_launch_profiles_declares_versioned_schema() -> None:
    source = _read("tools/cell_lens_local_launch_profiles.py")
    assert 'CELL_LENS_LAUNCH_PROFILES_SCHEMA = "missipy.cell_lens_local_launch_profiles.v1"' in source
    assert "build_cell_lens_launch_profiles" in source
    assert "detect_qt_platform" in source


def test_cell_lens_launch_profiles_has_no_live_or_mutation_path() -> None:
    source = _read("tools/cell_lens_local_launch_profiles.py")
    forbidden = ["requests", "urllib", "httpx", "OPENAI_API_KEY", "github", "ThreadingHTTPServer"]
    for token in forbidden:
        assert token not in source


def test_cell_lens_launch_profiles_docs_include_wayland_and_browser_modes() -> None:
    doc = _read("doc/demo/CELL_LENS_LOCAL_LAUNCH_PROFILES.md")
    assert "missipy.cell_lens_local_launch_profiles.v1" in doc
    assert "VISPY_APP=pyqt6" in doc
    assert "QT_QPA_PLATFORM=wayland" in doc
    assert "browser Canvas" in doc
    assert "read-only" in doc
    assert "127.0.0.1" in doc


def test_cell_lens_launch_profiles_manifest_has_no_runtime_dependency() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART10_5_CELL_LENS_LOCAL_LAUNCH_PROFILES.md")
    assert "tools/cell_lens_local_launch_profiles.py" in manifest
    assert "launch profiles" in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
