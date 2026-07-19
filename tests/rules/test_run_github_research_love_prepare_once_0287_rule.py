from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from tools import run_github_research_love_prepare_once_0287 as tool


def _args(tmp_path: Path, *, execute: bool) -> argparse.Namespace:
    return argparse.Namespace(
        project_config=tmp_path / "project.ini",
        fetch_config=tmp_path / "fetch.ini",
        scan_config=tmp_path / "scan.ini",
        runtime_config=tmp_path / "runtime.ini",
        runtime_factory="runtime_factory:create",
        policy_decision_id="policy:test:prepare-once",
        run_id="29622831972",
        existing_fetch_cycle_report=None,
        issue_number=15,
        project_owner="newicody",
        project_number=3,
        project_field_name="Résumé",
        project_status_value="Livrable final prêt",
        gh_command="gh",
        project_token_env="AUTODOC_PROJECT_TOKEN",
        max_runs=50,
        max_artifacts=150,
        max_artifact_bytes=5 * 1024 * 1024,
        working_directory=tmp_path,
        python_executable="/home/eric/python/bin/python",
        skip_openvino_compile=False,
        execute=execute,
        prepared_output=tmp_path / "prepared.json",
        output=tmp_path / "prepare-once.json",
        format="summary",
    )


def _scan_report(tmp_path: Path, *, execute: bool) -> dict:
    return {
        "valid": True,
        "mode": "execute" if execute else "plan",
        "status": "written" if execute else "plan-complete",
        "issues": [],
        "output": str(tmp_path / "scan.ini"),
        "token_env": "GITHUB_TOKEN",
    }


def _runtime_report() -> dict:
    return {
        "valid": True,
        "issues": [],
        "postgresql_ready": True,
        "qdrant_ready": True,
        "openvino_ready": True,
    }


def test_plan_validates_without_fetch_or_prepare(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        tool.scan_builder,
        "build_artifact_scan_config_report",
        lambda **kwargs: (
            calls.append("scan") or _scan_report(tmp_path, execute=False)
        ),
    )
    monkeypatch.setattr(
        tool,
        "_runtime_readiness",
        lambda *args, **kwargs: (
            calls.append("runtime") or _runtime_report()
        ),
    )
    monkeypatch.setattr(
        tool,
        "_invoke_json_main",
        lambda *args, **kwargs: pytest.fail(
            "plan mode must not fetch or prepare"
        ),
    )

    result = tool.prepare_once_report(
        _args(tmp_path, execute=False)
    )

    assert result["valid"] is True
    assert result["status"] == "ready-for-execute"
    assert result["fetch_cycle"] is None
    assert result["prepared_cycle"] is None
    assert calls == ["scan", "runtime"]
    assert result["boundaries"]["local_prepare_performed"] is False


def test_execute_fetches_then_prepares_and_stops_at_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _args(tmp_path, execute=True)
    calls: list[str] = []
    digest = "sha256:" + "7" * 64
    fetch_report_path = tmp_path / "fetch_cycle.json"

    monkeypatch.setenv("GITHUB_TOKEN", "secret")
    monkeypatch.setenv("AUTODOC_PROJECT_TOKEN", "secret")
    monkeypatch.setenv(
        "AUTODOC_QDRANT_POINT_WRITE_ALLOWED",
        "true",
    )
    monkeypatch.setenv(
        "AUTODOC_QDRANT_SEARCH_ALLOWED",
        "true",
    )
    monkeypatch.setattr(
        tool.scan_builder,
        "build_artifact_scan_config_report",
        lambda **kwargs: (
            calls.append("scan") or _scan_report(tmp_path, execute=True)
        ),
    )
    monkeypatch.setattr(
        tool,
        "_runtime_readiness",
        lambda *args, **kwargs: (
            calls.append("runtime") or _runtime_report()
        ),
    )

    def invoke(function, argv, *, label):
        calls.append(label)
        if label == "artifact fetch":
            return {
                "valid": True,
                "status": "artifacts-fetched",
                "issues": [],
                "reports": {
                    "cycle": str(fetch_report_path),
                },
            }
        return {
            "valid": True,
            "status": "publication-confirmation-required",
            "issues": [],
            "publication_plan_digest": digest,
        }

    monkeypatch.setattr(tool, "_invoke_json_main", invoke)

    result = tool.prepare_once_report(args)

    assert result["valid"] is True
    assert result["status"] == "publication-confirmation-required"
    assert result["publication_plan_digest"] == digest
    assert result["fetch_cycle_report"] == str(fetch_report_path)
    assert result["prepared_output"] == str(args.prepared_output)
    assert calls == [
        "scan",
        "runtime",
        "artifact fetch",
        "closed-loop prepare",
    ]
    assert result["boundaries"]["remote_issue_mutation_performed"] is False
    assert result["boundaries"]["project_v2_mutation_performed"] is False
    assert result["boundaries"]["operator_confirmation_required"] is True


