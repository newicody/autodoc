from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_github_external_artifact_smoke.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_EXTERNAL_ARTIFACT_SMOKE_0162.md"
RULE = ROOT / "doc" / "code-rules" / "0162_github_external_artifact_boundary_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0162_CHANGED_FILES.md"


def test_0162_files_exist() -> None:
    assert TOOL.exists()
    assert DOC.exists()
    assert RULE.exists()
    assert MANIFEST.exists()


def test_0162_tool_locks_external_github_boundary() -> None:
    text = TOOL.read_text(encoding="utf-8")

    for token in [
        "newicody/autodoc",
        "newicody/autodoc-ideas",
        "development_repo_ingestion",
        "github_project_external_artifact",
        "artifact exchange only",
        "publish_to_github",
        "external_call_performed",
        "sql_write",
        "qdrant_write",
        "github_api_call",
        "external_network",
        "scheduler_execution",
        "llm_execution",
        "openvino_execution",
        "github_project_scenario.py",
        "server_oriented_deliberation_cycle.py",
        "github_publication_review.py",
        "source_candidate_github_projection_payload.py",
        "source_candidate_remote_mutation_gate.py",
    ]:
        assert token in text

    for forbidden in [
        "DbApiSqlContextStore(",
        "request.urlopen(",
        "QdrantClient",
        "subprocess.run(",
    ]:
        assert forbidden not in text


def test_0162_docs_define_no_autodoc_dev_repo_ingestion() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")

    for token in [
        "Autodoc/MissiPy development repository",
        "external GitHub Project",
        "newicody/autodoc-ideas",
        "must not ingest newicody/autodoc",
        "no SQL write",
        "no Qdrant write",
        "no GitHub API call",
        "publication review",
    ]:
        assert token in doc

    for token in [
        "Do not use the development repository",
        "external artifact repository",
        "GitHub Action/Copilot",
        "publication review",
        "no automatic publication",
    ]:
        assert token in rule


def test_0162_manifest_changed_files_are_limited() -> None:
    text = MANIFEST.read_text(encoding="utf-8")

    for path in [
        "tools/run_github_external_artifact_smoke.py",
        "tests/tools/test_github_external_artifact_smoke_0162.py",
        "tests/rules/test_github_external_artifact_boundary_0162_rule.py",
        "doc/architecture/GITHUB_EXTERNAL_ARTIFACT_SMOKE_0162.md",
        "doc/code-rules/0162_github_external_artifact_boundary_rule.md",
        "doc/docs/architecture/runtime/162_github_external_artifact_smoke.dot",
        "doc/CHANGELOG_0162_GITHUB_EXTERNAL_ARTIFACT_SMOKE.md",
        "doc/manifests/MANIFEST_0162_CHANGED_FILES.md",
        "PHASE0162_TEST_REPORT.md",
    ]:
        assert path in text

    assert "src/context/github_project_scenario.py" not in text
    assert "src/context/source_candidate.py" not in text
