from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_github_issue_attachment_manifest.py"


def test_0170_tool_builds_attachment_manifest_from_event(tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "action": "opened",
                "repository": {"full_name": "newicody/autodoc-ideas"},
                "issue": {
                    "number": 42,
                    "title": "Need analysis",
                    "body": "![photo.jpg](https://github.com/user-attachments/assets/photo.jpg)\n[notes.txt](https://github.com/user-attachments/assets/notes.txt)",
                    "html_url": "https://github.com/newicody/autodoc-ideas/issues/42",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--event-path",
            str(event_path),
            "--output-dir",
            str(tmp_path / "out"),
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
    manifest = json.loads((tmp_path / "out" / "attachment_manifest.json").read_text(encoding="utf-8"))

    assert report["status"] == "ok"
    assert report["attachment_count"] == 2
    assert manifest["counts"]["attachment_count"] == 2
    assert [item["kind"] for item in manifest["attachments"]] == ["image", "text"]
