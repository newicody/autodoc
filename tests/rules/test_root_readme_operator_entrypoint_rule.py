from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_root_readme_is_operator_entrypoint() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    required_sections = [
        "# Autodoc / MissiPy",
        "## Why this exists",
        "## Current architecture",
        "## Source of truth",
        "## Patch queue workflow",
        "## Tests",
        "## Documentation map",
        "## AI-assisted development",
        "## Current boundary",
        "## Roadmap orientation",
        "## Non-goals",
    ]

    for section in required_sections:
        assert section in readme


def test_root_readme_documents_local_first_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "the local machine is the source of truth" in readme
    assert "remote mutation by default" in readme
    assert "GitHub API writes" in readme
    assert "tokens committed to the repository" in readme


def test_root_readme_documents_ai_assisted_hardware_context() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for name in ("ChatGPT", "Claude", "Gemini", "Perplexity", "Mistral"):
        assert name in readme

    assert "without requiring an expensive dedicated GPU" in readme
    assert "CPU/iGPU-friendly" in readme


def test_root_readme_is_not_a_phase_changelog_dump() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "The root README is intentionally stable" in readme
    assert "Phase 6.1-r1" not in readme
    assert "Phase 6.1-r1" not in readme
    assert "# Changelog" not in readme
