import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/audit_github_real_read_only_scan_reuse_0272.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("audit_github_0272", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_0272_cli_writes_atomic_report(tmp_path: Path, capsys) -> None:
    _write(tmp_path, "tools/run_github_actions_artifact_fetch_once.py", "class GitHubActionsClient:\n def _get_json(self): pass\n def _get_bytes(self): pass\n# no remote mutation\n")
    _write(tmp_path, "src/context/github_artifact_server_fetch_config.py", "token_env='GITHUB_TOKEN'\nallowed_repositories=()\ndef _looks_like_secret_value(v): return False\n")
    _write(tmp_path, "src/context/github_scan_once_handoff_0267.py", "HANDOFF_SCHEMA='x'\nscan_once=True\nremote_mutation_allowed=False\n")
    _write(tmp_path, "src/context/source_candidate_github_adapter.py", "FakeSourceCandidateGithubProjectionAdapter\nSourceCandidateRemoteMutationGatePolicy\nrun_source_candidate_remote_mutation_gate\n")
    _write(tmp_path, "src/context/source_candidate_remote_mutation_gate.py", "SourceCandidateRemoteMutationGatePolicy\nmutation_allowed=False\n")
    output = tmp_path / "report.json"
    module = _load_tool()
    code = module.main(("--repo-root", str(tmp_path), "--output", str(output), "--format", "summary"))
    assert code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["network_used"] is False
    assert "github_real_read_only_scan_reuse_audit_valid=True" in capsys.readouterr().out
    assert not output.with_suffix(".json.tmp").exists()
