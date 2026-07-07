from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_github_attachment_reference_fetch_once.py"


def _config_text(dataset_root: Path) -> str:
    return f"""[dataset]
root = {dataset_root}
raw_dir = raw
index_dir = index
history_dir = history
conversion_queue_dir = conversion_queue
converted_dir = converted
vispy_events_dir = vispy_events
"""


def test_0171_fetches_referenced_attachments_to_dataset_with_fixture(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    artifact_dir.mkdir()
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    dataset = tmp_path / "dataset"

    (artifact_dir / "artifact_bundle.json").write_text(
        json.dumps(
            {
                "repository": "newicody/autodoc-ideas",
                "origin_frame_id": "github-frame:newicody/autodoc-ideas/issues/42",
                "ticket_revision_id": "github-ticket-revision:0171demo",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "attachment_manifest.json").write_text(
        json.dumps(
            {
                "repository": "newicody/autodoc-ideas",
                "origin_frame_id": "github-frame:newicody/autodoc-ideas/issues/42",
                "ticket_revision_id": "github-ticket-revision:0171demo",
                "attachments": [
                    {"url": "https://github.com/user-attachments/assets/photo.jpg", "filename": "photo.jpg"},
                    {"url": "https://github.com/user-attachments/assets/notes.txt", "filename": "notes.txt"},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (fixture / "photo.jpg").write_bytes(b"fake image\n")
    (fixture / "notes.txt").write_bytes(b"notes\n")
    config = tmp_path / "config.ini"
    config.write_text(_config_text(dataset), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--config",
            str(config),
            "--artifact-dir",
            str(artifact_dir),
            "--run-id",
            "run0171",
            "--artifact-id",
            "artifact0171",
            "--attachment-fixture-root",
            str(fixture),
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
    assert report["counts"]["reference_count"] == 2
    assert report["counts"]["fetched_count"] == 2
    assert report["counts"]["queued_count"] == 2
    assert str(report["vispy_event_path"]).startswith(str(dataset))
    assert (dataset / "raw" / "newicody__autodoc-ideas" / "run0171" / "artifact0171" / "attachments" / "photo.jpg").exists()
    assert (dataset / "raw" / "newicody__autodoc-ideas" / "run0171" / "artifact0171" / "attachments" / "notes.txt").exists()
    assert (dataset / "conversion_queue" / "run0171-artifact0171-attachments.jsonl").exists()
    assert (dataset / "vispy_events" / "run0171-artifact0171-attachments.json").exists()
