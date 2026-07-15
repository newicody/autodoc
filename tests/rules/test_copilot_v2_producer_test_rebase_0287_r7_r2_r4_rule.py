from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OPTIONAL = ROOT / "tests/tools/test_github_copilot_advisory_optional_0277.py"
EXTRACTION = ROOT / "tests/tools/test_github_copilot_advisory_response_extraction_0279.py"
WORKFLOW = ROOT / "tests/tools/test_github_dual_artifact_actions_workflow_0275.py"
RUNNER = ROOT / "templates/github/scripts/run_autodoc_copilot_advisory.py"
REPORT = ROOT / "PHASE0287_R7_R2_R4_COPILOT_V2_PRODUCER_TEST_REBASE_REPORT.md"


_FIELDS = (
    "concrete_objective",
    "expected_result",
    "provided_constraints",
    "success_criteria",
)


def test_active_producer_fixtures_are_v2() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (OPTIONAL, EXTRACTION, WORKFLOW)
    )
    for field in _FIELDS:
        assert field in combined
    assert combined.count("missipy.github.copilot_advisory.v2") >= 3


def test_executable_tests_no_longer_feed_v1_response_shape() -> None:
    optional = OPTIONAL.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert '"suggested_route": "research"' not in optional
    assert '\"suggested_route\":\"laboratory\"' not in workflow


def test_historical_v1_reader_remains_available() -> None:
    extraction = EXTRACTION.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    assert "def _advisory()" in extraction
    assert '"summary": "Advisory summary"' in extraction
    assert "def extract_advisory" in runner
    assert "def extract_first_opinion" in runner


def test_rebase_is_test_only_and_installation_neutral() -> None:
    report = REPORT.read_text(encoding="utf-8")
    assert "production code unchanged" in report
    assert "installation_update_required: false" in report
    assert "code_rule_review: done" in report
