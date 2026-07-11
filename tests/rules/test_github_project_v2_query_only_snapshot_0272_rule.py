from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src/context/github_project_v2_query_only_snapshot_0272.py"
TOOL = ROOT / "tools/run_github_project_v2_query_only_snapshot_0272.py"
CONFIG = ROOT / "config/github_project_v2_query_only.example.ini"
DOC = ROOT / "doc/architecture/GITHUB_PROJECT_V2_QUERY_ONLY_SNAPSHOT_0272.md"
RULE = ROOT / "doc/code-rules/0272_github_project_v2_query_only_snapshot_rule.md"
OLD_DOC = ROOT / "doc/architecture/GITHUB_ACTIONS_ARTIFACT_SCAN_ONCE_LIVE_0272.md"
OLD_RULE = ROOT / "doc/code-rules/0272_github_actions_artifact_scan_once_live_rule.md"


def test_0272_r3_uses_real_project_identity() -> None:
    config = CONFIG.read_text(encoding="utf-8")
    for phrase in (
        "owner = newicody",
        "number = 2",
        "id = PVT_kwHOA3ouXM4Ba3Ar",
        "view_number_hint = 2",
        "source_mode = project_v2_query_only_snapshot",
    ):
        assert phrase in config


def test_0272_r3_keeps_query_and_mutation_boundaries() -> None:
    core = CORE.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")
    combined = core + tool
    assert "validate_query_only_document" in core
    assert '"graphql_mutation_allowed": False' in core
    assert '"remote_mutation_allowed": False' in core
    assert "Authorization" not in core
    for forbidden in (
        "/issues?",
        "create_issue(",
        "update_issue(",
        "workflow_dispatch(",
        "Scheduler" + ".run(",
        "Runtime" + "Manager",
        "qdrant_client",
        "sqlite3.connect",
    ):
        assert forbidden not in combined


def test_0272_r3_reuses_existing_config_and_isolates_io() -> None:
    core = CORE.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")
    assert "github_project_push_frame_config" in tool
    assert "urlopen" in tool
    assert "urlopen" not in core
    assert "subprocess" not in tool


def test_0272_r3_documents_canonical_and_secondary_paths() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (DOC, RULE, OLD_DOC, OLD_RULE)
    )
    for phrase in (
        "canonical",
        "ProjectV2",
        "query-only",
        "secondary",
        "immutable",
        "remote mutation",
    ):
        assert phrase in combined
