from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_aider_is_documented_as_dormant_not_removed() -> None:
    doc = _read("doc/maintenance/LOCAL_AI_AIDER_DORMANT.md")
    assert "Aider is dormant" in doc
    assert "not deleted" in doc
    assert "not part of the active development path" in doc


def test_cleanup_tool_targets_generated_aider_artifacts_only() -> None:
    source = _read("tools/local_ai_dormant_cleanup.py")
    assert "roadmap_b_aider_prompt.md" in source
    assert "roadmap_b_aider_orchestrator_run_report.json" in source
    assert "0039-part8_roadmap_b_part8_1_local_data_contract" in source
    assert "src/kernel/scheduler.py" not in source


def test_cleanup_patch_does_not_add_external_api_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART8_1_AIDER_DORMANT_CLEANUP.md")
    assert "OPENAI_API_KEY" not in manifest
    assert "remote mutation" not in manifest.lower()
    assert ".dot" not in manifest
    assert ".svg" not in manifest


def test_cleanup_keeps_patch_queue_as_active_development_path() -> None:
    doc = _read("doc/maintenance/LOCAL_AI_AIDER_DORMANT.md")
    assert "apply_patch_queue.py" in doc
    assert "ChatGPT Plus 5.5 Advanced" in doc
