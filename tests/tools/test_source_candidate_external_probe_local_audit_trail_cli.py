from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from source_candidate_external_probe_local_audit_trail_cli import main  # noqa: E402


def _write_summary(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.external_probe_operator_summary.v1",
                "index_path": "index.json",
                "bundle_count": 1,
                "ready_count": 1,
                "check_count": 0,
                "blocked_count": 0,
                "total_artifact_count": 3,
                "total_byte_count": 123,
                "items": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_local_audit_trail_cli_writes_log_and_report(tmp_path: Path, capsys) -> None:
    summary = tmp_path / "summary.json"
    audit_log = tmp_path / "audit.jsonl"
    report = tmp_path / "report.json"
    _write_summary(summary)

    exit_code = main(
        [
            "--summary",
            str(summary),
            "--audit-log",
            str(audit_log),
            "--report",
            str(report),
            "--created-at",
            "2026-07-02T10:00:00+00:00",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "external probe local audit trail" in captured.out
    assert audit_log.exists()
    assert report.exists()
    assert json.loads(report.read_text(encoding="utf-8"))["event_count"] == 1


def test_local_audit_trail_cli_prints_json(tmp_path: Path, capsys) -> None:
    summary = tmp_path / "summary.json"
    audit_log = tmp_path / "audit.jsonl"
    report = tmp_path / "report.json"
    _write_summary(summary)

    exit_code = main(
        [
            "--summary",
            str(summary),
            "--audit-log",
            str(audit_log),
            "--report",
            str(report),
            "--created-at",
            "2026-07-02T10:00:00+00:00",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema"] == "missipy.source_candidate.external_probe_local_audit_report.v1"
    assert payload["event_count"] == 1
