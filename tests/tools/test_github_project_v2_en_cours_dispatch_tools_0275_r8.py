from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = (
    ROOT
    / "tools/dispatch_github_project_v2_en_cours_transitions_0275_r8.py"
)
RUN_ONCE = (
    ROOT
    / "tools/run_github_project_v2_en_cours_dispatch_once_0275_r8.py"
)


def _load(path: Path, name: str):
    spec = spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_0275_r8_dispatch_tool_executes_once_and_persists_state(
    tmp_path,
    monkeypatch,
) -> None:
    module = _load(TOOL, "dispatch_tool_0275_r8")
    config = tmp_path / "config.ini"
    changes = tmp_path / "changes"
    state = tmp_path / "state.json"
    report = tmp_path / "report.json"
    changes.mkdir()
    change_set = changes / "project-v2-change-set-test.json"
    change_set.write_text(
        json.dumps(
            {
                "schema": "missipy.github.project_v2_snapshot_change_set.v1",
                "change_set_ref": "github-project-v2-change-set:test",
                "items": {
                    "changed": [
                        {
                            "item_id": "PVTI_1",
                            "item_type": {
                                "before": "ISSUE",
                                "after": "ISSUE",
                            },
                            "status": {
                                "before": "Recherche",
                                "after": "En cours",
                            },
                            "after": {
                                "type": "ISSUE",
                                "content": {
                                    "number": 1,
                                    "title": "Recherche",
                                    "url": "https://github.com/newicody/projects/issues/1",
                                    "repository": {
                                        "nameWithOwner": "newicody/projects"
                                    },
                                },
                            },
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    config.write_text(
        "\n".join(
            (
                "[workflow_dispatch]",
                "repository = newicody/projects",
                "workflow_name = autodoc-controlled-research.yml",
                "ref = master",
                "token_env = TEST_GITHUB_TOKEN",
                "api_url = https://api.github.invalid",
                "target_status = En cours",
                f"change_set_dir = {changes}",
                f"state_path = {state}",
                f"report_path = {report}",
                "max_dispatches = 10",
                "allow_workflow_dispatch = true",
                "allow_remote_mutation = true",
                "",
            )
        ),
        encoding="utf-8",
    )

    calls = []

    def fake_dispatch(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(module, "_post_workflow_dispatch", fake_dispatch)
    monkeypatch.setenv("TEST_GITHUB_TOKEN", "not-serialized")

    rc = module.main(
        (
            "--config",
            str(config),
            "--execute",
            "--policy-decision-id",
            "policy:test",
            "--format",
            "json",
        )
    )
    assert rc == 0
    assert len(calls) == 1
    assert calls[0]["inputs"]["requested_status"] == "Recherche"
    assert "not-serialized" not in report.read_text(encoding="utf-8")

    rc = module.main(
        (
            "--config",
            str(config),
            "--execute",
            "--policy-decision-id",
            "policy:test-repeat",
        )
    )
    assert rc == 0
    assert len(calls) == 1


def test_0275_r8_run_once_reuses_0272_tools_without_loop() -> None:
    module = _load(RUN_ONCE, "run_once_0275_r8")
    args = module.parse_args(
        (
            "--config",
            "config/example.ini",
            "--policy-decision-id",
            "policy:test",
        )
    )
    commands = module._commands(args)
    flattened = "\n".join(" ".join(command) for _, command in commands)

    assert "run_github_project_v2_query_only_snapshot_0272.py" in flattened
    assert "detect_github_project_v2_snapshot_changes_0272.py" in flattened
    assert "dispatch_github_project_v2_en_cours_transitions_0275_r8.py" in flattened
    source = RUN_ONCE.read_text(encoding="utf-8")
    assert "while " not in source
    assert "Scheduler" not in source
