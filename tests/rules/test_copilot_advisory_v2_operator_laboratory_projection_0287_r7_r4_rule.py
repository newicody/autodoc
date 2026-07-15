from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROJECTION = (
    ROOT / "src/context/github_operator_laboratory_advisory_projection_0281.py"
)
RUNBOOK = ROOT / "templates/github/projects-repository/COPILOT_ADVISORY_V2.md"
REPORT = (
    ROOT
    / "PHASE0287_R7_R4_COPILOT_ADVISORY_V2_OPERATOR_LABORATORY_PROJECTION_REPORT.md"
)


def test_existing_projection_surface_is_extended_without_parallel_runtime() -> None:
    source = PROJECTION.read_text(encoding="utf-8")

    for token in (
        "GitHubCopilotAdvisoryLaboratoryProjection",
        "GitHubCopilotFirstOpinionLaboratoryProjection",
        "PROJECTION_SCHEMA_V2",
        "PUBLICATION_PREVIEW_SCHEMA_V2",
        "ADVISORY_SCHEMA_V1",
        "ADVISORY_SCHEMA_V2",
        "run_github_dual_artifact_laboratory_smoke",
    ):
        assert token in source
    for forbidden in (
        "LaboratoryManager",
        "PromptManager",
        "Scheduler(",
        "qdrant_client",
        "requests.",
    ):
        assert forbidden not in source


def test_v2_projection_is_not_rewritten_into_v1_fields() -> None:
    source = PROJECTION.read_text(encoding="utf-8")

    v2_start = source.index("class GitHubCopilotFirstOpinionLaboratoryProjection")
    command_start = source.index(
        "class GitHubOperatorLaboratoryAdvisoryProjectionCommand"
    )
    v2_class = source[v2_start:command_start]
    for token in (
        "concrete_objective",
        "expected_result",
        "provided_constraints",
        "success_criteria",
    ):
        assert token in v2_class
    for legacy in (
        "summary:",
        "suggested_route:",
        "assumptions:",
        "questions:",
        "risks:",
        "confidence:",
    ):
        assert legacy not in v2_class


def test_runbook_and_report_lock_the_transition_boundary() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")

    for token in (
        "Projection opérateur/laboratoire",
        "publication preview v2",
        "aucun champ v1",
        "live_path_status: transition",
        "code_rule_review: done",
    ):
        assert token in runbook or token in report
