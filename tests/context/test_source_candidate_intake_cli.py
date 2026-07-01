from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from context.source_candidate_intake_cli import (
    command_from_args,
    main,
    run_source_candidate_intake,
)


def _args(tmp_path: Path, **overrides: object) -> Namespace:
    values = {
        "store_file": str(tmp_path / "source_candidates.json"),
        "title": "Review local artifact",
        "body": "artifact-dir needs inspection",
        "body_file": None,
        "origin_kind": "artifact_dir",
        "origin_reference": "/tmp/autodoc_e5_dry_run",
        "repository": "newicody/autodoc",
        "label": ["local", "e5"],
        "metadata": ["phase=6.1"],
        "id_prefix": "sc",
        "default_status": "new",
        "decision": None,
        "reason": "",
        "target_context_id": None,
        "report_file": str(tmp_path / "source_candidate_intake_report.json"),
        "format": "json",
    }
    values.update(overrides)
    return Namespace(**values)


def test_source_candidate_intake_writes_store_and_report(tmp_path: Path) -> None:
    command = command_from_args(_args(tmp_path))

    result = run_source_candidate_intake(command)

    store_payload = json.loads((tmp_path / "source_candidates.json").read_text(encoding="utf-8"))
    report_payload = json.loads((tmp_path / "source_candidate_intake_report.json").read_text(encoding="utf-8"))
    assert result.candidate_id.startswith("sc-")
    assert store_payload["schema"] == "missipy.source_candidate.store.v1"
    assert store_payload["candidate_count"] == 1
    assert store_payload["candidates"][0]["origin"]["repository"] == "newicody/autodoc"
    assert report_payload["schema"] == "missipy.source_candidate.store_report.v1"


def test_source_candidate_intake_applies_optional_decision(tmp_path: Path) -> None:
    command = command_from_args(_args(tmp_path, decision="archive", reason="duplicate local note"))

    result = run_source_candidate_intake(command)

    assert result.status == "archived"
    assert result.candidate.terminal is True
    assert result.to_json_dict()["decision"] == {
        "action": "archive",
        "reason": "duplicate local note",
        "target_context_id": None,
        "resulting_status": "archived",
    }


def test_source_candidate_intake_replaces_same_candidate_deterministically(tmp_path: Path) -> None:
    command = command_from_args(_args(tmp_path))

    first = run_source_candidate_intake(command)
    second = run_source_candidate_intake(command)

    assert first.candidate_id == second.candidate_id
    assert first.write_result.inserted is True
    assert second.write_result.inserted is False
    assert second.write_result.replaced is True


def test_source_candidate_intake_cli_json_stdout(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--store-file",
            str(tmp_path / "source_candidates.json"),
            "--title",
            "Manual source",
            "--body",
            "manual body",
            "--origin-kind",
            "manual",
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema"] == "missipy.source_candidate.intake_cli.v1"
    assert payload["candidate"]["title"] == "Manual source"
    assert payload["store_path"].endswith("source_candidates.json")


def test_source_candidate_intake_cli_reads_body_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    body_file = tmp_path / "body.txt"
    body_file.write_text("body from file", encoding="utf-8")

    main(
        [
            "--store-file",
            str(tmp_path / "source_candidates.json"),
            "--title",
            "File body source",
            "--body-file",
            str(body_file),
            "--origin-kind",
            "file",
            "--origin-reference",
            str(body_file),
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["candidate"]["body"] == "body from file"
    assert payload["candidate"]["origin"]["kind"] == "file"


def test_source_candidate_intake_cli_rejects_invalid_metadata(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "--store-file",
                str(tmp_path / "source_candidates.json"),
                "--title",
                "Bad metadata",
                "--body",
                "body",
                "--metadata",
                "missing-separator",
            ]
        )
