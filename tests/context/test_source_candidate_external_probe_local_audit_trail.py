from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate_external_probe_local_audit_trail import (
    build_source_candidate_external_probe_local_audit_event,
    build_source_candidate_external_probe_local_audit_report,
    read_source_candidate_external_probe_local_audit_events,
    record_source_candidate_external_probe_operator_summary,
    render_source_candidate_external_probe_local_audit_report,
    write_source_candidate_external_probe_local_audit_report,
)


def _summary_payload() -> dict[str, object]:
    return {
        "schema": "missipy.source_candidate.external_probe_operator_summary.v1",
        "index_path": "index.json",
        "bundle_count": 2,
        "ready_count": 1,
        "check_count": 1,
        "blocked_count": 0,
        "total_artifact_count": 6,
        "total_byte_count": 456,
        "items": [],
    }


def test_local_audit_event_builds_from_operator_summary(tmp_path: Path) -> None:
    event = build_source_candidate_external_probe_local_audit_event(
        summary_path=tmp_path / "summary.json",
        summary_payload=_summary_payload(),
        created_at="2026-07-02T10:00:00+00:00",
    )

    assert event.event_kind == "external_probe_operator_summary_recorded"
    assert event.ready_count == 1
    assert event.check_count == 1
    assert event.blocked_count == 0
    assert "summary.json" in event.event_id


def test_local_audit_record_appends_jsonl_and_report(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    audit_log = tmp_path / "audit.jsonl"
    summary_path.write_text(json.dumps(_summary_payload()) + "\n", encoding="utf-8")

    record_source_candidate_external_probe_operator_summary(
        audit_log_path=audit_log,
        summary_path=summary_path,
        created_at="2026-07-02T10:00:00+00:00",
    )
    record_source_candidate_external_probe_operator_summary(
        audit_log_path=audit_log,
        summary_path=summary_path,
        created_at="2026-07-02T10:01:00+00:00",
    )

    events = read_source_candidate_external_probe_local_audit_events(audit_log)
    report = build_source_candidate_external_probe_local_audit_report(audit_log)

    assert len(events) == 2
    assert report.event_count == 2
    assert report.ready_count == 2
    assert report.check_count == 2
    assert report.blocked_count == 0


def test_local_audit_report_writes_json(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    report = build_source_candidate_external_probe_local_audit_report(tmp_path / "missing.jsonl")

    returned = write_source_candidate_external_probe_local_audit_report(output, report)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert returned == output
    assert payload["schema"] == "missipy.source_candidate.external_probe_local_audit_report.v1"
    assert payload["event_count"] == 0


def test_local_audit_report_render_is_stable(tmp_path: Path) -> None:
    text = render_source_candidate_external_probe_local_audit_report(
        build_source_candidate_external_probe_local_audit_report(tmp_path / "missing.jsonl")
    )

    assert "external probe local audit trail" in text
    assert "event_count: 0" in text
    assert "latest_event_id: <none>" in text
