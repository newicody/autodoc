from configparser import ConfigParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/github_project_v2_query_only.example.ini"
DISPATCH_CONFIG = ROOT / "config/github_projects_workflow_dispatch.example.ini"


def _read_config(path: Path) -> ConfigParser:
    parser = ConfigParser(interpolation=None)
    loaded = parser.read(path, encoding="utf-8")
    assert loaded == [str(path)]
    return parser


def _config() -> ConfigParser:
    return _read_config(CONFIG)


def _dispatch_config() -> ConfigParser:
    return _read_config(DISPATCH_CONFIG)


def test_0275_r8_r1_preserves_the_locked_0272_scan_contract() -> None:
    parser = _config()

    assert parser["artifact_source"]["repositories"] == "newicody/projects"
    assert (
        parser["artifact_source"]["workflow_name"]
        == "autodoc-ticket-artifact.yml"
    )
    assert (
        parser["artifact_source"]["artifact_name_prefix"]
        == "autodoc-ticket-artifact-"
    )
    assert (
        parser["artifact_source"]["trigger_source"]
        == "github_action_on_ticket_event"
    )
    assert parser["scan"].getint("interval_minutes") == 10
    assert (
        parser["scan"]["scan_command"]
        == "tools/run_github_project_v2_query_only_snapshot_0272.py "
        "--execute --policy-decision-id "
        "policy:0272:fcron-project-v2-query-only"
    )


def test_0275_r8_r1_preserves_0272_readiness_and_safety_defaults() -> None:
    parser = _config()

    assert (
        parser["safety"]["allowed_repositories"]
        == "newicody/projects"
    )
    readiness = parser["deployment_readiness"]
    assert readiness["workflow_repository"] == "newicody/projects"
    assert readiness["workflow_name"] == "autodoc-ticket-artifact.yml"
    assert (
        readiness["workflow_path"]
        == ".github/workflows/autodoc-ticket-artifact.yml"
    )


def test_0275_r8_r1_keeps_the_new_dispatch_scope_isolated() -> None:
    parser = _config()

    assert "workflow_dispatch" not in parser
    dispatch = _dispatch_config()["workflow_dispatch"]
    assert dispatch["repository"] == "newicody/projects"
    assert dispatch["workflow_name"] == "autodoc-controlled-research.yml"
    assert dispatch["target_status"] == "En cours"
    assert dispatch.getboolean("allow_workflow_dispatch") is False
    assert dispatch.getboolean("allow_remote_mutation") is False

    safety = parser["safety"]
    assert safety.getboolean("query_only") is True
    assert safety.getboolean("graphql_mutation_allowed") is False
    assert safety.getboolean("allow_workflow_dispatch") is False
    assert safety.getboolean("allow_remote_mutation") is False
