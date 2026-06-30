from __future__ import annotations

from io import StringIO
from typing import Sequence

import pytest

from inference.e5_tool_cli import (
    E5_TOOL_COMMANDS,
    E5ToolCommand,
    E5ToolDispatchPolicy,
    run_e5_tool,
)


def test_e5_tool_command_accepts_known_subcommands_only() -> None:
    assert E5ToolCommand("search", ("--index", "corpus.json", "query")).argv == (
        "--index",
        "corpus.json",
        "query",
    )

    with pytest.raises(ValueError, match="unknown E5 subcommand"):
        E5ToolCommand("unknown")


def test_e5_tool_dispatch_policy_rejects_unknown_handler_name() -> None:
    with pytest.raises(ValueError, match="unknown E5 subcommand handler"):
        E5ToolDispatchPolicy({"unknown": _handler(0)})


def test_e5_tool_help_does_not_import_runtime_handlers() -> None:
    stdout = StringIO()
    stderr = StringIO()

    code = run_e5_tool(["--help"], stdout=stdout, stderr=stderr)

    assert code == 0
    assert "usage: missipy-e5 <command>" in stdout.getvalue()
    for command in E5_TOOL_COMMANDS:
        assert command in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_e5_tool_dispatches_to_selected_handler_only() -> None:
    calls: list[tuple[str, tuple[str, ...]]] = []

    def search_handler(argv: Sequence[str], *, stdout: StringIO, stderr: StringIO) -> int:
        calls.append(("search", tuple(argv)))
        stdout.write("handled search\n")
        assert stderr.getvalue() == ""
        return 7

    policy = E5ToolDispatchPolicy({"search": search_handler})
    stdout = StringIO()
    stderr = StringIO()

    code = run_e5_tool(
        ["search", "--index", "/tmp/corpus.json", "OpenVINO local"],
        stdout=stdout,
        stderr=stderr,
        dispatch_policy=policy,
    )

    assert code == 7
    assert calls == [("search", ("--index", "/tmp/corpus.json", "OpenVINO local"))]
    assert stdout.getvalue() == "handled search\n"
    assert stderr.getvalue() == ""


def test_e5_tool_rejects_missing_or_unknown_subcommand() -> None:
    stderr = StringIO()

    assert run_e5_tool([], stdout=StringIO(), stderr=stderr) == 2
    assert "usage: missipy-e5" in stderr.getvalue()

    stderr = StringIO()
    assert run_e5_tool(["missing"], stdout=StringIO(), stderr=stderr) == 2
    assert "unknown E5 subcommand: missing" in stderr.getvalue()


def _handler(code: int):
    def handler(argv: Sequence[str], *, stdout: StringIO, stderr: StringIO) -> int:
        return code

    return handler
