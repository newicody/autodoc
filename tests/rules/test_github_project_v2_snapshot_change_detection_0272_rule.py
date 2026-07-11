from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src/context/github_project_v2_snapshot_change_detection_0272.py"
TOOL = ROOT / "tools/detect_github_project_v2_snapshot_changes_0272.py"
DOC = ROOT / "doc/architecture/GITHUB_PROJECT_V2_SNAPSHOT_CHANGE_DETECTION_0272.md"
RULE = ROOT / "doc/code-rules/0272_github_project_v2_snapshot_change_detection_rule.md"


def test_0272_r4_surfaces_exist() -> None:
    for path in (CORE, TOOL, DOC, RULE):
        assert path.exists(), path


def test_change_detection_is_local_only() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in (CORE, TOOL))
    forbidden = (
        "urlopen(",
        "api.github.com",
        "Authorization",
        "qdrant_client",
        "sqlite3.connect",
        "subprocess",
        "Scheduler.run(",
        "workflow_dispatch",
    )
    for phrase in forbidden:
        assert phrase not in combined
    assert '"external_call_performed": False' in combined
    assert '"remote_mutation_allowed": False' in combined


def test_change_detection_reuses_r3_snapshot_schema() -> None:
    text = CORE.read_text(encoding="utf-8")
    assert "from context.github_project_v2_query_only_snapshot_0272 import SNAPSHOT_SCHEMA" in text
    assert "github-project-v2-change-set:" in text
