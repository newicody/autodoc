from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cell_snapshot_contract_declares_versioned_schema() -> None:
    source = _read("src/context/cell_snapshot.py")
    assert 'CELL_SNAPSHOT_SCHEMA = "missipy.cell.v1"' in source
    assert "@dataclass(frozen=True, slots=True)" in source


def test_cell_snapshot_contract_is_observation_only() -> None:
    source = _read("src/context/cell_snapshot.py")
    forbidden = [
        "vispy",
        "Scheduler",
        "EventBus",
        "requests",
        "urllib",
        "httpx",
        "subprocess",
        "OPENAI_API_KEY",
    ]
    for token in forbidden:
        assert token not in source


def test_cell_snapshot_contract_docs_forbid_commands() -> None:
    doc = _read("doc/contracts/CELL_SNAPSHOT_CONTRACT_V1.md")
    assert "missipy.cell.v1" in doc
    assert "observation-only" in doc
    assert "not a command" in doc
    assert "must not import VisPy" in doc


def test_cell_snapshot_manifest_has_no_runtime_dependency_additions() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART8_3_CELL_SNAPSHOT_CONTRACT_V1.md")
    assert "src/context/cell_snapshot.py" in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
