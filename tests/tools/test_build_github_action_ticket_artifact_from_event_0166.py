from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_github_action_ticket_artifact_from_event.py"


def test_0166_tool_builds_ticket_bundle_from_issue_event(tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "action": "opened",
                "repository": {"full_name": "newicody/autodoc-ideas"},
                "issue": {
                    "number": 42,
                    "title": "New task",
                    "body": (
                        "Colonne workflow:\\n"
                        "Ready\\n\\n"
                        "- include_total_project\\n"
                        "- include_repository_context\\n"
                        "requested_depth: deep"
                    ),
                    "html_url": "https://github.com/newicody/autodoc-ideas/issues/42",
                    "updated_at": "2026-07-07T00:00:00Z",
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
            "--project-url",
            "https://github.com/users/newicody/projects/2",
            "--output-dir",
            str(tmp_path / "out"),
            "--copilot-summary",
            "first orientation",
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
    ticket = json.loads((tmp_path / "out" / "ticket_artifact.json").read_text(encoding="utf-8"))
    bundle = json.loads((tmp_path / "out" / "artifact_bundle.json").read_text(encoding="utf-8"))
    copilot = json.loads((tmp_path / "out" / "copilot_preliminary_opinion.json").read_text(encoding="utf-8"))

    assert report["status"] == "ok"
    assert ticket["workflow"]["column_name"] == "Ready"
    assert ticket["context_options"]["include_total_project"] is True
    assert ticket["context_options"]["include_repository_context"] is True
    assert ticket["context_options"]["requested_depth"] == "deep"
    assert bundle["artifacts"]["copilot_preliminary_opinion"]["artifact_ref"] == copilot["artifact_ref"]
    assert copilot["server_use_policy"]["usable_as_authority"] is False
