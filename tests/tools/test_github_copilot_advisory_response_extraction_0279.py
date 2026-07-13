from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "templates/github/scripts/run_autodoc_copilot_advisory.py"


def _load_module():
    spec = spec_from_file_location("copilot_advisory_0279", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _advisory() -> dict[str, object]:
    return {
        "summary": "Advisory summary",
        "suggested_route": "research",
        "assumptions": ["Issue content is authoritative"],
        "questions": [],
        "risks": ["advisory_only"],
        "confidence": 0.75,
    }


def _request() -> dict[str, object]:
    return {
        "origin_frame_id": "github-frame:newicody/projects:15:test",
        "ticket_revision_id": "github-ticket-revision:test",
        "artifact_ref": "github-request:newicody/projects:15:test",
        "title": "Research request",
        "body": "Analyze the requested topic.",
        "labels": ["research"],
    }


def _fake_copilot(path: Path, stdout: str) -> Path:
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"sys.stdout.write({stdout!r})\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def test_extracts_advisory_from_jsonl_assistant_message() -> None:
    module = _load_module()
    advisory = _advisory()
    stdout = "\n".join(
        (
            json.dumps({"type": "session.start", "data": {"id": "s1"}}),
            json.dumps(
                {
                    "type": "assistant.message",
                    "data": {"content": json.dumps(advisory)},
                }
            ),
        )
    )

    assert module.extract_advisory(stdout) == advisory


def test_extracts_fenced_or_surrounded_advisory() -> None:
    module = _load_module()
    advisory = _advisory()
    fenced = "```json\n" + json.dumps(advisory) + "\n```"
    surrounded = "Result follows:\n" + json.dumps(advisory) + "\nDone."

    assert module.extract_advisory(fenced) == advisory
    assert module.extract_advisory(surrounded) == advisory


def test_rejects_invalid_advisory_types_and_confidence() -> None:
    module = _load_module()
    invalid_list = _advisory() | {"risks": "not-a-list"}
    invalid_confidence = _advisory() | {"confidence": 2.0}

    for payload in (invalid_list, invalid_confidence):
        try:
            module.extract_advisory(json.dumps(payload))
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("invalid advisory was accepted")


def test_jsonl_cli_response_builds_advisory_artifact(tmp_path: Path) -> None:
    advisory = _advisory()
    jsonl = json.dumps(
        {
            "type": "assistant.message",
            "data": {"content": json.dumps(advisory)},
        }
    ) + "\n"
    command = _fake_copilot(tmp_path / "copilot", jsonl)
    request_path = tmp_path / "request.json"
    output_path = tmp_path / "advisory.json"
    request_path.write_text(json.dumps(_request()), encoding="utf-8")

    env = os.environ.copy()
    env.update(
        {
            "AUTODOC_REQUEST": str(request_path),
            "AUTODOC_ADVISORY": str(output_path),
            "AUTODOC_COPILOT_COMMAND": str(command),
            "AUTODOC_COPILOT_REQUIRED": "true",
        }
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["summary"] == advisory["summary"]
    assert payload["confidence"] == 0.75
    assert payload["trusted"] is False
    assert payload["usable_as_authority"] is False


def test_cli_uses_structured_transport_and_denies_tools() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    for marker in (
        '"--output-format=json"',
        '"--stream=off"',
        '"--no-color"',
        '"--no-custom-instructions"',
        '"--deny-tool=read"',
        '"--deny-tool=write"',
        '"--deny-tool=shell"',
        '"--deny-tool=url"',
        '"--deny-tool=memory"',
    ):
        assert marker in text
