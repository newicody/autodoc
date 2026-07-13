from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/context/github_operator_laboratory_advisory_projection_0281.py"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/GITHUB_OPERATOR_LABORATORY_ADVISORY_PROJECTION_0281.md"
)
REPORT = (
    ROOT
    / "PHASE0281_R5_OPERATOR_LABORATORY_ADVISORY_PROJECTION_REPORT.md"
)


def test_projection_reuses_existing_intake_smoke_and_scheduler_path() -> None:
    text = MODULE.read_text(encoding="utf-8")

    for required in (
        "run_github_dual_artifact_source_candidate_intake",
        "run_github_dual_artifact_laboratory_smoke",
        "GitHubDualArtifactLaboratorySmokeCommand",
        "ctx:github-advisory:",
        "usable_as_hint",
        "usable_as_authority",
        "publication_gate_required",
        "existing_scheduler_used",
        "scheduler_created",
        "parallel_orchestrator_created",
        "github_mutation_performed",
    ):
        assert required in text

    for forbidden in (
        "Scheduler(",
        "SchedulerContract(",
        "asyncio.Queue(",
        "EventBus(",
        "QdrantClient(",
        "requests.",
        "urlopen(",
        "gh api",
        "issue comment",
    ):
        assert forbidden not in text


def test_projects_repository_change_is_explicitly_false() -> None:
    combined = (
        ARCHITECTURE.read_text(encoding="utf-8")
        + REPORT.read_text(encoding="utf-8")
    )
    assert "projects_repository_change_required: false" in combined
    assert "newicody/projects: no modification required" in combined
