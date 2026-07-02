from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate_phase7_closure_report import (
    build_source_candidate_phase7_closure_report,
    read_source_candidate_phase7_closure_report,
    render_source_candidate_phase7_closure_report,
    write_source_candidate_phase7_closure_report,
)


def test_phase7_closure_report_closes_when_required_artifacts_exist(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a\n", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "b.txt").write_text("b\n", encoding="utf-8")

    report = build_source_candidate_phase7_closure_report(
        tmp_path,
        required_artifacts=("a.txt", "nested/b.txt"),
    )

    assert report.status == "closed"
    assert report.artifact_count == 2
    assert report.missing_count == 0
    assert report.local_only is True
    assert report.remote_mutation_enabled is False
    assert report.scheduler_modified is False
    assert report.network_enabled is False
    assert report.next_phase == "8"


def test_phase7_closure_report_is_incomplete_when_artifact_is_missing(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a\n", encoding="utf-8")

    report = build_source_candidate_phase7_closure_report(
        tmp_path,
        required_artifacts=("a.txt", "missing.txt"),
    )

    assert report.status == "incomplete"
    assert report.missing_count == 1
    assert [artifact.path for artifact in report.artifacts if not artifact.exists] == ["missing.txt"]


def test_phase7_closure_report_writes_and_reads_json(tmp_path: Path) -> None:
    output = tmp_path / "closure.json"
    report = build_source_candidate_phase7_closure_report(tmp_path, required_artifacts=())

    returned = write_source_candidate_phase7_closure_report(output, report)
    payload = read_source_candidate_phase7_closure_report(output)

    assert returned == output
    assert payload["schema"] == "missipy.source_candidate.phase7_closure_report.v1"
    assert payload["status"] == "closed"


def test_phase7_closure_report_render_is_stable(tmp_path: Path) -> None:
    report = build_source_candidate_phase7_closure_report(
        tmp_path,
        required_artifacts=("missing.txt",),
    )

    text = render_source_candidate_phase7_closure_report(report)

    assert "source candidate phase 7 closure report" in text
    assert "status: incomplete" in text
    assert "- missing: missing.txt" in text
