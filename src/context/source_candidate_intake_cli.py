from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .source_candidate import (
    SourceCandidate,
    SourceCandidateCreationResult,
    SourceCandidateDecision,
    SourceCandidateInput,
    SourceCandidateOrigin,
    SourceCandidatePolicy,
    allowed_source_candidate_decisions,
    allowed_source_candidate_statuses,
    apply_source_candidate_decision,
    build_source_candidate,
)
from .source_candidate_store import (
    SourceCandidateReportPolicy,
    SourceCandidateStorePolicy,
    SourceCandidateStoreWriteResult,
    upsert_source_candidate,
)

_INTAKE_SCHEMA = "missipy.source_candidate.intake_cli.v1"
_ALLOWED_FORMATS = frozenset({"text", "json"})


@dataclass(frozen=True, slots=True)
class SourceCandidateIntakeRenderPolicy:
    """Politique de rendu de la CLI SourceCandidate locale."""

    output_format: str = "text"

    def __post_init__(self) -> None:
        if self.output_format not in _ALLOWED_FORMATS:
            raise ValueError("output_format must be text or json")


@dataclass(frozen=True, slots=True)
class SourceCandidateIntakeCommand:
    """Commande normalisée avant création et upsert local d'une SourceCandidate."""

    candidate_input: SourceCandidateInput
    candidate_policy: SourceCandidatePolicy
    store_policy: SourceCandidateStorePolicy
    report_policy: SourceCandidateReportPolicy
    render_policy: SourceCandidateIntakeRenderPolicy
    decision: SourceCandidateDecision | None = None


@dataclass(frozen=True, slots=True)
class SourceCandidateIntakeResult:
    """Résultat stable de l'intake CLI local SourceCandidate."""

    creation: SourceCandidateCreationResult
    candidate: SourceCandidate
    write_result: SourceCandidateStoreWriteResult
    decision: SourceCandidateDecision | None
    report_path: Path | None

    @property
    def candidate_id(self) -> str:
        return self.candidate.candidate_id

    @property
    def status(self) -> str:
        return self.candidate.status

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "schema": _INTAKE_SCHEMA,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "terminal": self.candidate.terminal,
            "actionable": self.candidate.actionable,
            "decision": self.decision.to_json_dict() if self.decision is not None else None,
            "store_path": str(self.write_result.path),
            "report_path": str(self.report_path) if self.report_path is not None else None,
            "inserted": self.write_result.inserted,
            "replaced": self.write_result.replaced,
            "candidate_count": self.write_result.snapshot.candidate_count,
            "candidate": self.candidate.to_json_dict(),
            "creation": self.creation.to_json_dict(),
            "write_result": self.write_result.to_json_dict(),
        }

    def to_text(self) -> str:
        lines = [
            "SourceCandidate intake",
            f"schema: {_INTAKE_SCHEMA}",
            f"candidate_id: {self.candidate_id}",
            f"title: {self.candidate.title}",
            f"status: {self.status}",
            f"terminal: {str(self.candidate.terminal).lower()}",
            f"actionable: {str(self.candidate.actionable).lower()}",
            f"store_path: {self.write_result.path}",
            f"inserted: {str(self.write_result.inserted).lower()}",
            f"replaced: {str(self.write_result.replaced).lower()}",
            f"candidate_count: {self.write_result.snapshot.candidate_count}",
        ]
        if self.decision is not None:
            lines.append(f"decision: {self.decision.action}")
        if self.report_path is not None:
            lines.append(f"report_path: {self.report_path}")
        return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="source-candidate-intake",
        description="Create or update one local SourceCandidate in a JSON store.",
    )
    parser.add_argument("--store-file", required=True, help="SourceCandidate JSON store file to update.")
    parser.add_argument("--title", required=True, help="Candidate title.")
    body_group = parser.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body", help="Candidate body text.")
    body_group.add_argument("--body-file", help="File containing the candidate body text.")
    parser.add_argument(
        "--origin-kind",
        default="manual",
        choices=("local", "file", "artifact_dir", "github", "manual"),
        help="Candidate origin kind.",
    )
    parser.add_argument("--origin-reference", default="", help="Origin reference, path, issue id or free-form source id.")
    parser.add_argument("--repository", default="newicody/autodoc", help="Repository projection namespace.")
    parser.add_argument("--label", action="append", default=[], help="Candidate label. May be repeated.")
    parser.add_argument("--metadata", action="append", default=[], help="Metadata entry key=value. May be repeated.")
    parser.add_argument("--id-prefix", default="sc", help="Candidate id prefix.")
    parser.add_argument(
        "--default-status",
        default="new",
        choices=allowed_source_candidate_statuses(),
        help="Initial candidate status before an optional decision.",
    )
    parser.add_argument(
        "--decision",
        choices=allowed_source_candidate_decisions(),
        help="Optional operator decision to apply before writing the candidate.",
    )
    parser.add_argument("--reason", default="", help="Optional decision reason.")
    parser.add_argument("--target-context-id", help="Optional target context id for merge/promote decisions.")
    parser.add_argument("--report-file", help="Optional JSON report file written atomically.")
    parser.add_argument("--format", default="text", choices=tuple(sorted(_ALLOWED_FORMATS)), help="Output format.")
    return parser


