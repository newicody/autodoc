from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_dual_artifact_run_assembly_0281.py"


def test_run_assembly_reuses_existing_intake_and_keeps_no_write_boundaries() -> None:
    text = MODULE.read_text(encoding="utf-8")

    for required in (
        "run_github_dual_artifact_source_candidate_intake",
        "GitHubDualArtifactIntakeCommand",
        "@dataclass(frozen=True, slots=True)",
        "advisory_payload_retained",
        "advisory_content_authoritative: bool = False",
        "filesystem_write_performed: bool = False",
        "scheduler_route_created: bool = False",
        "sql_write_performed: bool = False",
        "qdrant_write_performed: bool = False",
        "github_mutation_performed: bool = False",
    ):
        assert required in text

    for forbidden in (
        "Scheduler(",
        "EventBus(",
        "subprocess",
        "urllib",
        "urlopen",
        "sqlite3",
        "qdrant_client",
        ".write_text(",
        ".write_bytes(",
    ):
        assert forbidden not in text
