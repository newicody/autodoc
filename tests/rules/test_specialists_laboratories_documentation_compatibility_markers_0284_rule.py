import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "doc/README_CURRENT.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    / "SPECIALISTS_LABORATORIES_DOCUMENTATION_COMPATIBILITY_MARKERS_0284.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    / "MANIFEST_0284_R9_R2_SPECIALISTS_LABORATORIES_DOCUMENTATION_COMPATIBILITY_MARKERS.md"
)
REPORT = (
    ROOT
    / "PHASE0284_R9_R2_SPECIALISTS_LABORATORIES_DOCUMENTATION_COMPATIBILITY_MARKERS_REPORT.md"
)


def test_current_roadmap_preserves_stable_0281_0282_markers() -> None:
    source = CURRENT.read_text(encoding="utf-8")
    required = (
        "GLOBAL_ARCHITECTURE_CURRENT_0282.md",
        "PROJECTV2_CYCLE_HISTORY_DEVELOPMENT_0282.md",
        "PROJECT_BEGINNING_CURRENT_COMPARISON_0282.md",
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
        assert token in source


def test_installation_keeps_current_version_before_historical_marker() -> None:
    source = INSTALLATION.read_text(encoding="utf-8")
    current = re.search(
        r"^Version du guide : `(?P<version>[^`]+)`\.$",
        source,
        flags=re.MULTILINE,
    )
    assert current is not None
    assert current.group("version") != "0284-r1-r5"

    historical = "Version du guide : `0284-r1-r5`."
    assert historical in source[current.end() :]
    assert "| `0284-r9` |" in source


def test_phase_documents_lock_non_runtime_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, REPORT)
    )
    for marker in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "runtime_modified: false",
        "scheduler_modified: false",
        "projects_installation_modified: true",
        "projects_installation_verified: true",
        "external_dependencies_added: false",
    ):
        assert marker in combined
