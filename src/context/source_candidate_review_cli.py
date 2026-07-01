
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

from .source_candidate import allowed_source_candidate_statuses
from .source_candidate_handlers import SourceCandidateReviewHandler
from .source_candidate_review import (
    SourceCandidateReviewCommand,
    SourceCandidateReviewPolicy,
    SourceCandidateReviewResult,
)
from .source_candidate_store import SourceCandidateStorePolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review local SourceCandidate store through the Scheduler live path."
    )
    parser.add_argument("--store-file", required=True, help="Path to source_candidates.json")
    parser.add_argument("--repository", default="newicody/autodoc")
    parser.add_argument("--include-terminal", action="store_true")
    parser.add_argument(
        "--status",
        action="append",
        choices=allowed_source_candidate_statuses(),
        default=[],
        help="Filter by status. May be repeated.",
    )
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--body-preview-chars", type=int, default=160)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def command_from_args(args: argparse.Namespace) -> SourceCandidateReviewCommand:
    return SourceCandidateReviewCommand(
        store_policy=SourceCandidateStorePolicy(
            path=args.store_file,
            repository=args.repository,
        ),
        review_policy=SourceCandidateReviewPolicy(
            include_terminal=args.include_terminal,
            status_filter=tuple(args.status or ()),
            limit=args.limit,
            body_preview_chars=args.body_preview_chars,
        ),
    )


async def run_source_candidate_review_via_scheduler(
    command: SourceCandidateReviewCommand,
) -> SourceCandidateReviewResult:
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    dispatcher.register(EventType.SOURCE_CANDIDATE_REVIEW, SourceCandidateReviewHandler(bus))
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, Registry(), context_interval=60.0)

    reply = asyncio.get_running_loop().create_future()
    event = Event(
        EventType.SOURCE_CANDIDATE_REVIEW,
        source="source_candidate.review_cli",
        dest="source_candidate",
        payload=command,
        request=Request(reply=reply),
        metadata={"schema": "missipy.source_candidate.review_cli_event.v1"},
    )
    scheduler_task = asyncio.create_task(scheduler.run())
    try:
        await scheduler.emit(event)
        result = await asyncio.wait_for(reply, timeout=5.0)
    finally:
        await scheduler.shutdown()
        await scheduler_task
    if not isinstance(result, SourceCandidateReviewResult):
        raise ValueError("SOURCE_CANDIDATE_REVIEW result must be SourceCandidateReviewResult")
    return result


def render_source_candidate_review_result(
    result: SourceCandidateReviewResult,
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
    result = asyncio.run(run_source_candidate_review_via_scheduler(command))
    print(render_source_candidate_review_result(result, args.format))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
