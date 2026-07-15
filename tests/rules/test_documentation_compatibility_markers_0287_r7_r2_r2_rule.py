from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "doc/README_CURRENT.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
REPORT = ROOT / "PHASE0287_R7_R2_R2_DOCUMENTATION_COMPATIBILITY_MARKERS_REPORT.md"


def test_installation_keeps_stable_markers_and_records_v2_extension() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")

    assert "Version du guide : `0287-r5-r1`." in text
    assert "Extension de contrat Copilot : `0287-r7-r2`." in text
    assert "## Compatibilité cumulative 0287-r5-r2-r2" in text
    assert "Version actuelle du guide : `0287-r5`." in text
    assert "`COPILOT_ADVISORY_V2.md`" in text


def test_historical_chalouf_token_is_retired_not_scheduled() -> None:
    text = CURRENT.read_text(encoding="utf-8")

    assert "Chalouf as the final integrator scenario" in text
    assert "retired from the active roadmap" in text
    assert "### 0287-r7-r10 — generic operational closure" in text
    assert "### 0288" not in text


def test_correction_is_documentation_only() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "runtime_change: false" in text
    assert "remote_mutation: false" in text
    assert "No external library was added" in text
