import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_github_actions_artifact_scan_once_live_0272.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("github_artifact_scan_live_0272", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _configs(tmp_path: Path):
    dataset = SimpleNamespace(
        root=tmp_path / "dataset",
        state_path=tmp_path / "dataset/index/fetch_state.json",
    )
    project = SimpleNamespace(
        config_path=tmp_path / "project.ini",
        external_repository="newicody/autodoc-ideas",
        development_repository="newicody/autodoc",
        project_url="https://github.com/users/newicody/projects/2",
        workflow_name="autodoc-ticket-artifact.yml",
        artifact_name_prefix="autodoc-ticket-artifact-",
        token_env="GITHUB_TOKEN",
        api_url="https://api.github.com",
        allowed_repositories=("newicody/autodoc-ideas",),
        scan_command=(
            "tools/run_github_actions_artifact_scan_once_live_0272.py "
            "--execute --policy-decision-id "
            "policy:0272:fcron-actions-artifacts-read-only"
        ),
        history_mode="append_only",
        to_json_dict=lambda: {
            "safety": {
                "read_only_scan": True,
                "allow_workflow_dispatch": False,
                "allow_remote_mutation": False,
                "allow_sql_write": False,
                "allow_qdrant_write": False,
            }
        },
    )
    fetch = SimpleNamespace(
        config_path=tmp_path / "fetch.ini",
        external_repository="newicody/autodoc-ideas",
        development_repository="newicody/autodoc",
        project_url="https://github.com/users/newicody/projects/2",
        workflow_name="autodoc-ticket-artifact.yml",
        artifact_name_prefix="autodoc-ticket-artifact-",
        token_env="GITHUB_TOKEN",
        api_url="https://api.github.com",
        allowed_repositories=("newicody/autodoc-ideas",),
        dataset=dataset,
        to_json_dict=lambda: {
            "safety": {
                "read_only_fetch": True,
                "allow_remote_mutation": False,
                "allow_sql_write": False,
                "allow_qdrant_write": False,
            }
        },
    )
    return project, fetch


def test_0272_r2_cli_plan_is_offline(tmp_path: Path, monkeypatch, capsys) -> None:
    module = _load_tool()
    project, fetch = _configs(tmp_path)
    monkeypatch.setattr(module, "load_github_artifact_scan_config", lambda path: project)
    monkeypatch.setattr(module, "load_github_artifact_server_fetch_config", lambda path: fetch)
    output = tmp_path / "report.json"
    code = module.main(("--output", str(output), "--format", "summary"))
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert code == 0
    assert payload["valid"] is True
    assert payload["execute"] is False
    assert payload["external_call_performed"] is False
    assert "direct_issue_scan_required=False" in capsys.readouterr().out


def test_0272_r2_cli_wraps_existing_fetch_tool(tmp_path: Path, monkeypatch) -> None:
    module = _load_tool()
    project, fetch = _configs(tmp_path)
    monkeypatch.setattr(module, "load_github_artifact_scan_config", lambda path: project)
    monkeypatch.setattr(module, "load_github_artifact_server_fetch_config", lambda path: fetch)
    monkeypatch.setenv("GITHUB_TOKEN", "not-serialized")
    monkeypatch.setattr(
        module,
        "_run_existing_fetch_tool",
        lambda **kwargs: (
            0,
            {
                "schema": "missipy.github_actions.artifact_fetch_once_report.v1",
                "status": "ok",
                "repository": "newicody/autodoc-ideas",
                "workflow_name": "autodoc-ticket-artifact.yml",
                "artifact_name_prefix": "autodoc-ticket-artifact-",
                "external_call_performed": True,
                "counts": {
                    "downloaded_count": 1,
                    "synced_count": 1,
                    "error_count": 0,
                },
                "boundary": [
                    "read-only GitHub Actions artifact fetch",
                    "no remote mutation",
                    "no SQL write",
                    "no qdrant write",
                ],
                "state_path": str(tmp_path / "state.json"),
            },
        ),
    )
    output = tmp_path / "report.json"
    code = module.main(
        (
            "--execute",
            "--policy-decision-id",
            "policy:0272:test",
            "--output",
            str(output),
            "--format",
            "json",
        )
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert code == 0
    assert payload["valid"] is True
    assert payload["counts"]["synced_count"] == 1
    assert payload["token_env"] == "GITHUB_TOKEN"
    assert "not-serialized" not in output.read_text(encoding="utf-8")
    assert not output.with_suffix(".json.tmp").exists()


def test_0272_r2_cli_keeps_0165_config_alias() -> None:
    module = _load_tool()
    args = module.parse_args(("--config", "custom-project.ini"))
    assert args.project_config == Path("custom-project.ini")
