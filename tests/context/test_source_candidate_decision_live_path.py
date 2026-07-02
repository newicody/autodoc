from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from contracts.event import Event, EventType, Request
from context.source_candidate import SourceCandidateDecision, SourceCandidateInput, build_source_candidate
from context.source_candidate_decision import SourceCandidateDecisionCommand, SourceCandidateDecisionResult
from context.source_candidate_decision_handlers import (
    SourceCandidateDecisionHandler,
    source_candidate_decision_result_payload,
)
from context.source_candidate_store import SourceCandidateStorePolicy, load_source_candidate_store, upsert_source_candidate
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler


def _command(tmp_path: Path) -> SourceCandidateDecisionCommand:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    candidate = build_source_candidate(
        SourceCandidateInput(title="Live decision", body="Candidate body")
    ).candidate
    upsert_source_candidate(store_policy, candidate)
    return SourceCandidateDecisionCommand(
        store_policy=store_policy,
        candidate_id=candidate.candidate_id,
        decision=SourceCandidateDecision(action="archive", reason="done"),
    )


@pytest.mark.asyncio
async def test_source_candidate_decision_traverses_scheduler_live_path(tmp_path: Path) -> None:
    command = _command(tmp_path)
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    dispatcher.register(EventType.SOURCE_CANDIDATE_DECISION, SourceCandidateDecisionHandler(bus))
    observed = bus.subscribe(EventType.SOURCE_CANDIDATE_DECISION_RESULT)
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, Registry(), context_interval=60.0)

    reply = asyncio.get_running_loop().create_future()
    event = Event(
        EventType.SOURCE_CANDIDATE_DECISION,
        source="test.source_candidate.decision",
        dest="source_candidate",
        payload=command,
        request=Request(reply=reply),
    )

    task = asyncio.create_task(scheduler.run())
    try:
        await scheduler.emit(event)
        result = await asyncio.wait_for(reply, timeout=2.0)
    finally:
        await scheduler.shutdown()
        await task

    assert isinstance(result, SourceCandidateDecisionResult)
    assert result.after_status == "archived"

    result_event = await asyncio.wait_for(observed.get(), timeout=2.0)
    assert result_event.type is EventType.SOURCE_CANDIDATE_DECISION_RESULT
    assert result_event.source == "source_candidate.decision"
    assert source_candidate_decision_result_payload(result_event) is result

    reloaded = load_source_candidate_store(command.store_policy).find(command.candidate_id)
    assert reloaded is not None
    assert reloaded.status == "archived"
