from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_github_read_only_artifact_fetch_smoke.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_READ_ONLY_ARTIFACT_FETCH_SMOKE_0164.md"
RULE = ROOT / "doc" / "code-rules" / "0164_github_read_only_artifact_fetch_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0164_CHANGED_FILES.md"


def test_0164_files_exist() -> None:
    assert TOOL.exists()
    assert DOC.exists()
    assert RULE.exists()
    assert MANIFEST.exists()


def test_0164_tool_reuses_existing_read_only_surfaces() -> None:
    text = TOOL.read_text(encoding="utf-8")

    for token in [
        "FakeSourceCandidateReadOnlyExternalProbeAdapter",
        "build_source_candidate_read_only_external_probe_request_from_file",
        "write_source_candidate_read_only_external_probe_request",
        "write_source_candidate_read_only_external_probe_result",
        "build_source_candidate_external_probe_bundle",
        "SourceCandidateExternalProjectionContractPolicy",
        "build_source_candidate_external_projection_contract",
        "SourceCandidateGithubProjectionPayloadPolicy",
        "build_source_candidate_github_projection_payload",
        "SourceCandidateRemoteMutationGatePolicy",
        "run_source_candidate_remote_mutation_gate",
        "write_source_candidate_remote_mutation_gate_result",
        "existing_builders_used",
    ]:
        assert token in text

    for forbidden in [
        "class GitHubAdapter",
        "class GithubAdapter",
        "class SourceCandidateReadOnlyExternalProbeAdapter",
        "requests.",
        "urllib.",
        "http.client",
        "socket.",
        "DbApiSqlContextStore(",
        "Qdrant",
        "OpenVINO",
        "subprocess.run(",
    ]:
        assert forbidden not in text


def test_0164_docs_lock_read_only_before_real_github_fetch() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")

    for token in [
        "read-only artifact fetch",
        "reuse existing builders",
        "FakeSourceCandidateReadOnlyExternalProbeAdapter",
        "SourceCandidateExternalProbeBundle",
        "SourceCandidateGithubProjectionPayload",
        "run_source_candidate_remote_mutation_gate",
        "no GitHub API call",
        "no SQL write",
        "no Qdrant write",
        "remote mutation gate remains closed",
    ]:
        assert token in doc

    for token in [
        "Do not create a new GitHub adapter",
        "Use the existing read-only probe",
        "Use the existing external probe bundle",
        "Use the existing remote mutation gate",
        "No remote mutation",
    ]:
        assert token in rule


def test_0164_manifest_changed_files_are_limited() -> None:
    text = MANIFEST.read_text(encoding="utf-8")

    for path in [
        "tools/run_github_read_only_artifact_fetch_smoke.py",
        "tests/tools/test_github_read_only_artifact_fetch_smoke_0164.py",
        "tests/rules/test_github_read_only_artifact_fetch_0164_rule.py",
        "doc/architecture/GITHUB_READ_ONLY_ARTIFACT_FETCH_SMOKE_0164.md",
        "doc/code-rules/0164_github_read_only_artifact_fetch_rule.md",
        "doc/docs/architecture/runtime/164_github_read_only_artifact_fetch_smoke.dot",
        "doc/CHANGELOG_0164_GITHUB_READ_ONLY_ARTIFACT_FETCH_SMOKE.md",
        "doc/manifests/MANIFEST_0164_CHANGED_FILES.md",
        "PHASE0164_TEST_REPORT.md",
    ]:
        assert path in text

    assert "src/context/source_candidate_read_only_external_probe.py" not in text
    assert "src/context/source_candidate_external_probe_bundle.py" not in text
    assert "src/context/source_candidate_github_projection_payload.py" not in text
