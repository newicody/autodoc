from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUERY_CONFIG = ROOT / "config/github_project_v2_query_only.example.ini"
DISPATCH_CONFIG = ROOT / "config/github_projects_workflow_dispatch.example.ini"
PUSH_FRAME_CONFIG = ROOT / "config/github_project_push_frame.example.ini"
BUNDLE_README = ROOT / "templates/github/projects-repository/README.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
REPORT = ROOT / "PHASE0284_R1_R3_GITHUB_PROJECT_CONNECTOR_CONFIG_SPLIT_REPORT.md"


def test_query_only_and_dispatch_configs_are_separate() -> None:
    query = QUERY_CONFIG.read_text(encoding="utf-8")
    dispatch = DISPATCH_CONFIG.read_text(encoding="utf-8")

    assert "[workflow_dispatch]" not in query
    assert "query_only = true" in query
    assert "graphql_mutation_allowed = false" in query
    assert dispatch.startswith("[workflow_dispatch]\n")
    assert "repository = newicody/projects" in dispatch
    assert "allow_workflow_dispatch = false" in dispatch
    assert "allow_remote_mutation = false" in dispatch



def test_examples_no_longer_reference_retired_repository() -> None:
    combined = "\n".join(
        (
            QUERY_CONFIG.read_text(encoding="utf-8"),
            PUSH_FRAME_CONFIG.read_text(encoding="utf-8"),
            DISPATCH_CONFIG.read_text(encoding="utf-8"),
        )
    )

    assert "newicody/autodoc-ideas" not in combined
    assert "repositories = newicody/projects" in combined


def test_projects_bundle_has_cumulative_installation_guide() -> None:
    readme = BUNDLE_README.read_text(encoding="utf-8")
    installation = INSTALLATION.read_text(encoding="utf-8")

    assert "INSTALLATION.md" in readme
    assert "mode opératoire cumulatif" in installation
    assert "templates/github/projects-repository" in installation
    assert "/home/eric/projet/git/projects" in installation
    assert "rsync -aivn" in installation
    assert "Ne pas utiliser `--delete`" in installation
    assert "github_projects_workflow_dispatch.ini" in installation
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=true" in installation


def test_phase_declares_no_runtime_or_scheduler_change() -> None:
    report = REPORT.read_text(encoding="utf-8")

    assert "scheduler_modified: false" in report
    assert "new_project_mode_added_to_autodoc: false" in report
    assert "active_projects_workflow_added_to_autodoc_root: false" in report
    assert "live_path_status: n/a" in report
    assert "external_library_added: false" in report
