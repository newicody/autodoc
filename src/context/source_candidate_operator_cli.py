from __future__ import annotations

import argparse
import importlib
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceCandidateOperatorCommandSpec:
    """Description d'une commande opérateur SourceCandidate existante."""

    module: str
    description: str


_COMMANDS: dict[str, SourceCandidateOperatorCommandSpec] = {
    "intake": SourceCandidateOperatorCommandSpec(
        module="context.source_candidate_intake_cli",
        description="create or update a local SourceCandidate",
    ),
    "review": SourceCandidateOperatorCommandSpec(
        module="context.source_candidate_review_cli",
        description="review the local SourceCandidate store",
    ),
    "decide": SourceCandidateOperatorCommandSpec(
        module="context.source_candidate_decision_cli",
        description="apply a local operator decision",
    ),
    "review-audit": SourceCandidateOperatorCommandSpec(
        module="context.source_candidate_review_audit_cli",
        description="review candidates with decision/audit summaries",
    ),
    "report": SourceCandidateOperatorCommandSpec(
        module="context.source_candidate_operator_report_cli",
        description="build a compact operator report",
    ),
    "report-file": SourceCandidateOperatorCommandSpec(
        module="context.source_candidate_operator_report_file_cli",
        description="write an operator report artifact",
    ),
    "bundle": SourceCandidateOperatorCommandSpec(
        module="context.source_candidate_operator_bundle_cli",
        description="write an operator bundle directory",
    ),
}


def command_names() -> tuple[str, ...]:
    """Retourne les commandes exposées par la surface opérateur unifiée."""

    return tuple(sorted(_COMMANDS))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="source-candidate",
        description="Unified local SourceCandidate operator command surface.",
        epilog=_format_command_epilog(),
    )
    parser.add_argument(
        "command",
        choices=command_names(),
        help="Operator command to run. Use '<command> --help' for command-specific options.",
    )
    parser.add_argument(
        "command_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded unchanged to the selected command.",
    )
    return parser


def dispatch_source_candidate_operator_command(command: str, argv: Sequence[str]) -> int:
    """Délègue vers la CLI spécialisée sans porter de logique métier."""

    try:
        spec = _COMMANDS[command]
    except KeyError as exc:
        raise ValueError(f"unknown source candidate operator command: {command}") from exc

    module = importlib.import_module(spec.module)
    main = getattr(module, "main", None)
    if main is None:
        raise ValueError(f"operator command module has no main(): {spec.module}")
    result = main(tuple(_strip_separator(argv)))
    return int(result or 0)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return dispatch_source_candidate_operator_command(args.command, args.command_args)
    except ValueError as exc:
        parser.error(str(exc))
    return 2


def _strip_separator(argv: Sequence[str]) -> tuple[str, ...]:
    if argv and argv[0] == "--":
        return tuple(argv[1:])
    return tuple(argv)


def _format_command_epilog() -> str:
    lines = ["commands:"]
    for name in command_names():
        lines.append(f"  {name:12s} {_COMMANDS[name].description}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
