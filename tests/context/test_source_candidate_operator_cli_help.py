from __future__ import annotations

import os
import subprocess
import sys


_EXPECTED_COMMANDS = (
    "intake",
    "review",
    "decide",
    "review-audit",
    "report",
    "report-file",
    "bundle",
)


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src" + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def test_operator_cli_root_help_lists_expected_commands() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "context.source_candidate_operator_cli", "--help"],
        check=True,
        env=_env(),
        text=True,
        stdout=subprocess.PIPE,
    )

    assert "source_candidate_operator_cli" in result.stdout or "SourceCandidate" in result.stdout
    for command in _EXPECTED_COMMANDS:
        assert command in result.stdout


def test_operator_cli_subcommand_help_is_available() -> None:
    for command in _EXPECTED_COMMANDS:
        result = subprocess.run(
            [sys.executable, "-m", "context.source_candidate_operator_cli", command, "--help"],
            check=True,
            env=_env(),
            text=True,
            stdout=subprocess.PIPE,
        )
        assert result.stdout.strip()
