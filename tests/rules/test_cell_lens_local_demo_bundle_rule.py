from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cell_lens_demo_bundle_declares_versioned_schema() -> None:
    source = _read("tools/cell_lens_local_demo_bundle.py")
    assert 'CELL_LENS_DEMO_BUNDLE_SCHEMA = "missipy.cell_lens_local_demo_bundle.v1"' in source
    assert "build_cell_lens_local_demo_bundle" in source


def test_cell_lens_demo_bundle_is_dry_run_file_only() -> None:
    source = _read("tools/cell_lens_local_demo_bundle.py")
    forbidden = ["vispy", "Scheduler", "EventBus", "requests", "urllib", "httpx", "OPENAI_API_KEY", "github", "ThreadingHTTPServer"]
    for token in forbidden:
        assert token not in source


def test_cell_lens_demo_bundle_docs_show_full_local_chain() -> None:
    doc = _read("doc/demo/CELL_LENS_LOCAL_DEMO_BUNDLE.md")
    assert "missipy.cell_lens_local_demo_bundle.v1" in doc
    assert "synthetic population" in doc
    assert "missipy.cell.v1 journal" in doc
    assert "SSE preview" in doc
    assert "read-only" in doc
    assert "does not start a server" in doc


def test_cell_lens_demo_bundle_manifest_has_no_runtime_server_or_renderer() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART10_4_CELL_LENS_LOCAL_DEMO_BUNDLE.md")
    assert "tools/cell_lens_local_demo_bundle.py" in manifest
    assert "local demo bundle" in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