def command_from_args(args: argparse.Namespace) -> SourceCandidateIntakeCommand:
    body = _read_body(args)
    origin = SourceCandidateOrigin(
        kind=args.origin_kind,
        reference=args.origin_reference,
        repository=args.repository,
    )
    candidate_input = SourceCandidateInput(
        title=args.title,
        body=body,
        origin=origin,
        labels=tuple(args.label),
        metadata=_parse_metadata(args.metadata),
    )
    candidate_policy = SourceCandidatePolicy(
        default_status=args.default_status,
        default_repository=args.repository,
        id_prefix=args.id_prefix,
    )
    decision = None
    if args.decision is not None:
        decision = SourceCandidateDecision(
            action=args.decision,
            reason=args.reason,
            target_context_id=args.target_context_id,
        )
    return SourceCandidateIntakeCommand(
        candidate_input=candidate_input,
        candidate_policy=candidate_policy,
        store_policy=SourceCandidateStorePolicy(path=args.store_file, repository=args.repository),
        report_policy=SourceCandidateReportPolicy(path=args.report_file),
        render_policy=SourceCandidateIntakeRenderPolicy(output_format=args.format),
        decision=decision,
    )


def run_source_candidate_intake(command: SourceCandidateIntakeCommand) -> SourceCandidateIntakeResult:
    creation = build_source_candidate(command.candidate_input, command.candidate_policy)
    candidate = creation.candidate
    if command.decision is not None:
        candidate = apply_source_candidate_decision(candidate, command.decision)
    report_policy = command.report_policy if command.report_policy.path is not None else None
    write_result = upsert_source_candidate(command.store_policy, candidate, report=report_policy)
    return SourceCandidateIntakeResult(
        creation=creation,
        candidate=candidate,
        write_result=write_result,
        decision=command.decision,
        report_path=command.report_policy.path,
    )


def render_source_candidate_intake_result(
    result: SourceCandidateIntakeResult,
    policy: SourceCandidateIntakeRenderPolicy,
) -> str:
    if policy.output_format == "json":
        return json.dumps(result.to_json_dict(), ensure_ascii=False, sort_keys=True, indent=2)
    if policy.output_format == "text":
        return result.to_text()
    raise ValueError("output_format must be text or json")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        command = command_from_args(args)
        result = run_source_candidate_intake(command)
        print(render_source_candidate_intake_result(result, command.render_policy))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


def _read_body(args: argparse.Namespace) -> str:
    if args.body_file is not None:
        return Path(args.body_file).read_text(encoding="utf-8")
    return args.body or ""


def _parse_metadata(entries: Sequence[str]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for entry in entries:
        key, separator, value = entry.partition("=")
        if not separator or not key.strip():
            raise ValueError("metadata entries must use key=value")
        metadata[key.strip()] = value
    return metadata


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
