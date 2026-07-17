from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_love_actions_closed_loop_0287.py"


def test_importer_composes_the_readable_name_matcher() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "from context.human_readable_artifact_identity_0287 import" in source
    assert "matches_actions_artifact_name(" in source
    assert "legacy exact name or readable canonical suffix" in source


def test_importer_downloads_the_actual_remote_name_but_keeps_canonical_keys() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert 'actual_artifact_name = str(metadata.get("name", "")).strip()' in source
    assert "artifact_name=actual_artifact_name" in source
    assert "metadata = artifact_metadata[artifact_name]" in source
    assert '"autodoc-authoritative-request": "authoritative_request.json"' in source
    assert '"autodoc-copilot-advisory": "copilot_advisory.json"' in source
    assert '"autodoc-dual-artifact-manifest": "dual_artifact_manifest.json"' in source
