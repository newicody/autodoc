from pathlib import Path

from context.github_real_read_only_scan_reuse_audit_0272 import (
    GitHubReadOnlyScanAuditCommand,
    audit_github_real_read_only_scan_reuse,
)


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture(root: Path) -> None:
    _write(
        root,
        "tools/run_github_actions_artifact_fetch_once.py",
        "class GitHubActionsClient:\n def _get_json(self): pass\n def _get_bytes(self): pass\n# no remote mutation\n",
    )
    _write(
        root,
        "src/context/github_artifact_server_fetch_config.py",
        "token_env = 'GITHUB_TOKEN'\nallowed_repositories = ()\ndef _looks_like_secret_value(value): return False\nallow_remote_mutation = False\n",
    )
    _write(
        root,
        "src/context/github_scan_once_handoff_0267.py",
        "HANDOFF_SCHEMA='x'\nscan_once=True\nremote_mutation_allowed=False\n",
    )
    _write(
        root,
        "src/context/source_candidate_github_adapter.py",
        "FakeSourceCandidateGithubProjectionAdapter\nSourceCandidateRemoteMutationGatePolicy\nrun_source_candidate_remote_mutation_gate\n",
    )
    _write(
        root,
        "src/context/source_candidate_remote_mutation_gate.py",
        "SourceCandidateRemoteMutationGatePolicy\nmutation_allowed=False\n",
    )


def test_0272_audit_reuses_existing_boundaries_and_justifies_issue_client(tmp_path: Path) -> None:
    _fixture(tmp_path)
    result = audit_github_real_read_only_scan_reuse(
        GitHubReadOnlyScanAuditCommand(repo_root=tmp_path)
    )
    assert result.valid is True
    assert result.actions_read_only_client_found is True
    assert result.issue_read_only_client_found is False
    assert result.implementation_needed is True
    assert result.new_shared_read_only_io_module_justified is True
    assert result.network_used is False
    assert result.remote_mutation_performed is False


def test_0272_audit_detects_an_existing_issue_client(tmp_path: Path) -> None:
    _fixture(tmp_path)
    path = tmp_path / "tools/run_github_actions_artifact_fetch_once.py"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\nclass GitHubIssuesReadOnlyClient: pass\ndef list_repository_issues(): pass\n",
        encoding="utf-8",
    )
    result = audit_github_real_read_only_scan_reuse(
        GitHubReadOnlyScanAuditCommand(repo_root=tmp_path)
    )
    assert result.valid is True
    assert result.issue_read_only_client_found is True
    assert result.implementation_needed is False
    assert result.new_shared_read_only_io_module_justified is False


def test_0272_audit_is_bounded() -> None:
    try:
        GitHubReadOnlyScanAuditCommand(repo_root=Path("."), max_files=0)
    except ValueError as exc:
        assert "max_files" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")
