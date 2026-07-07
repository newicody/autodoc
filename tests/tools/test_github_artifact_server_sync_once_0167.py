from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_github_artifact_server_sync_once.py"


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


def test_0167_server_sync_copies_artifact_and_queues_attachments(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "downloaded"
    attachments = artifact_dir / "attachments"
    attachments.mkdir(parents=True)

    (artifact_dir / "artifact_bundle.json").write_text(
        json.dumps(
            {
                "schema": "missipy.github_action.ticket_artifact_bundle.v1",
                "origin_frame_id": "github-frame:newicody/autodoc-ideas/issues/42",
                "ticket_revision_id": "github-ticket-revision:0167demo",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "ticket_artifact.json").write_text(json.dumps({"ticket": 42}) + "\n", encoding="utf-8")
    (attachments / "photo.jpg").write_text("fake image\n", encoding="utf-8")
    (attachments / "notes.txt").write_text("notes\n", encoding="utf-8")

    config_path = tmp_path / "github_artifact_server_fetch.ini"
    config_path.write_text(_config_text(tmp_path / "dataset"), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--config",
            str(config_path),
            "--artifact-dir",
            str(artifact_dir),
            "--run-id",
            "run0167",
            "--artifact-id",
            "artifact0167",
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

    assert str(report["vispy_event_path"]).startswith(str(tmp_path / "dataset"))
    assert report["status"] == "ok"
    assert report["counts"]["attachment_count"] == 2
    assert report["counts"]["queued_count"] == 2
    assert len(report["attachments"]) == 2
    assert len(report["queue_records"]) == 2
    assert report["artifact_record"]["status"] == "synced"
    assert Path(report["vispy_event_path"]).exists()
    assert (tmp_path / "dataset" / "conversion_queue").exists()
    assert (tmp_path / "dataset" / "raw").exists()
