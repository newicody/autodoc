from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate_external_probe_local_replay import (
    build_source_candidate_external_probe_local_replay_report,
    read_source_candidate_external_probe_local_replay_report,
    render_source_candidate_external_probe_local_replay_report,
    write_source_candidate_external_probe_local_replay_report,
)


def _event(event_id: str, *, ready: int, check: int, blocked: int) -> dict[str, object]:
    return {
        "schema": "missipy.source_candidate.external_probe_local_audit_event.v1",
        "event_id": event_id,
        "created_at": f"2026-07-02T10:0{event_id}+00:00",
        "event_kind": "external_probe_operator_summary_recorded",
        "summary_path": f"summary-{event_id}.json",
        "bundle_count": ready + check + blocked,
        "ready_count": ready,
        "check_count": check,
        "blocked_count": blocked,
        "total_artifact_count": 3,
        "total_byte_count": 123,
    }


def _write_audit(path: Path) -> None:
    path.write_text(
        "\n".join(
            json.dumps(payload)
            for payload in (
                _event("1", ready=1, check=0, blocked=0),
                _event("2", ready=1, check=1, blocked=0),
                _event("3", ready=1, check=0, blocked=1),
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_local_replay_report_counts_statuses(tmp_path: Path) -> None:
    audit_log = tmp_path / "audit.jsonl"
    _write_audit(audit_log)

    report = build_source_candidate_external_probe_local_replay_report(audit_log)

    assert report.event_count == 3
    assert report.replayed_count == 3
    assert report.ready_event_count == 1
    assert report.check_event_count == 1
    assert report.blocked_event_count == 1
    assert report.latest_event_id == "3"


def test_local_replay_report_can_limit_latest_events(tmp_path: Path) -> None:
    audit_log = tmp_path / "audit.jsonl"
    _write_audit(audit_log)

    report = build_source_candidate_external_probe_local_replay_report(audit_log, limit=2)

    assert report.event_count == 3
    assert report.replayed_count == 2
    assert report.ready_event_count == 0
    assert report.check_event_count == 1
    assert report.blocked_event_count == 1


def test_local_replay_report_writes_and_reads_json(tmp_path: Path) -> None:
    audit_log = tmp_path / "audit.jsonl"
    output = tmp_path / "replay.json"
    _write_audit(audit_log)

    report = build_source_candidate_external_probe_local_replay_report(audit_log)
    returned = write_source_candidate_external_probe_local_replay_report(output, report)
    payload = read_source_candidate_external_probe_local_replay_report(output)

    assert returned == output
    assert payload["schema"] == "missipy.source_candidate.external_probe_local_replay_report.v1"
    assert payload["event_count"] == 3


def test_local_replay_report_render_is_stable(tmp_path: Path) -> None:
    audit_log = tmp_path / "audit.jsonl"
    _write_audit(audit_log)

    text = render_source_candidate_external_probe_local_replay_report(
        build_source_candidate_external_probe_local_replay_report(audit_log)
    )

    assert "external probe local replay" in text
    assert "event_count: 3" in text
    assert "latest_event_id: 3" in text
