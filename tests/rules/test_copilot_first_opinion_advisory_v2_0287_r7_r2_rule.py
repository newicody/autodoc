from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "templates/github/scripts/run_autodoc_copilot_advisory.py"
REPORT = ROOT / "PHASE0287_R7_R2_COPILOT_FIRST_OPINION_ADVISORY_V2_REPORT.md"
ARCH = ROOT / "doc/architecture/COPILOT_FIRST_OPINION_ADVISORY_V2_0287_R7_R2.md"


def test_public_meaning_is_versioned_at_the_top_level() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert '"schema": "missipy.github.copilot_advisory.v2"' in text
    assert "parsed = extract_first_opinion(process.stdout)" in text
    assert "def extract_advisory" in text
    assert "def extract_first_opinion" in text
    assert "def _first_opinion_prompt" in text
    assert '("autodoc_dispatch", "context")' in text
    assert "copilot_first_opinion.v1" not in text
    assert '"first_opinion"' not in text


def test_v2_contains_only_the_four_requested_analysis_fields() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    for marker in (
        '"concrete_objective": parsed["concrete_objective"]',
        '"expected_result": parsed["expected_result"]',
        '"provided_constraints": list(parsed["provided_constraints"])',
        '"success_criteria": list(parsed["success_criteria"])',
        "actual != expected",
        'if not normalized["success_criteria"]',
    ):
        assert marker in text

    payload_section = text.split('payload = {', maxsplit=1)[1]
    payload_section = payload_section.split('except (', maxsplit=1)[0]
    for old_key in (
        '"summary": parsed',
        '"suggested_route": parsed',
        '"assumptions": list',
        '"questions": list',
        '"risks": list',
        '"confidence": parsed',
    ):
        assert old_key not in payload_section


def test_existing_copilot_safety_boundary_is_preserved() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    for marker in (
        '"--output-format=json"',
        '"--stream=off"',
        '"--deny-tool=read"',
        '"--deny-tool=write"',
        '"--deny-tool=shell"',
        '"--deny-tool=url"',
        '"--deny-tool=memory"',
        '"usable_as_authority": False',
    ):
        assert marker in text


def test_phase_records_code_rule_and_transition_status() -> None:
    report = REPORT.read_text(encoding="utf-8")
    architecture = ARCH.read_text(encoding="utf-8")

    assert "code_rule_review: done" in report
    assert "code_rule_update_required: false" in report
    assert "live_path_status: transition" in report
    assert "No external library was added" in report
    assert "v2 only" in architecture


def test_projects_installation_guide_is_cumulative_and_safe() -> None:
    guide = (
        ROOT / "templates/github/projects-repository/INSTALLATION.md"
    ).read_text(encoding="utf-8")
    runbook = (
        ROOT / "templates/github/projects-repository/COPILOT_ADVISORY_V2.md"
    ).read_text(encoding="utf-8")

    assert "Version du guide : `0287-r5-r1`." in guide
    assert "Extension de contrat Copilot : `0287-r7-r2`." in guide
    assert "Version actuelle du guide : `0287-r5`." in guide
    assert "0287-r5-r2-r2" in guide
    assert "`COPILOT_ADVISORY_V2.md`" in guide
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in guide
    assert "Ne pas créer de secret `AUTODOC_COPILOT_TOKEN`" in guide
    assert "Ne pas utiliser `--delete`" in guide
    assert len(guide.splitlines()) <= 380
    assert "missipy.github.copilot_advisory.v2" in runbook
    assert "usable_as_authority=false" in runbook
    assert "plan_digest" in runbook


def test_roadmap_ends_with_generic_operational_closure() -> None:
    roadmap = (ROOT / "doc/README_CURRENT.md").read_text(encoding="utf-8")

    assert "### 0287-r7-r2 — Copilot first-opinion advisory v2" in roadmap
    assert "### 0287-r7-r10 — generic operational closure" in roadmap
    normalized = " ".join(roadmap.split())
    assert "No Chalouf or other product-specific phase follows" in normalized
    assert "### 0288" not in roadmap
    assert "Chalouf integrator" not in roadmap
