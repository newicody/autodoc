from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from io import TextIOBase
from types import MappingProxyType
from typing import Protocol


E5_TOOL_COMMANDS: tuple[str, ...] = (
    "embed",
    "rank",
    "build",
    "search",
    "rebuild",
    "inspect",
)


class E5ToolSubcommandHandler(Protocol):
    """Contrat d'un adaptateur de sous-commande E5."""

    def __call__(self, argv: Sequence[str], *, stdout: TextIOBase, stderr: TextIOBase) -> int:
        """Exécute la sous-commande avec ses arguments propres."""


@dataclass(frozen=True, slots=True)
class E5ToolCommand:
    """Intention typée de dispatch vers une sous-commande E5."""

    name: str
    argv: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.name not in E5_TOOL_COMMANDS:
            raise ValueError(f"unknown E5 subcommand: {self.name}")
        object.__setattr__(self, "argv", tuple(self.argv))


@dataclass(frozen=True, slots=True)
class E5ToolDispatchPolicy:
    """Politique explicite de routage des sous-commandes E5."""

    handlers: Mapping[str, E5ToolSubcommandHandler]

    def __post_init__(self) -> None:
        normalized: dict[str, E5ToolSubcommandHandler] = {}
        for name, handler in self.handlers.items():
            if name not in E5_TOOL_COMMANDS:
                raise ValueError(f"unknown E5 subcommand handler: {name}")
            normalized[name] = handler
        if not normalized:
            raise ValueError("E5ToolDispatchPolicy.handlers must not be empty")
        object.__setattr__(self, "handlers", MappingProxyType(normalized))

    def handler_for(self, command: E5ToolCommand) -> E5ToolSubcommandHandler:
        try:
            return self.handlers[command.name]
        except KeyError as exc:
            raise ValueError(f"missing E5 subcommand handler: {command.name}") from exc


def default_e5_tool_dispatch_policy() -> E5ToolDispatchPolicy:
    """Construit la politique de dispatch par défaut, avec imports paresseux."""
    return E5ToolDispatchPolicy(
        handlers={
            "embed": _run_embed,
            "rank": _run_rank,
            "build": _run_build,
            "search": _run_search,
            "rebuild": _run_rebuild,
            "inspect": _run_inspect,
        }
    )


def run_e5_tool(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIOBase | None = None,
    stderr: TextIOBase | None = None,
    dispatch_policy: E5ToolDispatchPolicy | None = None,
) -> int:
    """Point d'entrée unique des outils E5 locaux."""
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    raw = tuple(argv if argv is not None else sys.argv[1:])
    if not raw:
        err.write(_usage())
        return 2
    if raw[0] in ("-h", "--help", "help"):
        out.write(_usage())
        return 0
    try:
        command = E5ToolCommand(name=raw[0], argv=raw[1:])
        policy = dispatch_policy or default_e5_tool_dispatch_policy()
        handler = policy.handler_for(command)
    except ValueError as exc:
        err.write(f"{exc}\n")
        err.write(_usage())
        return 2
    return handler(command.argv, stdout=out, stderr=err)


def e5_tool_main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée console pour tools/e5.py."""
    return run_e5_tool(argv)


def _usage() -> str:
    commands = " | ".join(E5_TOOL_COMMANDS)
    return (
        "usage: missipy-e5 <command> [args...]\n"
        f"commands: {commands}\n"
        "\n"
        "Examples:\n"
        "  missipy-e5 embed 'query: exemple'\n"
        "  missipy-e5 search --index /tmp/corpus.json 'OpenVINO local'\n"
        "  missipy-e5 rebuild --index /tmp/corpus.json --source-dir .\n"
    )


def _run_embed(argv: Sequence[str], *, stdout: TextIOBase, stderr: TextIOBase) -> int:
    from .e5_cli import run

    return run(argv, stdout=stdout, stderr=stderr)


def _run_rank(argv: Sequence[str], *, stdout: TextIOBase, stderr: TextIOBase) -> int:
    from .e5_rank_cli import run

    return run(argv, stdout=stdout, stderr=stderr)


def _run_build(argv: Sequence[str], *, stdout: TextIOBase, stderr: TextIOBase) -> int:
    from .e5_corpus_cli import run_build

    return run_build(argv, stdout=stdout, stderr=stderr)


def _run_search(argv: Sequence[str], *, stdout: TextIOBase, stderr: TextIOBase) -> int:
    from .e5_corpus_cli import run_search

    return run_search(argv, stdout=stdout, stderr=stderr)


def _run_rebuild(argv: Sequence[str], *, stdout: TextIOBase, stderr: TextIOBase) -> int:
    from .e5_rebuild_cli import run_rebuild

    return run_rebuild(argv, stdout=stdout, stderr=stderr)


def _run_inspect(argv: Sequence[str], *, stdout: TextIOBase, stderr: TextIOBase) -> int:
    from .e5_corpus_inspect_cli import run_inspect

    return run_inspect(argv, stdout=stdout, stderr=stderr)
