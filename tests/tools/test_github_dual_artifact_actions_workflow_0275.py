from pathlib import Path

import json
import os
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def test_scripts_build_three_separate_artifacts(tmp_path):
    event = {
        "issue": {
            "number": 7,
            "title": "Build it",
            "body": "Details",
            "html_url": "https://example/7",
            "created_at": "2026-07-11T00:00:00Z",
            "labels": [{"name": "feature"}],
        },
        "repository": {"full_name": "newicody/autodoc"},
        "sender": {"login": "eric"},
    }
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")
    output_dir = tmp_path / "out"
    fake = tmp_path / "copilot"
    first_opinion = {
        "concrete_objective": "Build the requested result.",
        "expected_result": "A built result.",
        "provided_constraints": ["Details"],
        "success_criteria": ["The three artifacts are written."],
    }
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        f"print(json.dumps({first_opinion!r}))\n",
        encoding="utf-8",
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    env = dict(
        os.environ,
        GITHUB_EVENT_PATH=str(event_path),
        GITHUB_REPOSITORY="newicody/autodoc",
        GITHUB_RUN_ID="99",
        AUTODOC_OUTPUT=str(output_dir / "authoritative_request.json"),
    )
    subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "templates/github/scripts/build_autodoc_authoritative_request.py"
            ),
        ],
        env=env,
        check=True,
    )
    env.update(
        AUTODOC_REQUEST=str(output_dir / "authoritative_request.json"),
        AUTODOC_ADVISORY=str(output_dir / "copilot_advisory.json"),
        AUTODOC_COPILOT_COMMAND=str(fake),
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "templates/github/scripts/run_autodoc_copilot_advisory.py"),
        ],
        env=env,
        check=True,
    )
    env.update(AUTODOC_MANIFEST=str(output_dir / "dual_artifact_manifest.json"))
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "templates/github/scripts/build_autodoc_dual_manifest.py"),
        ],
        env=env,
        check=True,
    )
    request = json.loads(
        (output_dir / "authoritative_request.json").read_text(encoding="utf-8")
    )
    advisory = json.loads(
        (output_dir / "copilot_advisory.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (output_dir / "dual_artifact_manifest.json").read_text(encoding="utf-8")
    )
    assert request["authoritative"] is True
    assert advisory["usable_as_authority"] is False
    assert advisory["schema"] == "missipy.github.copilot_advisory.v2"
    assert manifest["request_filename"] != manifest["advisory_filename"]
