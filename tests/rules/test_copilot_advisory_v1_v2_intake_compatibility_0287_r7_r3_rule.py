from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "src/context/github_dual_artifact_contract_0275.py"
INTAKE = ROOT / "src/context/github_dual_artifact_source_candidate_intake_0275.py"
ASSEMBLY = ROOT / "src/context/github_dual_artifact_run_assembly_0281.py"
RUNBOOK = ROOT / "templates/github/projects-repository/COPILOT_ADVISORY_V2.md"
REPORT = ROOT / "PHASE0287_R7_R3_COPILOT_ADVISORY_V1_V2_INTAKE_REPORT.md"


def test_existing_contract_and_intake_are_extended_without_parallel_runtime() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    intake = INTAKE.read_text(encoding="utf-8")

    assert "GitHubCopilotAdvisoryArtifact" in contract
    assert "GitHubCopilotFirstOpinionAdvisoryArtifact" in contract
    assert "parse_copilot_advisory_artifact" in contract
    assert "missipy.github.copilot_advisory.v1" in contract
    assert "missipy.github.copilot_advisory.v2" in contract
    assert "parse_copilot_advisory_artifact" in intake
    for forbidden in (
        "LaboratoryManager",
        "PromptManager",
        "new Scheduler",
        "qdrant_client",
        "requests.",
    ):
        assert forbidden not in contract
        assert forbidden not in intake


def test_v2_runbook_and_report_lock_non_reinterpretation_boundary() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")

    for token in (
        "aucun champ v1 n’est réinterprété",
        "Le schéma v2 est validé strictement",
        "advisory_schema",
        "advisory_content_copied",
        "live_path_status: transition",
        "code_rule_review: done",
    ):
        assert token in runbook or token in report


def test_existing_run_assembly_remains_schema_neutral() -> None:
    assembly = ASSEMBLY.read_text(encoding="utf-8")

    assert "run_github_dual_artifact_source_candidate_intake" in assembly
    assert "parse_copilot_advisory_artifact" not in assembly
    assert "ADVISORY_SCHEMA_V2" not in assembly
    assert "github_mutation_performed: bool = False" in assembly
