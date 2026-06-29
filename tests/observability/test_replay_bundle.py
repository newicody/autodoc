from __future__ import annotations

import json
from pathlib import Path

import pytest

from contracts.replay import (
    ReplayEvent,
    ReplayPlan,
    ReplayScenario,
)
from observability.replay_scenario import ReplayScenarioRunner
from observability.replay_bundle import ReplayReportBundleWriter


def make_report():
    plan = ReplayPlan(
        events=(
            ReplayEvent(
                original_id="evt-1",
                type="TICK",
                source="dummy",
                dest="scheduler",
                priority=0,
                timestamp_ns=1,
            ),
        ),
        source_record_count=1,
    )
    scenario = ReplayScenario(name="ok", plan=plan)
    return ReplayScenarioRunner().report((scenario,))


def test_replay_bundle_writer_writes_text_json_and_manifest(tmp_path: Path) -> None:
    writer = ReplayReportBundleWriter()

    result = writer.write(make_report(), tmp_path / "bundle", create_parents=True)

    text_path = tmp_path / "bundle" / "report.txt"
    json_path = tmp_path / "bundle" / "report.json"
    manifest_path = tmp_path / "bundle" / "manifest.json"

    assert text_path.exists()
    assert json_path.exists()
    assert manifest_path.exists()
    assert result.file_count == 2
    assert result.total_bytes_written > 0
    assert result.manifest.path == str(manifest_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "missipy.replay.bundle.v1"
    assert [entry["path"] for entry in manifest["files"]] == [
        "report.txt",
        "report.json",
    ]
    assert set(result.sha256_by_path) == {
        str(text_path),
        str(json_path),
        str(manifest_path),
    }


def test_replay_bundle_writer_requires_existing_directory_without_create_parents(
    tmp_path: Path,
) -> None:
    writer = ReplayReportBundleWriter()

    with pytest.raises(FileNotFoundError):
        writer.write(make_report(), tmp_path / "missing")


def test_replay_bundle_writer_refuses_overwrite_by_default(tmp_path: Path) -> None:
    writer = ReplayReportBundleWriter()
    bundle_dir = tmp_path / "bundle"
    writer.write(make_report(), bundle_dir, create_parents=True)

    with pytest.raises(FileExistsError):
        writer.write(make_report(), bundle_dir)


def test_replay_bundle_writer_is_deterministic_with_overwrite(tmp_path: Path) -> None:
    writer = ReplayReportBundleWriter()
    bundle_dir = tmp_path / "bundle"

    first = writer.write(make_report(), bundle_dir, create_parents=True)
    second = writer.write(make_report(), bundle_dir, overwrite=True)

    assert first.sha256_by_path == second.sha256_by_path
