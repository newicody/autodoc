from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_vispy_viewer_is_confined_to_tool_boundary() -> None:
    tool = _read("tools/visualize_cell_population_vispy.py")
    assert "from vispy import app, scene" in tool

    health = _read("src/visualization/cell_lens_health.py")
    projection = _read("src/visualization/cell_lens_projection.py")
    assert "vispy" not in health.lower()
    assert "vispy" not in projection.lower()


def test_vispy_viewer_does_not_use_command_or_bus_tokens() -> None:
    combined = (
        _read("tools/visualize_cell_population_vispy.py")
        + _read("src/visualization/cell_lens_health.py")
        + _read("src/visualization/cell_lens_projection.py")
    )
    forbidden = [
        "Scheduler",
        "EventBus",
        "requests",
        "urllib",
        "httpx",
        "OPENAI_API_KEY",
        "github",
    ]
    for token in forbidden:
        assert token not in combined


def test_vispy_viewer_docs_keep_it_observation_only() -> None:
    doc = _read("doc/visualization/VISPY_CELL_LENS_VIEWER.md")
    assert "observation-only" in doc
    assert "read-only" in doc
    assert "tail" in doc
    assert "replay" in doc
    assert "must not command the system" in doc


def test_vispy_viewer_manifest_declares_optional_dependency_only() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART9_1_VISPY_CELL_LENS_VIEWER.md")
    assert "tools/visualize_cell_population_vispy.py" in manifest
    assert "optional" in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
