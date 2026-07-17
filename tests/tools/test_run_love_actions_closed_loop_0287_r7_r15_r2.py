from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest


def _load_tool(name: str, filename: str) -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "tools" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    return module


def _artifacts():
    return (
        {
            "id": 11,
            "name": "autodoc-authoritative-request",
            "expired": False,
            "workflow_run": {"id": 12345},
        },
        {
            "id": 12,
            "name": "autodoc-copilot-advisory",
            "expired": False,
            "workflow_run": {"id": 12345},
        },
        {
            "id": 13,
            "name": "autodoc-dual-artifact-manifest",
            "expired": False,
            "workflow_run": {"id": 12345},
        },
    )


def test_artifact_selection_requires_one_exact_member_per_name() -> None:
    tool = _load_tool(
        "run_love_actions_closed_loop",
        "run_love_actions_closed_loop_0287.py",
    )
    selected = tool._select_artifacts(_artifacts(), run_id="12345")
    assert tuple(selected) == tuple(tool._EXPECTED_ARTIFACTS)

    with pytest.raises(tool.LoveActionsClosedLoopPreviewError):
        tool._select_artifacts(_artifacts()[:-1], run_id="12345")
    with pytest.raises(tool.LoveActionsClosedLoopPreviewError):
        tool._select_artifacts(
            (*_artifacts(), _artifacts()[0]),
            run_id="12345",
        )


def test_download_member_must_be_unique(tmp_path: Path) -> None:
    tool = _load_tool(
        "run_love_actions_closed_loop_unique",
        "run_love_actions_closed_loop_0287.py",
    )
    target = tmp_path / "artifact"
    target.mkdir()
    expected = target / "authoritative_request.json"
    expected.write_text("{}", encoding="utf-8")
    assert tool._find_exact_download(target, expected.name) == expected

    nested = target / "nested"
    nested.mkdir()
    (nested / expected.name).write_text("{}", encoding="utf-8")
    with pytest.raises(tool.LoveActionsClosedLoopPreviewError):
        tool._find_exact_download(target, expected.name)