def test_execute_reuses_explicit_fetch_cycle_without_new_fetch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _args(tmp_path, execute=True)
    existing = tmp_path / "existing-fetch-cycle.json"
    existing.write_text("{}\n", encoding="utf-8")
    args.existing_fetch_cycle_report = existing
    digest = "sha256:" + "8" * 64
    calls: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("AUTODOC_PROJECT_TOKEN", "secret")
    monkeypatch.setenv(
        "AUTODOC_QDRANT_POINT_WRITE_ALLOWED",
        "true",
    )
    monkeypatch.setenv(
        "AUTODOC_QDRANT_SEARCH_ALLOWED",
        "true",
    )
    monkeypatch.setattr(
        tool.scan_builder,
        "build_artifact_scan_config_report",
        lambda **kwargs: _scan_report(tmp_path, execute=True),
    )
    monkeypatch.setattr(
        tool,
        "_runtime_readiness",
        lambda *args, **kwargs: _runtime_report(),
    )

    def invoke(function, argv, *, label):
        calls.append((label, tuple(argv)))
        assert label == "closed-loop prepare"
        assert function is tool.closed_loop_tool.main
        return {
            "valid": True,
            "status": "publication-confirmation-required",
            "issues": [],
            "publication_plan_digest": digest,
        }

    monkeypatch.setattr(tool, "_invoke_json_main", invoke)

    result = tool.prepare_once_report(args)

    assert result["valid"] is True
    assert result["fetch_strategy"] == "reuse-existing"
    assert result["fetch_cycle_report"] == str(existing)
    assert result["fetch_cycle"]["status"] == (
        "existing-fetch-cycle-selected"
    )
    assert len(calls) == 1
    assert "--fetch-cycle-report" in calls[0][1]
    report_index = calls[0][1].index("--fetch-cycle-report") + 1
    assert calls[0][1][report_index] == str(existing)
    assert result["boundaries"]["artifact_fetch_performed"] is False
    assert result["boundaries"]["existing_fetch_cycle_reused"] is True
    assert (
        result["boundaries"]["automatic_historical_fallback_performed"]
        is False
    )


def test_missing_existing_fetch_cycle_fails_before_runtime(
    tmp_path: Path,
) -> None:
    args = _args(tmp_path, execute=True)
    args.existing_fetch_cycle_report = tmp_path / "missing.json"

    with pytest.raises(
        tool.GitHubResearchLovePrepareOnceError,
        match="existing fetch cycle report does not exist",
    ):
        tool.prepare_once_report(args)


