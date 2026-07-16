from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_final_deliverable_publication_plan_0287.py"
REPORT = ROOT / "PHASE0287_R7_R13_FINAL_DELIVERABLE_PUBLICATION_PLAN_REPORT.md"
ARCH = ROOT / "doc/architecture/FINAL_DELIVERABLE_PUBLICATION_PLAN_0287_R7_R13.md"
DOT = ROOT / "doc/architecture/FINAL_DELIVERABLE_PUBLICATION_PLAN_0287_R7_R13.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_R13_FINAL_DELIVERABLE_PUBLICATION_PLAN.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R13_FINAL_DELIVERABLE_PUBLICATION_PLAN.md"


def test_r13_bundle_is_complete_and_keeps_dot_as_source() -> None:
    for path in (SOURCE, REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
    assert not DOT.with_suffix(".svg").exists()


def test_contract_reuses_existing_comment_snapshot_and_uses_distinct_marker() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "github_controlled_advisory_issue_publication_0281" in text
    assert "GitHubIssueCommentSnapshot" in text
    assert 'MARKER_PREFIX = "autodoc:final-deliverable"' in text
    assert 'MARKER_PREFIX = "autodoc:copilot-advisory"' not in text


def test_contract_is_pure_and_creates_no_parallel_runtime() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import subprocess",
        "class MemoryManager",
        "class PublicationManager",
        "class LaboratoryManager",
        "class Scheduler",
        "class Orchestrator",
        "QdrantClient(",
        "openvino.runtime",
    )
    for token in forbidden:
        assert token not in text


def test_plan_requires_operator_digest_and_exact_readback() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "confirmed_plan_digest_required" in text
    assert "operator_decision_required" in text
    assert "require_exact_issue_body" in text
    assert "require_exact_project_value" in text
    assert "verify_love_final_deliverable_publication_readback" in text


def test_manifest_declares_unchanged_authorities_and_next_steps() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    for token in (
        "Scheduler unchanged",
        "SQL unchanged",
        "Qdrant unchanged",
        "OpenVINO unchanged",
        "GitHub mutation not performed",
        "0287-r7-r14",
    ):
        assert token in text
