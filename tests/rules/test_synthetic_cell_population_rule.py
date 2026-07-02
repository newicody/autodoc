from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_synthetic_cell_population_declares_versioned_schema() -> None:
    source = _read("src/context/cell_snapshot_synthetic.py")
    assert 'CELL_SYNTHETIC_POPULATION_SCHEMA = "missipy.cell_synthetic_population.v1"' in source
    assert "SyntheticCellPopulationConfig" in source
    assert "generate_synthetic_cell_snapshots" in source


def test_synthetic_cell_population_emits_cell_contract_not_renderer_contract() -> None:
    source = _read("src/context/cell_snapshot_synthetic.py")
    assert "CellSnapshot" in source
    forbidden = [
        "vispy",
        "Scheduler",
        "EventBus",
        "requests",
        "urllib",
        "httpx",
        "OPENAI_API_KEY",
    ]
    for token in forbidden:
        assert token not in source


def test_synthetic_cell_population_documentation_keeps_it_replaceable() -> None:
    doc = _read("doc/contracts/SYNTHETIC_CELL_POPULATION_GENERATOR_V1.md")
    assert "missipy.cell_synthetic_population.v1" in doc
    assert "same missipy.cell.v1" in doc
    assert "replaceable" in doc
    assert "faux flux" in doc
    assert "true bus" in doc


def test_synthetic_cell_population_manifest_has_no_renderer_dependency() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART8_6_SYNTHETIC_CELL_POPULATION_GENERATOR.md")
    assert "src/context/cell_snapshot_synthetic.py" in manifest
    assert "tools/generate_synthetic_cell_journal.py" in manifest
    assert "VisPy" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