def test_missing_effect_gate_blocks_before_fetch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        tool.scan_builder,
        "build_artifact_scan_config_report",
        lambda **kwargs: _scan_report(tmp_path, execute=True),
    )
    monkeypatch.setattr(
        tool,
        "_runtime_readiness",
        lambda *args, **kwargs: _runtime_report(),
    )
    monkeypatch.delenv(
        "AUTODOC_QDRANT_POINT_WRITE_ALLOWED",
        raising=False,
    )
    monkeypatch.setenv(
        "AUTODOC_QDRANT_SEARCH_ALLOWED",
        "true",
    )
    monkeypatch.setattr(
        tool,
        "_invoke_json_main",
        lambda *args, **kwargs: pytest.fail(
            "fetch must not run without write gate"
        ),
    )

    with pytest.raises(
        tool.GitHubResearchLovePrepareOnceError,
        match="AUTODOC_QDRANT_POINT_WRITE_ALLOWED",
    ):
        tool.prepare_once_report(_args(tmp_path, execute=True))


def test_failed_fetch_blocks_prepare(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "secret")
    monkeypatch.setenv("AUTODOC_PROJECT_TOKEN", "secret")
    monkeypatch.setenv(
        "AUTODOC_QDRANT_POINT_WRITE_ALLOWED",
        "true",
    )
    monkeypatch.setenv(
        "AUTODOC_QDRANT_SEARCH_ALLOWED",
        "true",
    )
    monkeypatch.setattr(
        tool.scan_builder,
        "build_artifact_scan_config_report",
        lambda **kwargs: _scan_report(tmp_path, execute=True),
    )
    monkeypatch.setattr(
        tool,
        "_runtime_readiness",
        lambda *args, **kwargs: _runtime_report(),
    )

    calls = 0

    def invoke(function, argv, *, label):
        nonlocal calls
        calls += 1
        assert label == "artifact fetch"
        return {
            "valid": False,
            "status": "scan-failed",
            "issues": ["artifact scan failed"],
        }

    monkeypatch.setattr(tool, "_invoke_json_main", invoke)

    result = tool.prepare_once_report(
        _args(tmp_path, execute=True)
    )

    assert result["valid"] is False
    assert result["status"] == "artifact-fetch-failed"
    assert result["prepared_cycle"] is None
    assert calls == 1


def test_main_writes_operator_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "report.json"
    prepared = tmp_path / "prepared.json"
    monkeypatch.setattr(
        tool,
        "prepare_once_report",
        lambda args: {
            "schema": tool.SCHEMA,
            "valid": True,
            "mode": "plan",
            "status": "ready-for-execute",
            "issues": [],
            "publication_plan_digest": "",
            "prepared_output": str(prepared),
            "boundaries": {},
        },
    )

    exit_code = tool.main(
        (
            "--project-config",
            str(tmp_path / "project.ini"),
            "--fetch-config",
            str(tmp_path / "fetch.ini"),
            "--runtime-config",
            str(tmp_path / "runtime.ini"),
            "--policy-decision-id",
            "policy:test:prepare-once",
            "--run-id",
            "29622831972",
            "--issue-number",
            "15",
            "--project-owner",
            "newicody",
            "--project-number",
            "3",
            "--prepared-output",
            str(prepared),
            "--output",
            str(output),
        )
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["status"] == "ready-for-execute"
    assert output.with_suffix(".json.tmp").exists() is False


def test_tool_is_only_an_operator_composition_surface() -> None:
    source = Path(tool.__file__).read_text(encoding="utf-8")

    assert "build_artifact_scan_config_report(" in source
    assert "load_manual_installed_runtime_settings(" in source
    assert "inspect_manual_runtime_readiness(" in source
    assert "fetch_tool.main" in source
    assert "closed_loop_tool.main" in source
    assert "--existing-fetch-cycle-report" in source
    assert "automatic_historical_fallback_performed" in source
    assert "publication-confirmation-required" in source

    for forbidden in (
        "Scheduler(",
        "Dispatcher(",
        "EventBus(",
        "QdrantClient(",
        "psycopg.connect(",
        "openvino.Core(",
        "updateProjectV2ItemFieldValue",
        "create_comment(",
        "subprocess.run(",
        "requests.",
    ):
        assert forbidden not in source
