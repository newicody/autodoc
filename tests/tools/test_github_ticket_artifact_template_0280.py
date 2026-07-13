from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "templates"
    / "github"
    / "scripts"
    / "build_autodoc_ticket_artifact.py"
)


def test_ticket_artifact_builder_writes_valid_newline_terminated_json(
    tmp_path: Path,
) -> None:
    event_path = tmp_path / "event.json"
    output_dir = tmp_path / "out"
    event_path.write_text(
        json.dumps(
            {
                "action": "opened",
                "repository": {"full_name": "newicody/projects"},
                "issue": {
                    "number": 15,
                    "title": "Test controlled research",
                    "body": "column: Recherche\nrequested_depth: normal",
                    "html_url": (
                        "https://github.com/newicody/projects/issues/15"
                    ),
                    "updated_at": "2026-07-13T09:00:00Z",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    env = dict(os.environ)
    env.pop("AUTODOC_COPILOT_PRELIMINARY_SUMMARY", None)
    env["GITHUB_SHA"] = "0280-test-revision"
    subprocess.run(
        (
            sys.executable,
            str(SCRIPT),
            "--event-path",
            str(event_path),
            "--project-url",
            "https://github.com/users/newicody/projects/3",
            "--output-dir",
            str(output_dir),
        ),
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    expected = {
        "ticket_artifact.json": "missipy.github_action.ticket_artifact.v1",
        "artifact_bundle.json": (
            "missipy.github_action.ticket_artifact_bundle.v1"
        ),
    }
    for filename, schema in expected.items():
        content = (output_dir / filename).read_bytes()
        assert content.endswith(b"\n")
        assert not content.endswith(b"\n\n")
        assert json.loads(content)["schema"] == schema

    assert not (output_dir / "copilot_preliminary_opinion.json").exists()
