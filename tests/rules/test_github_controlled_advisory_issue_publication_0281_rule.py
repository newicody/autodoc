from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "src/context/github_controlled_advisory_issue_publication_0281.py"
)
TOOL = ROOT / "tools/publish_github_advisory_issue_comment_0281.py"
ARCHITECTURE = (
    ROOT
    / "doc/architecture/GITHUB_CONTROLLED_ADVISORY_ISSUE_PUBLICATION_0281.md"
)
REPORT = (
    ROOT
    / "PHASE0281_R6_CONTROLLED_ADVISORY_ISSUE_PUBLICATION_REPORT.md"
)


def test_contract_and_adapter_keep_mutation_explicit_and_local() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")

    for token in (
        "operator_decision must be approve",
        "policy_decision_id must start with policy:",
        "action == \"replay\"",
        "collision",
        "advisory_is_authority",
        "github_mutation_allowed",
        "github_mutation_performed",
    ):
        assert token in contract

    for token in (
        "--execute",
        "--confirm-plan-digest",
        '"POST"',
        "replay-noop",
        "collision blocks mutation",
        "workflow producer cannot self-authorize publication",
    ):
        assert token in tool

    for forbidden in (
        "Scheduler(",
        "QdrantClient(",
        "requests.",
        "urlopen(",
        "issues: write",
        "${{ github.token }}",
    ):
        assert forbidden not in contract + tool


def test_projects_repository_change_is_explicitly_false() -> None:
    combined = (
        ARCHITECTURE.read_text(encoding="utf-8")
        + REPORT.read_text(encoding="utf-8")
    )
    assert "projects_repository_change_required: false" in combined
    assert "newicody/projects: no Git-tracked modification required" in combined
    assert "workflow permissions remain unchanged" in combined
