from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_github_actions_artifact_fetch_once.py"


def _config_text(dataset_root: Path) -> str:
    return f"""[github]
token_env = GITHUB_TOKEN
api_url = https://api.github.com

[project]
url = https://github.com/users/newicody/projects/2
owner = newicody
number = 2

[artifact_source]
repositories = newicody/autodoc-ideas
workflow_name = autodoc-ticket-artifact.yml
artifact_name_prefix = autodoc-ticket-artifact-

[dataset]
root = {dataset_root}
raw_dir = raw
index_dir = index
history_dir = history
conversion_queue_dir = conversion_queue
converted_dir = converted
vispy_events_dir = vispy_events

[safety]
development_repository = newicody/autodoc
allowed_repositories = newicody/autodoc-ideas
read_only_fetch = true
allow_remote_mutation = false
allow_sql_write = false
allow_qdrant_write = false

[pipeline]
queue_after_complete_sync = true
history_mode = append_only
"""


def test_0168_fetch_fixture_downloads_and_invokes_0167_dataset_sync(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset"
    config_path = tmp_path / "github_artifact_server_fetch.ini"
    config_path.write_text(_config_text(dataset_root), encoding="utf-8")

    fixture_root = tmp_path / "fixture"
    fixture_root.mkdir()
    (fixture_root / "workflow_runs.json").write_text(
        json.dumps({"workflow_runs": [{"id": 101, "status": "completed", "conclusion": "success"}]}) + "\n",
        encoding="utf-8",
    )
    (fixture_root / "run_101_artifacts.json").write_text(
        json.dumps(
            {
                "artifacts": [
                    {
                        "id": 202,
                        "name": "autodoc-ticket-artifact-42",
                        "expired": False,
                        "archive_download_url": "fixture://artifact_202.zip",
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with ZipFile(fixture_root / "artifact_202.zip", "w") as archive:
        archive.writestr(
            "artifact_bundle.json",
            json.dumps(
                {
                    "schema": "missipy.github_action.ticket_artifact_bundle.v1",
                    "origin_frame_id": "github-frame:newicody/autodoc-ideas/issues/42",
                    "ticket_revision_id": "github-ticket-revision:0168demo",
                }
            )
            + "\n",
        )
        archive.writestr("ticket_artifact.json", json.dumps({"ticket": 42}) + "\n")
        archive.writestr("attachments/notes.txt", "notes\n")
        archive.writestr("attachments/photo.jpg", "fake image\n")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--config",
            str(config_path),
            "--fixture-root",
            str(fixture_root),
            "--staging-root",
            str(tmp_path / "staging"),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    report = json.loads(completed.stdout)

    assert report["status"] == "ok"
    assert report["external_call_performed"] is False
    assert report["counts"]["downloaded_count"] == 1
    assert report["counts"]["synced_count"] == 1
    assert report["downloaded_artifacts"][0]["sync_status"] == "ok"
    assert str(report["downloaded_artifacts"][0]["sync_report"]["vispy_event_path"]).startswith(str(dataset_root))
    assert (dataset_root / "raw" / "newicody__autodoc-ideas" / "101" / "202" / "artifact_bundle.json").exists()
    assert (dataset_root / "conversion_queue").exists()
    assert Path(report["state_path"]).exists()


def test_0168_fetch_fixture_skips_already_synced_artifact(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset"
    config_path = tmp_path / "github_artifact_server_fetch.ini"
    config_path.write_text(_config_text(dataset_root), encoding="utf-8")
    fixture_root = tmp_path / "fixture"
    fixture_root.mkdir()
    (fixture_root / "workflow_runs.json").write_text(json.dumps({"workflow_runs": [{"id": 101}]}) + "\n", encoding="utf-8")
    (fixture_root / "run_101_artifacts.json").write_text(
        json.dumps({"artifacts": [{"id": 202, "name": "autodoc-ticket-artifact-42", "expired": False}]}) + "\n",
        encoding="utf-8",
    )
    with ZipFile(fixture_root / "artifact_202.zip", "w") as archive:
        archive.writestr(
            "artifact_bundle.json",
            json.dumps(
                {
                    "origin_frame_id": "github-frame:newicody/autodoc-ideas/issues/42",
                    "ticket_revision_id": "github-ticket-revision:0168demo",
                }
            )
            + "\n",
        )
        archive.writestr("ticket_artifact.json", "{}\n")

    first = subprocess.run(
        [sys.executable, str(TOOL), "--config", str(config_path), "--fixture-root", str(fixture_root), "--format", "json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    second = subprocess.run(
        [sys.executable, str(TOOL), "--config", str(config_path), "--fixture-root", str(fixture_root), "--format", "json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert json.loads(first.stdout)["counts"]["synced_count"] == 1
    second_report = json.loads(second.stdout)
    assert second_report["counts"]["downloaded_count"] == 0
    assert second_report["skipped"][0]["reason"] == "already_synced"
