from __future__ import annotations

import json
from pathlib import Path

from tools.build_typed_github_research_scheduler_command_0287 import main
from tests.context.test_github_research_scheduler_command_0287 import _report


def test_tool_builds_summary_without_filesystem_handoff(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "intake.json"
    source.write_text(json.dumps(_report()), encoding="utf-8")

    returncode = main(
        [
            "--input",
            str(source),
            "--max-scheduler-steps",
            "16",
            "--max-specialist-visits",
            "2",
            "--max-wall-time-s",
            "1800",
            "--format",
            "summary",
        ]
    )

    captured = capsys.readouterr()
    assert returncode == 0
    assert "status=typed-command-ready-for-sql" in captured.out
    assert "legacy_filesystem_handoff_is_canonical=false" in captured.out
    assert "sql_write_performed=false" in captured.out
    assert not list(tmp_path.glob("*.jsonl"))
