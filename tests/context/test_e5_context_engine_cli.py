from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from context.e5_context_engine_cli import (
    build_e5_context_engine_parser,
    command_from_args,
    run_e5_context_engine,
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


def test_parser_builds_typed_context_engine_command() -> None:
    parser = build_e5_context_engine_parser()
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
    ])

    command = command_from_args(args)

    assert command.artifact_dir == Path("artifacts")
    assert command.render.output_format == "json"
    assert command.status.component_name == "project_context"
    assert command.intake.runtime_policy is not None
    assert command.intake.runtime_policy.require_ready is True
    assert command.intake.attachment_policy is not None
    assert command.intake.runtime_policy.bridge_policy.component_name == "project_context"
    assert command.intake.runtime_policy.bridge_policy.priority == 7
    assert command.intake.runtime_policy.bridge_policy.include_context_text is True
    assert command.intake.runtime_policy.bridge_policy.include_prompt_text is False
    assert command.intake.attachment_policy.minimum_priority == 7


def test_context_engine_cli_renders_text_status_from_artifact_dir(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path)
    stdout = StringIO()
    stderr = StringIO()

    code = run_e5_context_engine([str(directory)], stdout=stdout, stderr=stderr)

    assert code == 0
    assert stderr.getvalue() == ""
    text = stdout.getvalue()
    assert "schema: missipy.e5.context_engine_cli.v1" in text
    assert f"artifact_dir: {directory}" in text
    assert "ready: true" in text
    assert "changed: true" in text
    assert "component: e5_local_context" in text
    assert "attached: true" in text
    assert "query: OpenVINO local" in text
    assert "selected_item_count: 1" in text


def test_context_engine_cli_renders_json_status_from_artifact_dir(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path)
    stdout = StringIO()
    stderr = StringIO()

    code = run_e5_context_engine(["--format", "json", str(directory)], stdout=stdout, stderr=stderr)

    assert code == 0
    assert stderr.getvalue() == ""
    payload = json.loads(stdout.getvalue())
    assert payload["schema"] == "missipy.e5.context_engine_cli.v1"
    assert payload["artifact_dir"] == str(directory)
    assert payload["intake"]["schema"] == "missipy.e5.context_engine_intake.v1"
    assert payload["intake"]["ready"] is True
    assert payload["status"]["schema"] == "missipy.e5.context_engine_status.v1"
    assert payload["status"]["attached"] is True
    assert payload["status"]["selected_item_count"] == 1


def test_context_engine_cli_reports_missing_artifact_dir(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    stdout = StringIO()
    stderr = StringIO()

    code = run_e5_context_engine([str(missing)], stdout=stdout, stderr=stderr)

    assert code == 1
    assert stdout.getvalue() == ""
    assert "missipy-e5-context-engine failed" in stderr.getvalue()


def test_context_engine_cli_can_require_ready_context(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path, selected=0)
    stdout = StringIO()
    stderr = StringIO()

    code = run_e5_context_engine(["--require-ready", str(directory)], stdout=stdout, stderr=stderr)

    assert code == 1
    assert stdout.getvalue() == ""
    assert "status must be ready" in stderr.getvalue()


def test_context_package_does_not_export_context_engine_cli_boundary() -> None:
    import context

    assert not hasattr(context, "run_e5_context_engine")
    assert not hasattr(context, "build_e5_context_engine_parser")
