from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_github_actions_artifact_fetch_once.py"
REPORT = (
    ROOT
    / "PHASE0168_R1_GITHUB_ARTIFACT_DOWNLOAD_REDIRECT_AUTH_FIX_REPORT.md"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "GITHUB_ACTIONS_ARTIFACT_DOWNLOAD_REDIRECT_AUTH_0168.md"
)


def test_redirect_boundary_is_local_to_existing_fetcher() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for required in (
        "_download_artifact_archive",
        "HTTPRedirectHandler",
        "build_opener",
        '"application/zip"',
        "artifact redirect URL must be credential-free HTTPS",
    ):
        assert required in source

    redirected_section = source.split(
        "artifact_request = Request(location)",
        maxsplit=1,
    )[1].split("def _get_json", maxsplit=1)[0]
    assert "Authorization" not in redirected_section


def test_phase_boundaries_remain_locked() -> None:
    combined = (
        REPORT.read_text(encoding="utf-8")
        + ARCHITECTURE.read_text(encoding="utf-8")
    )
    for required in (
        "existing_fetcher_reused: true",
        "new_fetcher_added: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
        "remote_mutation_added: false",
    ):
        assert required in combined
