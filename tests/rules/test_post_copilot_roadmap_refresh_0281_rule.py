from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "doc" / "README_CURRENT.md"
README = ROOT / "README.md"


def test_current_roadmap_locks_post_copilot_closed_loop() -> None:
    text = CURRENT.read_text(encoding="utf-8")

    required = (
        "Scheduler = the only orchestration authority",
        "autodoc-authoritative-request/authoritative_request.json",
        "autodoc-copilot-advisory/copilot_advisory.json",
        "autodoc-dual-artifact-manifest/dual_artifact_manifest.json",
        "0281-r2 — dual-artifact run assembly contract",
        "0281-r3 — fetch-once run-group integration",
        "0281-r4 — pinned and cached Copilot CLI runtime",
        "0281-r5 — operator and laboratory advisory projection",
        "0281-r6 — controlled Issue publication",
        "0281-r7 — real closed-loop smoke",
        "no new Scheduler or parallel orchestrator for laboratories",
        "Chalouf as the final integrator scenario",
    )

    for token in required:
        assert token in text


def test_root_readme_points_to_current_roadmap_without_becoming_phase_doc() -> None:
    text = README.read_text(encoding="utf-8")

    assert "doc/README_CURRENT.md" in text
    assert "The active roadmap is maintained in `doc/README_CURRENT.md`." in text
    assert not text.startswith("# Phase 0281")
