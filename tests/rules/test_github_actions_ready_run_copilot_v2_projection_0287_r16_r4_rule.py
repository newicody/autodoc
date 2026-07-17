from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_actions_ready_run_copilot_v2_projection_0287.py"
TOOL = ROOT / "tools/run_github_actions_ready_run_copilot_v2_projection_0287.py"


def test_ready_run_projection_reuses_existing_v2_adapters() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for marker in (
        "build_copilot_advisory_v2_publication_preview",
        "project_copilot_advisory_v2_fields",
        "execute_copilot_v2_field_projection",
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_PROJECT_PROJECTION_ALLOWED",
        "confirm_plan_digest",
        "readback_verified",
    ):
        assert marker in source


def test_projection_is_local_raw_only_before_explicit_projectv2_gate() -> None:
    module = MODULE.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")
    for marker in (
        'dataset_root / "raw"',
        "github_artifact_download_performed",
        "durable_raw_dataset_only",
        "laboratory_execution_started",
        "sql_write_performed",
        "qdrant_write_performed",
    ):
        assert marker in module or marker in tool
    for forbidden in (
        "gh run download",
        "LaboratoryManager",
        "Scheduler(",
        "qdrant_client",
        "psycopg",
    ):
        assert forbidden not in tool
