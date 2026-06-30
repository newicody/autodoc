from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from context.e5_artifact_cli import (
    build_e5_artifact_context_parser,
    command_from_args,
    run_e5_artifact_context,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _artifact_dir(tmp_path: Path) -> Path:
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
            "used_chars": 46,
            "available_item_count": 1,
            "selected_item_count": 1,
            "skipped_item_count": 0,
            "context_text": "[1] notes.md\nOpenVINO E5 local",
            "items": [{"id": "chunk-1", "text": "[1] notes.md\nOpenVINO E5 local"}],
        },
    )
    _write_json(
        directory / "prompt.json",
        {
            "query": "OpenVINO local",
            "prefixed_query": "query: OpenVINO local",
            "selected_item_count": 1,
            "prompt_text": "[QUESTION]\nOpenVINO local\n\n[CONTEXT]\nOpenVINO E5 local",
        },
    )
    return directory


def test_parser_builds_typed_command() -> None:
    parser = build_e5_artifact_context_parser()
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
    ])

    command = command_from_args(args)

    assert command.artifact_dir == Path("artifacts")
    assert command.render.output_format == "json"
    assert command.bridge_policy.component_name == "project_context"
    assert command.bridge_policy.priority == 7
    assert command.bridge_policy.include_context_text is True
    assert command.bridge_policy.include_prompt_text is False


def test_cli_renders_text_summary_from_artifact_dir(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path)
    stdout = StringIO()
    stderr = StringIO()

    code = run_e5_artifact_context([str(directory)], stdout=stdout, stderr=stderr)

    assert code == 0
    assert stderr.getvalue() == ""
    text = stdout.getvalue()
    assert "schema: missipy.e5.artifact_context_cli.v1" in text
    assert f"artifact_dir: {directory}" in text
    assert "component: e5_local_context" in text
    assert "status: ready" in text
    assert "query: OpenVINO local" in text
    assert "selected_item_count: 1" in text


def test_cli_renders_json_payload_from_artifact_dir(tmp_path: Path) -> None:
    directory = _artifact_dir(tmp_path)
    stdout = StringIO()
    stderr = StringIO()

    code = run_e5_artifact_context(["--format", "json", str(directory)], stdout=stdout, stderr=stderr)

    assert code == 0
    assert stderr.getvalue() == ""
    payload = json.loads(stdout.getvalue())
    assert payload["schema"] == "missipy.e5.artifact_context_cli.v1"
    assert payload["artifact_dir"] == str(directory)
    assert payload["bridge"]["component_name"] == "e5_local_context"
    feature = payload["bridge"]["features"]["e5_local_context"]
    assert feature["status"] == "ready"
    assert feature["selected_item_count"] == 1
    assert "prompt_text" in feature


def test_cli_reports_loader_errors(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    stdout = StringIO()
    stderr = StringIO()

    code = run_e5_artifact_context([str(missing)], stdout=stdout, stderr=stderr)

    assert code == 1
    assert stdout.getvalue() == ""
    assert "missipy-e5-artifact-context failed" in stderr.getvalue()


def test_context_package_does_not_export_cli_boundary() -> None:
    import context

    assert not hasattr(context, "run_e5_artifact_context")
    assert not hasattr(context, "build_e5_artifact_context_parser")
