from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/publish_github_copilot_advisory_v2_issue_comment_0287.py"


def _preview(path: Path) -> None:
    payload = {
        "schema": "missipy.github.copilot_advisory_publication_preview.v2",
        "source_candidate_ref": "request:42",
        "advisory_artifact_ref": "advisory:42",
        "concrete_objective": "Étudier la demande.",
        "expected_result": "Produire un premier avis.",
        "provided_constraints": ["Rester consultatif."],
        "success_criteria": ["L’avis est visible."],
        "workflow_run_ref": "github-actions-run:99",
        "response_digest": "d" * 64,
        "repository": "newicody/projects",
        "issue_number": 42,
        "advisory_schema": "missipy.github.copilot_advisory.v2",
        "request_authoritative": True,
        "advisory_is_authority": False,
        "operator_decision_required": True,
        "publication_gate_required": True,
        "github_mutation_performed": False,
        "remote_mutation_allowed": False,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _fake_gh(path: Path, state: Path) -> None:
    source = f'''#!/usr/bin/env python3
import json
from pathlib import Path
import sys
state = Path({str(state)!r})
args = sys.argv[1:]
if "--method" in args and "POST" in args:
    body_arg = next(item for item in args if item.startswith("body="))
    body = body_arg.split("=", 1)[1]
    state.write_text(body, encoding="utf-8")
    print(json.dumps({{"id": 17, "html_url": "https://example/17"}}))
elif state.exists():
    print(json.dumps([{{"id": 17, "html_url": "https://example/17", "body": state.read_text(encoding="utf-8")}}]))
else:
    print("[]")
'''
    path.write_text(source, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _run(preview: Path, gh: Path, *extra: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(TOOL),
        "--repository",
        "newicody/projects",
        "--issue-number",
        "42",
        "--preview",
        str(preview),
        "--policy-decision-id",
        "policy:copilot-v2-publish",
        "--operator-decision",
        "approve",
        "--gh-command",
        str(gh),
        "--format",
        "json",
        *extra,
    ]
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_issue_adapter_requires_digest_then_reads_back_created_comment(tmp_path: Path) -> None:
    preview = tmp_path / "preview.json"
    state = tmp_path / "comment.txt"
    gh = tmp_path / "gh"
    _preview(preview)
    _fake_gh(gh, state)

    first = _run(preview, gh)
    assert first.returncode == 0, first.stderr
    first_payload = json.loads(first.stdout)
    digest = first_payload["plan"]["plan_digest"]
    assert first_payload["plan"]["action"] == "create"
    assert first_payload["github_mutation_performed"] is False

    env = dict(os.environ)
    env["AUTODOC_REMOTE_MUTATION_ALLOWED"] = "true"
    env["AUTODOC_ISSUE_PUBLICATION_ALLOWED"] = "true"
    executed = _run(
        preview,
        gh,
        "--execute",
        "--confirm-plan-digest",
        digest,
        env=env,
    )
    assert executed.returncode == 0, executed.stderr
    payload = json.loads(executed.stdout)
    assert payload["github_mutation_performed"] is True
    assert payload["readback_verified"] is True
    assert payload["mutation_action"] == "created"

    replay = _run(preview, gh)
    replay_payload = json.loads(replay.stdout)
    assert replay_payload["plan"]["action"] == "replay"
    assert replay_payload["plan"]["plan_digest"] == digest
