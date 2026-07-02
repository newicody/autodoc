from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence

from contracts.event import Event, EventType, Request
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler

from .source_candidate import SourceCandidateDecision, allowed_source_candidate_decisions
from .source_candidate_decision import (
    SourceCandidateDecisionCommand,
    SourceCandidateDecisionResult,
)
from .source_candidate_decision_handlers import SourceCandidateDecisionHandler
from .source_candidate_store import SourceCandidateReportPolicy, SourceCandidateStorePolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply a local SourceCandidate operator decision through the Scheduler live path."
    )
    parser.add_argument("--store-file", required=True, help="Path to source_candidates.json")
    parser.add_argument("--repository", default="newicody/autodoc")
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--action", required=True, choices=allowed_source_candidate_decisions())
    parser.add_argument("--reason", default="")
    parser.add_argument("--target-context-id")
    parser.add_argument("--report-file")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def command_from_args(args: argparse.Namespace) -> SourceCandidateDecisionCommand:
    report_policy = (
        SourceCandidateReportPolicy(path=args.report_file) if args.report_file else None
    )
    return SourceCandidateDecisionCommand(
        store_policy=SourceCandidateStorePolicy(
            path=args.store_file,
            repository=args.repository,
        ),
        candidate_id=args.candidate_id,
        decision=SourceCandidateDecision(
            action=args.action,
            reason=args.reason,
            target_context_id=args.target_context_id,
        ),
        report_policy=report_policy,
    )


async def run_source_candidate_decision_via_scheduler(
    command: SourceCandidateDecisionCommand,
) -> SourceCandidateDecisionResult:
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    dispatcher.register(EventType.SOURCE_CANDIDATE_DECISION, SourceCandidateDecisionHandler(bus))
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, Registry(), context_interval=60.0)

    reply = asyncio.get_running_loop().create_future()
    event = Event(
        EventType.SOURCE_CANDIDATE_DECISION,
        source="source_candidate.decision_cli",
        dest="source_candidate",
        payload=command,
        request=Request(reply=reply),
        metadata={"schema": "missipy.source_candidate.decision_cli_event.v1"},
    )

    scheduler_task = asyncio.create_task(scheduler.run())
    try:
        await scheduler.emit(event)
        result = await asyncio.wait_for(reply, timeout=5.0)
    finally:
        await scheduler.shutdown()
        await scheduler_task

    if not isinstance(result, SourceCandidateDecisionResult):
        raise ValueError("SOURCE_CANDIDATE_DECISION result must be SourceCandidateDecisionResult")
    return result


def render_source_candidate_decision_result(
    result: SourceCandidateDecisionResult,
    output_format: str,
) -> str:
    if output_format == "json":
        return json.dumps(result.to_json_dict(), ensure_ascii=False, sort_keys=True, indent=2)
    if output_format == "text":
        return result.to_text()
    raise ValueError("format must be text or json")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = command_from_args(args)
    result = asyncio.run(run_source_candidate_decision_via_scheduler(command))
    print(render_source_candidate_decision_result(result, args.format))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
