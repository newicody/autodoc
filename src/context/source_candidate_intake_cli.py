from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from contracts.event import Event, EventType, Request
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler

from .source_candidate import (
    SourceCandidateDecision,
    SourceCandidateInput,
    SourceCandidateOrigin,
    SourceCandidatePolicy,
    allowed_source_candidate_decisions,
    allowed_source_candidate_statuses,
)
from .source_candidate_handlers import SourceCandidateIntakeHandler
from .source_candidate_intake import (
    SourceCandidateIntakeCommand,
    SourceCandidateIntakeResult,
    run_source_candidate_intake,
)
from .source_candidate_store import SourceCandidateReportPolicy, SourceCandidateStorePolicy

_ALLOWED_FORMATS = frozenset({"text", "json"})


@dataclass(frozen=True, slots=True)
class SourceCandidateIntakeRenderPolicy:
    """Politique de rendu de la CLI SourceCandidate locale."""

    output_format: str = "text"

    def __post_init__(self) -> None:
        if self.output_format not in _ALLOWED_FORMATS:
            raise ValueError("output_format must be text or json")



def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="source-candidate-intake",
        description="Create or update one local SourceCandidate through the Scheduler live path.",
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
    intake = SourceCandidateIntakeCommand(
        candidate_input=candidate_input,
        candidate_policy=candidate_policy,
        store_policy=SourceCandidateStorePolicy(path=args.store_file, repository=args.repository),
        report_policy=SourceCandidateReportPolicy(path=args.report_file),
        decision=decision,
    )
    return intake


async def run_source_candidate_intake_via_scheduler(
    command: SourceCandidateIntakeCommand,
) -> SourceCandidateIntakeResult:
    """Exécute l'intake par le chemin Scheduler vivant local."""

    registry = Registry()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    dispatcher.register(EventType.SOURCE_CANDIDATE_INTAKE, SourceCandidateIntakeHandler(bus))
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, registry, context_interval=60.0)

    loop = asyncio.get_running_loop()
    reply = loop.create_future()
    event = Event(
        EventType.SOURCE_CANDIDATE_INTAKE,
        source="source_candidate.intake_cli",
        dest="source_candidate",
        payload=command,
        request=Request(reply=reply),
    )
    scheduler_task = asyncio.create_task(scheduler.run(), name="source-candidate-intake-scheduler")
    try:
        await scheduler.emit(event)
        result = await asyncio.wait_for(reply, timeout=event.request.timeout if event.request else 5.0)
        if not isinstance(result, SourceCandidateIntakeResult):
            raise ValueError("SOURCE_CANDIDATE_INTAKE result must be SourceCandidateIntakeResult")
        return result
    finally:
        await scheduler.shutdown()
        await scheduler_task


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
        render_policy = SourceCandidateIntakeRenderPolicy(output_format=args.format)
        result = asyncio.run(run_source_candidate_intake_via_scheduler(command))
        print(render_source_candidate_intake_result(result, render_policy))
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
