from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_real_closed_loop_smoke_0281.py"
TOOL = ROOT / "tools/run_github_real_closed_loop_smoke_0281.py"
ARCHITECTURE = (
    ROOT / "doc/architecture/GITHUB_REAL_CLOSED_LOOP_SMOKE_0281.md"
)
REPORT = ROOT / "PHASE0281_R7_REAL_CLOSED_LOOP_SMOKE_REPORT.md"


def test_real_smoke_reuses_locked_chain_and_never_mutates_github() -> None:
    module = MODULE.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")

    for required in (
        "run_github_dual_artifact_run_assembly",
        "run_github_operator_laboratory_advisory_projection",
        "plan_github_controlled_advisory_issue_publication",
        "FakeLaboratoryClosedLoopSmokeCommand",
        "SourceCandidateDecision",
        "publication_preview",
        "publication_plan",
        "existing_scheduler_used",
        "github_mutation_performed",
    ):
        assert required in module

    for required in (
        "register_laboratory_visit_handler",
        "Scheduler(",
        "SQLiteSqlContextStore",
        "DemoQdrantProjectionExecutor",
        "DemoQdrantRecallExecutor",
        "publication_preview.json",
        "publication_plan.json",
    ):
        assert required in tool

    for forbidden in (
        "gh api",
        "issue comment",
        "--method POST",
        "requests.",
        "urlopen(",
        "QdrantClient(",
        "LaboratoryManager",
    ):
        assert forbidden not in module + tool


def test_projects_repository_change_is_explicitly_false() -> None:
    combined = (
        ARCHITECTURE.read_text(encoding="utf-8")
        + REPORT.read_text(encoding="utf-8")
    )
    assert "projects_repository_change_required: false" in combined
    assert "newicody/projects: no Git-tracked modification required" in combined
