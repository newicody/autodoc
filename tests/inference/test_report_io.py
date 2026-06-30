from __future__ import annotations

import json

from inference.report_io import JsonReportWritePolicy, write_json_report_atomic, write_json_report_file


def test_write_json_report_file_skips_none_path() -> None:
    result = write_json_report_file(None, {"ok": True})

    assert result.written is False
    assert result.path is None


def test_write_json_report_atomic_writes_sorted_indented_payload(tmp_path) -> None:
    report = tmp_path / "report.json"
    result = write_json_report_atomic(JsonReportWritePolicy(path=report), {"b": 2, "a": 1})

    assert result.written is True
    assert result.path == report
    assert json.loads(report.read_text(encoding="utf-8")) == {"a": 1, "b": 2}
    assert report.read_text(encoding="utf-8").endswith("\n")
    assert not (tmp_path / ".report.json.tmp").exists()


def test_json_report_policy_requires_filename() -> None:
    try:
        JsonReportWritePolicy(path=__import__("pathlib").Path("/"))
    except ValueError as exc:
        assert "filename" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")
