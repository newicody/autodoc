from __future__ import annotations

from pathlib import Path

import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
ADVISORY_SCRIPT = ROOT / "templates/github/scripts/run_autodoc_copilot_advisory.py"
REQUEST_SCRIPT = ROOT / "templates/github/scripts/build_autodoc_authoritative_request.py"


def _request_payload() -> dict[str, object]:
    return {
        "schema": "missipy.github.authoritative_request.v1",
        "origin_frame_id": "github-frame:newicody/projects:1:test",
        "ticket_revision_id": "github-ticket-revision:test",
        "artifact_ref": "github-request:newicody/projects:1:test",
        "title": "Research request",
        "body": "Analyze the requested topic.",
        "labels": ["research"],
    }


def _fake_command(path: Path, body: str) -> Path:
    path.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    path.chmod(0o755)
    return path


def _run_advisory(
    tmp_path: Path,
    command: Path,
    *,
    required: bool = False,
) -> subprocess.CompletedProcess[str]:
    request_path = tmp_path / "request.json"
    advisory_path = tmp_path / "advisory.json"
    request_path.write_text(json.dumps(_request_payload()), encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "AUTODOC_REQUEST": str(request_path),
            "AUTODOC_ADVISORY": str(advisory_path),
            "AUTODOC_COPILOT_COMMAND": str(command),
            "AUTODOC_COPILOT_REQUIRED": "true" if required else "false",
        }
    )
    return subprocess.run(
        [sys.executable, str(ADVISORY_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_copilot_cli_failure_is_non_blocking_by_default(tmp_path: Path) -> None:
    command = _fake_command(
        tmp_path / "copilot-fail",
        'import sys\nprint("sensitive diagnostic", file=sys.stderr)\nraise SystemExit(7)\n',
    )
    stale = tmp_path / "advisory.json"
    stale.write_text('{"stale": true}\n', encoding="utf-8")

    result = _run_advisory(tmp_path, command)

    assert result.returncode == 0
    assert "exit_status:7" in result.stderr
    assert "sensitive diagnostic" not in result.stderr
    assert not stale.exists()


def test_copilot_cli_failure_can_be_required(tmp_path: Path) -> None:
    command = _fake_command(tmp_path / "copilot-fail", "raise SystemExit(9)\n")

    result = _run_advisory(tmp_path, command, required=True)

    assert result.returncode == 1
    assert "exit_status:9" in result.stderr
    assert not (tmp_path / "advisory.json").exists()


def test_invalid_copilot_response_is_non_blocking(tmp_path: Path) -> None:
    command = _fake_command(tmp_path / "copilot-invalid", 'print("not json")\n')

    result = _run_advisory(tmp_path, command)

    assert result.returncode == 0
    assert "invalid_response:JSONDecodeError" in result.stderr
    assert not (tmp_path / "advisory.json").exists()


def test_valid_copilot_response_builds_non_authoritative_artifact(
    tmp_path: Path,
) -> None:
    response = {
        "summary": "Advisory summary",
        "suggested_route": "research",
        "assumptions": [],
        "questions": [],
        "risks": ["advisory_only"],
        "confidence": 0.5,
    }
    command = _fake_command(
        tmp_path / "copilot-ok",
        f"import json\nprint(json.dumps({response!r}))\n",
    )

    result = _run_advisory(tmp_path, command)

    assert result.returncode == 0, result.stderr
    payload = json.loads((tmp_path / "advisory.json").read_text(encoding="utf-8"))
    assert payload["trusted"] is False
    assert payload["usable_as_hint"] is True
    assert payload["usable_as_authority"] is False
    assert payload["summary"] == "Advisory summary"


def _run_request(tmp_path: Path, event: dict[str, object]) -> subprocess.CompletedProcess[str]:
    event_path = tmp_path / "event.json"
    output_path = tmp_path / "request.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_EVENT_PATH": str(event_path),
            "AUTODOC_OUTPUT": str(output_path),
        }
    )
    return subprocess.run(
        [sys.executable, str(REQUEST_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_authoritative_request_rejects_missing_issue(tmp_path: Path) -> None:
    result = _run_request(
        tmp_path,
        {"repository": {"full_name": "newicody/projects"}},
    )

    assert result.returncode != 0
    assert "GitHub event issue must be a JSON object" in result.stderr
    assert not (tmp_path / "request.json").exists()


def test_authoritative_request_accepts_title_only_issue(tmp_path: Path) -> None:
    result = _run_request(
        tmp_path,
        {
            "issue": {
                "number": 8,
                "title": "Real request",
                "body": None,
                "labels": [],
            },
            "repository": {"full_name": "newicody/projects"},
            "sender": {"login": "newicody"},
        },
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads((tmp_path / "request.json").read_text(encoding="utf-8"))
    assert payload["issue_number"] == 8
    assert payload["title"] == "Real request"
    assert payload["body"] == ""


def test_authoritative_request_prefers_controlled_event_path(tmp_path: Path) -> None:
    native_event_path = tmp_path / "native-workflow-dispatch.json"
    controlled_event_path = tmp_path / "controlled-issue-event.json"
    output_path = tmp_path / "request.json"

    native_event_path.write_text(
        json.dumps({"inputs": {"issue_number": "8"}}),
        encoding="utf-8",
    )
    controlled_event_path.write_text(
        json.dumps(
            {
                "issue": {
                    "number": 8,
                    "title": "Controlled request",
                    "body": "Research this issue.",
                    "labels": [],
                },
                "repository": {"full_name": "newicody/projects"},
                "sender": {"login": "newicody"},
            }
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env.update(
        {
            "GITHUB_EVENT_PATH": str(native_event_path),
            "AUTODOC_EVENT_PATH": str(controlled_event_path),
            "AUTODOC_OUTPUT": str(output_path),
        }
    )
    result = subprocess.run(
        [sys.executable, str(REQUEST_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["issue_number"] == 8
    assert payload["title"] == "Controlled request"
