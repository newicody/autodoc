from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_github_dual_artifact_server_sync_once_0281.py"
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_DUAL_ARTIFACT_FETCH_RUN_GROUP_INTEGRATION_0281.md"
REPORT = ROOT / "PHASE0281_R3_FETCH_ONCE_RUN_GROUP_INTEGRATION_REPORT.md"


def test_fetch_integration_reuses_existing_ports_and_assembly() -> None:
    text = TOOL.read_text(encoding="utf-8")

    for required in (
        "_DEFAULT_BASE_SYNC_TOOL",
        "run_github_dual_artifact_run_assembly",
        "GitHubDualArtifactRunAssemblyCommand",
        "GitHubDualArtifactRunMember",
        "run_group_write_action",
        "advisory_payload_retained",
        "advisory_content_authoritative",
        "no GitHub mutation",
        "no SQL write",
        "no Qdrant write",
        "no Scheduler route",
    ):
        assert required in text

    for forbidden in (
        "urlopen(",
        "Request(",
        "requests.",
        "gh api",
        "issue comment",
        "Scheduler(",
        "QdrantClient(",
    ):
        assert forbidden not in text


def test_phase_declares_no_projects_repository_change() -> None:
    combined = (
        ARCHITECTURE.read_text(encoding="utf-8")
        + REPORT.read_text(encoding="utf-8")
    )
    assert "projects_repository_change_required: false" in combined
    assert "newicody/projects: no modification required" in combined
    assert "--sync-tool tools/run_github_dual_artifact_server_sync_once_0281.py" in combined
