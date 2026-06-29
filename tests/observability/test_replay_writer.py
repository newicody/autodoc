from __future__ import annotations

import hashlib

from contracts.replay import ReplayReportExport, ReplayReportWriteResult
from observability.replay_writer import ReplayReportFileWriter


def make_export(content: str = "ReplayReport: OK\n") -> ReplayReportExport:
    return ReplayReportExport(
        format="text",
        media_type="text/plain; charset=utf-8",
        content=content,
    )


def test_replay_report_file_writer_writes_explicit_path(tmp_path) -> None:
    export = make_export()
    target = tmp_path / "report.txt"
    writer = ReplayReportFileWriter()

    result = writer.write(export, target)

    assert isinstance(result, ReplayReportWriteResult)
    assert target.read_text(encoding="utf-8") == export.content
    assert result.path == str(target)
    assert result.format == "text"
    assert result.media_type == export.media_type
    assert result.bytes_written == len(export.content.encode("utf-8"))
    assert result.sha256 == hashlib.sha256(export.content.encode("utf-8")).hexdigest()


def test_replay_report_file_writer_refuses_existing_file_without_overwrite(tmp_path) -> None:
    target = tmp_path / "report.txt"
    target.write_text("old", encoding="utf-8")
    writer = ReplayReportFileWriter()

    try:
        writer.write(make_export("new"), target)
    except FileExistsError:
        pass
    else:  # pragma: no cover
        raise AssertionError("existing files must not be overwritten by default")

    assert target.read_text(encoding="utf-8") == "old"


def test_replay_report_file_writer_overwrites_when_explicit(tmp_path) -> None:
    target = tmp_path / "report.txt"
    target.write_text("old", encoding="utf-8")
    writer = ReplayReportFileWriter()

    result = writer.write(make_export("new"), target, overwrite=True)

    assert target.read_text(encoding="utf-8") == "new"
    assert result.bytes_written == 3


def test_replay_report_file_writer_parent_creation_is_explicit(tmp_path) -> None:
    target = tmp_path / "nested" / "report.txt"
    writer = ReplayReportFileWriter()

    try:
        writer.write(make_export(), target)
    except FileNotFoundError as exc:
        assert "parent directory" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("missing parent must be rejected by default")

    result = writer.write(make_export(), target, create_parents=True)

    assert target.exists()
    assert result.path == str(target)


def test_replay_report_write_result_validates_metadata() -> None:
    try:
        ReplayReportWriteResult(
            path="report.txt",
            format="text",
            media_type="text/plain",
            bytes_written=-1,
            sha256="0" * 64,
        )
    except ValueError as exc:
        assert "bytes_written" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("negative bytes_written must be rejected")

    try:
        ReplayReportWriteResult(
            path="report.txt",
            format="text",
            media_type="text/plain",
            bytes_written=0,
            sha256="bad",
        )
    except ValueError as exc:
        assert "sha256" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("invalid sha256 must be rejected")
