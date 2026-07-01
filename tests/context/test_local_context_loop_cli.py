from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from context.local_context_loop_cli import (
    build_local_context_loop_parser,
    command_from_args,
    run_local_context_loop,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _artifact_dir(tmp_path: Path, *, selected: int = 1) -> Path:
    directory = tmp_path / "artifacts"
    directory.mkdir()
    _write_json(
        directory / "report.json",
        {
            "query": "OpenVINO local",
            "prefixed_query": "query: OpenVINO local",
            "index": "/tmp/corpus.json",
            "model": "fake-e5",
            "backend": "fake-backend",
            "tokenizer": "fake-tokenizer",
            "dimension": 384,
            "hit_count": 1,
            "hits": [{"id": "chunk-1"}],
        },
    )
    _write_json(
        directory / "context.json",
        {
            "query": "OpenVINO local",
            "prefixed_query": "query: OpenVINO local",
            "index": "/tmp/corpus.json",
            "item_count": 1,
            "items": [{"id": "chunk-1", "excerpt": "OpenVINO E5 local"}],
        },
    )
    _write_json(
        directory / "consumed_context.json",
        {
            "query": "OpenVINO local",
            "prefixed_query": "query: OpenVINO local",
            "max_chars": 500,
            "used_chars": 46 if selected else 0,
            "available_item_count": 1,
            "selected_item_count": selected,
            "skipped_item_count": 0 if selected else 1,
            "context_text": "[1] notes.md\nOpenVINO E5 local" if selected else "",
            "items": [{"id": "chunk-1", "text": "[1] notes.md\nOpenVINO E5 local"}] if selected else [],
        },
    )
    _write_json(
        directory / "prompt.json",
        {
            "query": "OpenVINO local",
            "prefixed_query": "query: OpenVINO local",
            "selected_item_count": selected,
            "prompt_text": "[QUESTION]\nOpenVINO local\n\n[CONTEXT]\nOpenVINO E5 local" if selected else "",
        },
    )
    return directory


def test_parser_builds_typed_local_context_loop_command() -> None:
    parser = build_local_context_loop_parser()
    args = parser.parse_args([
        "artifacts",
        "--format",
        "json",
        "--component-name",
        "project_context",
        "--priority",
        "7",
        "--include-context-text",
        "--hide-prompt-text",
        "--require-ready",
        "--next-action",
        "archive",
    ])

    command = command_from_args(args)

    assert command.artifact_dir == Path("artifacts")
    assert command.render.output_format == "json"
    assert command.status.component_name == "project_context"
    assert command.decision.next_action == "archive"
    assert command.intake.runtime_policy is not None
    assert command.intake.runtime_policy.require_ready is True
    assert command.intake.attachment_policy is not None
    assert command.intake.runtime_policy.bridge_policy.component_name == "project_context"
    assert command.intake.runtime_policy.bridge_policy.priority == 7
    assert command.intake.runtime_policy.bridge_policy.include_context_text is True
    assert command.intake.runtime_policy.bridge_policy.include_prompt_text is False
    assert command.intake.attachment_policy.minimum_priority == 7


def test_local_context_loop_cli_renders_text_from_artifact_dir(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path)
    stdout = StringIO()
    stderr = StringIO()

    code = run_local_context_loop(["--next-action", "relaunch", str(directory)], stdout=stdout, stderr=stderr)

    assert code == 0
    assert stderr.getvalue() == ""
    text = stdout.getvalue()
    assert "schema: missipy.local_context_loop_cli.v1" in text
    assert "phase: 5.13" in text
    assert f"artifact_dir: {directory}" in text
    assert "ready: true" in text
    assert "mutation_applied: false" in text
    assert "next_action: relaunch" in text
    assert "component: e5_local_context" in text
    assert "attached: true" in text
    assert "query: OpenVINO local" in text
    assert "selected_item_count: 1" in text


def test_local_context_loop_cli_renders_json_from_artifact_dir(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path)
    stdout = StringIO()
    stderr = StringIO()

    code = run_local_context_loop(["--format", "json", str(directory)], stdout=stdout, stderr=stderr)

    assert code == 0
    assert stderr.getvalue() == ""
    payload = json.loads(stdout.getvalue())
    assert payload["schema"] == "missipy.local_context_loop_cli.v1"
    assert payload["phase"] == "5.13"
    assert payload["artifact_dir"] == str(directory)
    assert payload["ready"] is True
    assert payload["mutation_applied"] is False
    assert payload["next_action"] == "inspect"
    assert payload["intake"]["schema"] == "missipy.e5.context_engine_intake.v1"
    assert payload["status"]["schema"] == "missipy.e5.context_engine_status.v1"
    assert payload["status"]["attached"] is True
    assert "archive" in payload["decision_options"]


def test_local_context_loop_cli_reports_missing_artifact_dir(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    stdout = StringIO()
    stderr = StringIO()

    code = run_local_context_loop([str(missing)], stdout=stdout, stderr=stderr)

    assert code == 1
    assert stdout.getvalue() == ""
    assert "missipy-local-context-loop failed" in stderr.getvalue()


def test_local_context_loop_cli_can_require_ready_context(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path, selected=0)
    stdout = StringIO()
    stderr = StringIO()

    code = run_local_context_loop(["--require-ready", str(directory)], stdout=stdout, stderr=stderr)

    assert code == 1
    assert stdout.getvalue() == ""
    assert "status must be ready" in stderr.getvalue()


def test_local_context_loop_cli_writes_report_file(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path)
    report = tmp_path / "local_loop_report.json"
    stdout = StringIO()
    stderr = StringIO()

    code = run_local_context_loop([
        "--format",
        "json",
        "--next-action",
        "archive",
        "--report-file",
        str(report),
        str(directory),
    ], stdout=stdout, stderr=stderr)

    assert code == 0
    assert stderr.getvalue() == ""
    stdout_payload = json.loads(stdout.getvalue())
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert report_payload == stdout_payload
    assert report_payload["schema"] == "missipy.local_context_loop_cli.v1"
    assert report_payload["next_action"] == "archive"
    assert report_payload["mutation_applied"] is False


def test_local_context_loop_cli_report_file_failure_returns_error(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path)
    target_directory = tmp_path / "report.json"
    target_directory.mkdir()
    stdout = StringIO()
    stderr = StringIO()

    code = run_local_context_loop([
        "--report-file",
        str(target_directory),
        str(directory),
    ], stdout=stdout, stderr=stderr)

    assert code == 1
    assert stdout.getvalue() == ""
    assert "failed to write report" in stderr.getvalue()


def test_context_package_does_not_export_local_loop_cli_boundary() -> None:
    import context

    assert not hasattr(context, "run_local_context_loop")
    assert not hasattr(context, "build_local_context_loop_parser")
