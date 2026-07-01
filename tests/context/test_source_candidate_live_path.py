from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from context.source_candidate import SourceCandidateInput, SourceCandidateOrigin, SourceCandidatePolicy
from context.source_candidate_handlers import SourceCandidateIntakeHandler, source_candidate_intake_result_payload
from context.source_candidate_intake import SourceCandidateIntakeCommand, SourceCandidateIntakeResult
from context.source_candidate_store import SourceCandidateReportPolicy, SourceCandidateStorePolicy
from contracts.event import Event, EventType, Request
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler
from policy.engine import PolicyEngine


def _command(tmp_path: Path) -> SourceCandidateIntakeCommand:
    return SourceCandidateIntakeCommand(
        candidate_input=SourceCandidateInput(
            title="Live path candidate",
            body="created through Scheduler",
            origin=SourceCandidateOrigin(kind="manual", reference="pytest"),
            labels=("live-path",),
            metadata={"phase": "6.1-r1"},
        ),
        candidate_policy=SourceCandidatePolicy(default_repository="newicody/autodoc"),
        store_policy=SourceCandidateStorePolicy(path=tmp_path / "source_candidates.json"),
        report_policy=SourceCandidateReportPolicy(path=tmp_path / "intake_report.json"),
    )


def test_policy_allows_source_candidate_destination() -> None:
    decision = PolicyEngine().decide(
        Event(
            EventType.SOURCE_CANDIDATE_INTAKE,
            source="test",
            dest="source_candidate",
            payload=None,
        )
    )
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_source_candidate_intake_traverses_scheduler_live_path(tmp_path: Path) -> None:
    registry = Registry()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    dispatcher.register(EventType.SOURCE_CANDIDATE_INTAKE, SourceCandidateIntakeHandler(bus))
    observed = bus.subscribe(EventType.SOURCE_CANDIDATE_INTAKE_RESULT)
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, registry, context_interval=60.0)

    reply = asyncio.get_running_loop().create_future()
    event = Event(
        EventType.SOURCE_CANDIDATE_INTAKE,
        source="pytest",
        dest="source_candidate",
        payload=_command(tmp_path),
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

    assert isinstance(result, SourceCandidateIntakeResult)
    assert result.candidate.title == "Live path candidate"
    assert result.write_result.path == tmp_path / "source_candidates.json"
    assert result_event.type is EventType.SOURCE_CANDIDATE_INTAKE_RESULT
    assert result_event.source == "source_candidate.intake"
    assert result_event.dest == "pytest"
    assert result_event.correlation_id == event.id
    assert source_candidate_intake_result_payload(result_event) is result

    store_payload = json.loads((tmp_path / "source_candidates.json").read_text(encoding="utf-8"))
    report_payload = json.loads((tmp_path / "intake_report.json").read_text(encoding="utf-8"))
    assert store_payload["schema"] == "missipy.source_candidate.store.v1"
    assert store_payload["candidate_count"] == 1
    assert report_payload["schema"] == "missipy.source_candidate.store_report.v1"
