
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from context.source_candidate import SourceCandidateInput, SourceCandidateOrigin, build_source_candidate
from context.source_candidate_handlers import (
    SourceCandidateReviewHandler,
    source_candidate_review_result_payload,
)
from context.source_candidate_review import (
    SourceCandidateReviewCommand,
    SourceCandidateReviewResult,
)
from context.source_candidate_store import SourceCandidateStorePolicy, upsert_source_candidate
from contracts.event import Event, EventType, Request
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler


def _store(tmp_path: Path) -> SourceCandidateStorePolicy:
    policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    candidate = build_source_candidate(
        SourceCandidateInput(
            title="Review through Scheduler",
            body="created before review",
            origin=SourceCandidateOrigin(kind="manual", reference="pytest"),
            labels=("live-path",),
            metadata={"phase": "6.2"},
        )
    ).candidate
    upsert_source_candidate(policy, candidate)
    return policy


@pytest.mark.asyncio
async def test_source_candidate_review_traverses_scheduler_live_path(tmp_path: Path) -> None:
    registry = Registry()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    dispatcher.register(EventType.SOURCE_CANDIDATE_REVIEW, SourceCandidateReviewHandler(bus))
    observed = bus.subscribe(EventType.SOURCE_CANDIDATE_REVIEW_RESULT)
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, registry, context_interval=60.0)

    command = SourceCandidateReviewCommand(store_policy=_store(tmp_path))
    reply = asyncio.get_running_loop().create_future()
    event = Event(
        EventType.SOURCE_CANDIDATE_REVIEW,
        source="pytest",
        dest="source_candidate",
        payload=command,
        request=Request(reply=reply),
    )

    scheduler_task = asyncio.create_task(scheduler.run())
    try:
        await scheduler.emit(event)
        result = await asyncio.wait_for(reply, timeout=1.0)
        result_event = await asyncio.wait_for(observed.get(), timeout=1.0)
    finally:
        await scheduler.shutdown()
        await scheduler_task

    assert isinstance(result, SourceCandidateReviewResult)
    assert result.returned_count == 1
    assert result.items[0].candidate.title == "Review through Scheduler"
    assert result_event.type is EventType.SOURCE_CANDIDATE_REVIEW_RESULT
    assert result_event.source == "source_candidate.review"
    assert result_event.dest == "pytest"
    assert result_event.correlation_id == event.id
    assert source_candidate_review_result_payload(result_event) is result
