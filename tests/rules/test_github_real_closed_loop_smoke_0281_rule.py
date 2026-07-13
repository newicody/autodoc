from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_real_closed_loop_smoke_0281.py"
TOOL = ROOT / "tools/run_github_real_closed_loop_smoke_0281.py"
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_REAL_CLOSED_LOOP_SMOKE_0281.md"
REPORT = ROOT / "PHASE0281_R7_REAL_CLOSED_LOOP_SMOKE_REPORT.md"


def test_r7_consumes_only_configured_import_dataset() -> None:
    module = MODULE.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")
    for required in (
        "github_dual_artifact_run_groups",
        "configured_server_dataset",
        "dataset_raw_path",
        "dataset_index_path",
        "sha256 mismatch",
        "run_group_report_ref",
    ):
        assert required in module
    for required in (
        "load_github_artifact_server_fetch_config",
        "--config",
        "config.dataset.raw_path",
        "config.dataset.index_path",
        "github_closed_loop_0281",
    ):
        assert required in tool
    for forbidden in (
        "--run-root",
        "--output-root",
        "gh run download",
        "staging/github_actions_artifacts",
        "gh api",
        "--method POST",
        "LaboratoryManager",
    ):
        assert forbidden not in module + tool


def test_locked_chain_and_repo_impact() -> None:
    combined = (
        MODULE.read_text(encoding="utf-8")
        + ARCHITECTURE.read_text(encoding="utf-8")
        + REPORT.read_text(encoding="utf-8")
    )
    for required in (
        "run_github_dual_artifact_run_assembly",
        "run_github_operator_laboratory_advisory_projection",
        "plan_github_controlled_advisory_issue_publication",
        "existing Scheduler",
        "projects_repository_change_required: false",
        "newicody/projects: no Git-tracked modification required",
    ):
        assert required in combined
