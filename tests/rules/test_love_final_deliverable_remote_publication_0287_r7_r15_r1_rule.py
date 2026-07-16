from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_final_deliverable_remote_publication_0287.py"
TOOL = ROOT / "tools/publish_love_final_deliverable_0287.py"
CONTEXT_TEST = ROOT / "tests/context/test_love_final_deliverable_remote_publication_0287_r7_r15_r1.py"
TOOL_TEST = ROOT / "tests/tools/test_publish_love_final_deliverable_0287_r7_r15_r1.py"
REPORT = ROOT / "PHASE0287_R7_R15_R1_FINAL_DELIVERABLE_REMOTE_PUBLICATION_ADAPTER_REPORT.md"
ARCH = ROOT / "doc/architecture/FINAL_DELIVERABLE_REMOTE_PUBLICATION_ADAPTER_0287_R7_R15_R1.md"
DOT = ROOT / "doc/architecture/FINAL_DELIVERABLE_REMOTE_PUBLICATION_ADAPTER_0287_R7_R15_R1.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_R15_R1_FINAL_DELIVERABLE_REMOTE_PUBLICATION_ADAPTER.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R15_R1_FINAL_DELIVERABLE_REMOTE_PUBLICATION_ADAPTER.md"
RULE_TEST = Path(__file__)


def test_r15_r1_bundle_is_complete_and_dot_is_source_only() -> None:
    for path in (
        SOURCE,
        TOOL,
        CONTEXT_TEST,
        TOOL_TEST,
        REPORT,
        ARCH,
        DOT,
        CHANGELOG,
        MANIFEST,
        RULE_TEST,
    ):
        assert path.is_file(), path
    assert not DOT.with_suffix(".svg").exists()


def test_domain_reuses_exact_r13_plan_and_readback_verifier() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for token in (
        "LoveFinalDeliverablePublicationPlan",
        "FinalDeliverableProjectV2Projection",
        "GitHubIssueCommentSnapshot",
        "verify_love_final_deliverable_publication_readback",
        "parse_love_final_deliverable_publication_plan",
    ):
        assert token in text


def test_domain_remains_transport_neutral_and_has_no_parallel_authority() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "import os",
        "import subprocess",
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "class Scheduler",
        "class Orchestrator",
        "class PublicationManager",
        "QdrantClient(",
        "openvino.runtime",
    )
    for token in forbidden:
        assert token not in text


def test_tool_owns_transport_three_locks_and_exact_digest_gate() -> None:
    text = TOOL.read_text(encoding="utf-8")
    for token in (
        "import subprocess",
        "gh_command",
        '"api"',
        '"graphql"',
        "updateProjectV2ItemFieldValue",
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_ISSUE_PUBLICATION_ALLOWED",
        "AUTODOC_PROJECT_PROJECTION_ALLOWED",
        "--confirm-plan-digest",
        "--execute",
    ):
        assert token in text


def test_tool_does_not_enter_scheduler_memory_or_inference_layers() -> None:
    text = TOOL.read_text(encoding="utf-8")
    forbidden = (
        "Scheduler(",
        "Laboratory",
        "Specialist",
        "DbApiSqlContextStore",
        "QdrantClient(",
        "openvino.runtime",
        "run_love_memory_evidence_liaison_synthesis",
        "run_love_full_deterministic_local_smoke",
    )
    for token in forbidden:
        assert token not in text


def test_result_exposes_replay_collision_partial_and_closed_local_boundaries() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for token in (
        '"replay"',
        '"collision"',
        '"partial"',
        "partial_execution",
        "confirm-plan-digest mismatch",
        "scheduler_modified",
        "sql_modified",
        "qdrant_modified",
        "openvino_modified",
    ):
        assert token in text


def test_dot_contains_publication_architecture_without_policy_document() -> None:
    text = DOT.read_text(encoding="utf-8")
    assert "code_rule" not in text.lower()
    for token in (
        "r13 immutable",
        "Issue comment",
        "ProjectV2 field",
        "plan_digest",
        "readback verifier",
    ):
        assert token in text


def test_manifest_keeps_r15_open_and_declares_remaining_units() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    for token in (
        "Preview is the default",
        "0287-r7-r15-r2",
        "0287-r7-r15-r3",
        "0287-r7-r16",
    ):
        assert token in text