def test_publish_tool_reports_missing_plan_without_traceback(
    tmp_path: Path,
    capsys,
) -> None:
    tool = _load_tool(
        "publish_love_final_missing_plan",
        "publish_love_final_deliverable_0287.py",
    )
    missing = tmp_path / "missing.json"
    status = tool.main(
        [
            "--plan",
            str(missing),
            "--operator-decision",
            "approve",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    assert status == 2
    assert "plan file not found" in captured.err
    assert "run_love_actions_closed_loop_0287.py" in captured.err
    assert "Traceback" not in captured.err


def test_runtime_factory_reference_is_explicit_and_has_no_fallback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tool = _load_tool(
        "run_love_actions_closed_loop_factory",
        "run_love_actions_closed_loop_0287.py",
    )
    module_path = tmp_path / "real_runtime_factory_fixture.py"
    module_path.write_text(
        "def build_runtime(**kwargs):\n    return kwargs\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    factory = tool._load_runtime_factory(
        "real_runtime_factory_fixture:build_runtime"
    )
    assert callable(factory)

    with pytest.raises(tool.LoveActionsClosedLoopPreviewError):
        tool._load_runtime_factory("missing-separator")
    with pytest.raises(tool.LoveActionsClosedLoopPreviewError):
        tool._load_runtime_factory("real_runtime_factory_fixture:missing")


def test_r14_runs_inside_injected_scheduler_lifecycle(monkeypatch) -> None:
    import asyncio
    from types import SimpleNamespace

    tool = _load_tool(
        "run_love_actions_closed_loop_scheduler",
        "run_love_actions_closed_loop_0287.py",
    )

    class Scheduler:
        def __init__(self) -> None:
            self.running = False
            self.stopped = asyncio.Event()

        async def run(self) -> None:
            self.running = True
            await self.stopped.wait()
            self.running = False

        async def shutdown(self) -> None:
            self.stopped.set()

    scheduler = Scheduler()
    runtime = SimpleNamespace(
        scheduler=scheduler,
        dispatcher=object(),
        authority_store=object(),
        projection_port=object(),
        collection=object(),
        embedder=object(),
        executor=object(),
        scheduler_lifecycle="tool-bounded",
    )
    command = SimpleNamespace(run_id="123")

    async def fake_r14(command, **ports):
        assert scheduler.running is True
        assert ports["scheduler"] is scheduler
        return "r14-result"

    monkeypatch.setattr(
        tool,
        "run_love_full_deterministic_local_smoke",
        fake_r14,
    )
    result = asyncio.run(
        tool._run_r14_on_existing_scheduler(command, runtime)
    )
    assert result == "r14-result"
    assert scheduler.running is False


def test_externally_managed_scheduler_is_not_started_or_stopped(monkeypatch) -> None:
    import asyncio
    from types import SimpleNamespace

    tool = _load_tool(
        "run_love_actions_closed_loop_external_scheduler",
        "run_love_actions_closed_loop_0287.py",
    )

    class Scheduler:
        async def run(self) -> None:
            raise AssertionError("externally managed scheduler must not be started")

        async def shutdown(self) -> None:
            raise AssertionError("externally managed scheduler must not be stopped")

    runtime = SimpleNamespace(
        scheduler=Scheduler(),
        dispatcher=object(),
        authority_store=object(),
        projection_port=object(),
        collection=object(),
        embedder=object(),
        executor=object(),
        scheduler_lifecycle="externally-managed",
    )
    command = SimpleNamespace(run_id="123")

    async def fake_r14(command, **ports):
        return "external-r14-result"

    monkeypatch.setattr(
        tool,
        "run_love_full_deterministic_local_smoke",
        fake_r14,
    )
    assert (
        asyncio.run(tool._run_r14_on_existing_scheduler(command, runtime))
        == "external-r14-result"
    )


def test_tool_bounded_scheduler_failure_cancels_r14(monkeypatch) -> None:
    import asyncio
    from types import SimpleNamespace

    tool = _load_tool(
        "run_love_actions_closed_loop_scheduler_failure",
        "run_love_actions_closed_loop_0287.py",
    )

    class Scheduler:
        async def run(self) -> None:
            raise RuntimeError("scheduler failed")

        async def shutdown(self) -> None:
            return None

    runtime = SimpleNamespace(
        scheduler=Scheduler(),
        dispatcher=object(),
        authority_store=object(),
        projection_port=object(),
        collection=object(),
        embedder=object(),
        executor=object(),
        scheduler_lifecycle="tool-bounded",
    )
    command = SimpleNamespace(run_id="123")

    async def hanging_r14(command, **ports):
        await asyncio.Event().wait()

    monkeypatch.setattr(
        tool,
        "run_love_full_deterministic_local_smoke",
        hanging_r14,
    )
    with pytest.raises(
        tool.LoveActionsClosedLoopPreviewError,
        match="Scheduler failed",
    ):
        asyncio.run(tool._run_r14_on_existing_scheduler(command, runtime))


def test_artifact_selection_rejects_other_workflow_run() -> None:
    tool = _load_tool(
        "run_love_actions_closed_loop_wrong_run",
        "run_love_actions_closed_loop_0287.py",
    )
    artifacts = list(_artifacts())
    artifacts[1] = dict(artifacts[1])
    artifacts[1]["workflow_run"] = {"id": 99999}
    with pytest.raises(
        tool.LoveActionsClosedLoopPreviewError,
        match="run identity mismatch",
    ):
        tool._select_artifacts(tuple(artifacts), run_id="12345")


def test_candidate_decision_is_explicit_and_merge_requires_target(tmp_path: Path) -> None:
    tool = _load_tool(
        "run_love_actions_closed_loop_candidate_gate",
        "run_love_actions_closed_loop_0287.py",
    )
    common = {
        "repository": "newicody/projects",
        "run_id": "12345",
        "project_owner": "newicody",
        "project_number": 3,
        "project_item_id": "PVTI_item",
        "project_field_ref": "PVTSSF_field",
        "project_field_name": "Statut révision",
        "project_status_value": "Terminé",
        "output_path": tmp_path / "result.json",
        "gh_command": "gh",
        "token_env": "AUTODOC_PROJECT_TOKEN",
        "context_generation": 1,
        "branch_ref": "context-branch:main",
        "project_ref": "project:newicody-projects",
        "security_scope": "scope:local",
        "artifact_storage_ref": "storage:zfs:test",
        "policy_decision_id": "policy:test",
        "target_context_id": "",
        "operator_reason": "Approved for preview.",
        "runtime_factory_ref": "server.runtime:build",
    }
    promote = tool.LoveActionsClosedLoopPreviewCliCommand(
        candidate_decision="promote",
        **common,
    )
    assert promote.candidate_decision == "promote"

    with pytest.raises(
        tool.LoveActionsClosedLoopPreviewError,
        match="requires target_context_id",
    ):
        tool.LoveActionsClosedLoopPreviewCliCommand(
            candidate_decision="merge",
            **common,
        )


def test_low_level_project_identifiers_and_runtime_override_are_optional() -> None:
    tool = _load_tool(
        "run_love_actions_closed_loop_short_cli",
        "run_love_actions_closed_loop_0287.py",
    )
    args = tool._parse_args(
        [
            "--run-id",
            "12345",
            "--repository",
            "newicody/projects",
            "--candidate-decision",
            "promote",
        ]
    )
    assert args.project_item_id == ""
    assert args.project_field_ref == ""
    assert args.runtime_factory is None


def test_local_settings_reuse_project_config_and_one_runtime_config(
    tmp_path: Path,
) -> None:
    tool = _load_tool(
        "run_love_actions_closed_loop_settings",
        "run_love_actions_closed_loop_0287.py",
    )
    local = tmp_path / "love.ini"
    local.write_text(
        "[runtime]\n"
        "factory = configured.runtime:build_runtime\n"
        "[project]\n"
        "field_name = Statut révision\n"
        "status_value = Terminé\n",
        encoding="utf-8",
    )
    project = tmp_path / "project.ini"
    project.write_text(
        "[github]\n"
        "token_env = GITHUB_TOKEN\n"
        "[project]\n"
        "owner = newicody\n"
        "number = 3\n",
        encoding="utf-8",
    )
    args = SimpleNamespace(
        config=str(local),
        project_config=str(project),
        project_owner=None,
        project_number=None,
        project_field_name=None,
        project_status_value=None,
        runtime_factory=None,
        token_env=None,
    )
    settings = tool._resolve_local_settings(args)
    assert settings.project_owner == "newicody"
    assert settings.project_number == 3
    assert settings.project_field_name == "Statut révision"
    assert settings.project_status_value == "Terminé"
    assert settings.runtime_factory_ref == "configured.runtime:build_runtime"
    assert settings.token_env == "GITHUB_TOKEN"


def test_cli_values_override_local_configuration(tmp_path: Path) -> None:
    tool = _load_tool(
        "run_love_actions_closed_loop_settings_override",
        "run_love_actions_closed_loop_0287.py",
    )
    local = tmp_path / "love.ini"
    local.write_text(
        "[runtime]\nfactory = configured.runtime:build_runtime\n",
        encoding="utf-8",
    )
    args = SimpleNamespace(
        config=str(local),
        project_config=None,
        project_owner="operator",
        project_number=7,
        project_field_name="Final",
        project_status_value="Ready",
        runtime_factory="override.runtime:build",
        token_env="TOKEN_ENV",
    )
    settings = tool._resolve_local_settings(args)
    assert settings.project_owner == "operator"
    assert settings.project_number == 7
    assert settings.project_field_name == "Final"
    assert settings.project_status_value == "Ready"
    assert settings.runtime_factory_ref == "override.runtime:build"
    assert settings.token_env == "TOKEN_ENV"


def test_missing_runtime_configuration_has_operator_facing_error(
    tmp_path: Path,
) -> None:
    tool = _load_tool(
        "run_love_actions_closed_loop_missing_runtime",
        "run_love_actions_closed_loop_0287.py",
    )
    local = tmp_path / "love.ini"
    local.write_text("", encoding="utf-8")
    project = tmp_path / "project.ini"
    project.write_text(
        "[project]\nowner = newicody\nnumber = 3\n",
        encoding="utf-8",
    )
    args = SimpleNamespace(
        config=str(local),
        project_config=str(project),
        project_owner=None,
        project_number=None,
        project_field_name=None,
        project_status_value=None,
        runtime_factory=None,
        token_env=None,
    )
    with pytest.raises(
        tool.LoveActionsClosedLoopPreviewError,
        match="real runtime factory is not configured",
    ):
        tool._resolve_local_settings(args)
