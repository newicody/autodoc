from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase7_handoff_contract_is_local_only() -> None:
    source = _read("src/context/source_candidate_phase7_handoff_contract.py").lower()
    cli = _read("tools/source_candidate_phase7_handoff_contract_cli.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "authorization")
    for forbidden_text in forbidden:
        assert forbidden_text not in source
        assert forbidden_text not in cli


def test_phase7_handoff_contract_freezes_boundaries() -> None:
    source = _read("src/context/source_candidate_phase7_handoff_contract.py")
    assert "external_service_calls_allowed=False" in source
    assert "remote_mutation_allowed=False" in source
    assert "scheduler_execution_allowed=False" in source
    assert "local_source_of_truth=True" in source


def test_phase7_handoff_contract_manifest_uses_post_migration_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_20_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_phase7_handoff_contract.py" in manifest


def test_phase7_handoff_contract_does_not_add_dot_or_svg() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_20_CHANGED_FILES.md")
    assert ".dot" not in manifest
    assert ".svg" not in manifest
