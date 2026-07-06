from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_github_external_artifact_smoke.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_EXTERNAL_ARTIFACT_EXISTING_BUILDERS_0163.md"
RULE = ROOT / "doc" / "code-rules" / "0163_github_external_artifact_existing_builders_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0163_CHANGED_FILES.md"


def test_0163_files_exist() -> None:
    assert TOOL.exists()
    assert DOC.exists()
    assert RULE.exists()
    assert MANIFEST.exists()


def test_0163_tool_uses_existing_github_builders() -> None:
    text = TOOL.read_text(encoding="utf-8")

    for token in [
        "GitHubProjectArtifact",
        "build_github_source_candidate",
        "build_github_context_objective",
        "build_github_project_scenario_packet",
        "build_github_project_context_graph",
        "export_context_graph_dot",
        "build_github_publication_review",
        "render_github_publication_review_markdown",
        "build_context_exploration_plan",
        "LLMSolutionCandidate",
        "LLMSpecialistResult",
        "build_server_orientation_from_github_artifact",
        "existing_builders_used",
    ]:
        assert token in text

    for forbidden in [
        "class GitHubProjectArtifact",
        "class GitHubSourceCandidate",
        "class GitHubProjectPublication",
        "class GitHubPublicationReviewPacket",
        "class GitHubProjectScenarioPacket",
        "class GitHubAdapter",
        "class GithubAdapter",
    ]:
        assert forbidden not in text


def test_0163_docs_lock_reuse_before_new_runtime() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")

    for token in [
        "reuse existing builders",
        "GitHubProjectArtifact",
        "build_github_project_scenario_packet",
        "build_github_publication_review",
        "no new GitHub model",
        "no SQL write",
        "no Qdrant write",
    ]:
        assert token in doc

    for token in [
        "Do not create a parallel GitHub model",
        "Use the existing builders",
        "No new adapter",
        "No new orchestrator",
    ]:
        assert token in rule


def test_0163_manifest_changed_files_are_limited() -> None:
    text = MANIFEST.read_text(encoding="utf-8")

    for path in [
        "tools/run_github_external_artifact_smoke.py",
        "tests/tools/test_github_external_artifact_existing_builders_0163.py",
        "tests/tools/test_github_external_artifact_smoke_0162.py",
        "tests/rules/test_github_external_artifact_existing_builders_0163_rule.py",
        "doc/architecture/GITHUB_EXTERNAL_ARTIFACT_EXISTING_BUILDERS_0163.md",
        "doc/code-rules/0163_github_external_artifact_existing_builders_rule.md",
        "doc/docs/architecture/runtime/163_github_external_artifact_existing_builders.dot",
        "doc/CHANGELOG_0163_GITHUB_EXTERNAL_ARTIFACT_EXISTING_BUILDERS.md",
        "doc/manifests/MANIFEST_0163_CHANGED_FILES.md",
        "PHASE0163_TEST_REPORT.md",
    ]:
        assert path in text

    assert "src/context/github_project_scenario.py" not in text
    assert "src/context/github_publication_review.py" not in text
