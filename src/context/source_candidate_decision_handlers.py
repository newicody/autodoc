from __future__ import annotations

from typing import Any

from contracts.event import Event, EventType
from kernel.event_bus import EventBus

from .source_candidate_decision import (
    SourceCandidateDecisionCommand,
    SourceCandidateDecisionResult,
    run_source_candidate_decision,
)


class SourceCandidateDecisionHandler:
    """Handler Scheduler pour l'application d'une décision opérateur locale."""

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    async def handle(self, event: Event) -> SourceCandidateDecisionResult:
        if not isinstance(event.payload, SourceCandidateDecisionCommand):
            raise ValueError(
                "SOURCE_CANDIDATE_DECISION payload must be SourceCandidateDecisionCommand"
            )

        result = run_source_candidate_decision(event.payload)

        await self.event_bus.publish(
            Event(
                EventType.SOURCE_CANDIDATE_DECISION_RESULT,
                source="source_candidate.decision",
                dest=event.source,
                payload=result,
                priority=event.priority,
                correlation_id=event.id,
                metadata={"schema": "missipy.source_candidate.decision_result_event.v1"},
            )
        )

        return result


def source_candidate_decision_result_payload(event: Event) -> SourceCandidateDecisionResult:
    """Extrait un payload typé de résultat observable SourceCandidate decision."""

    payload: Any = event.payload
    if not isinstance(payload, SourceCandidateDecisionResult):
        raise ValueError(
            "source candidate decision event payload must be SourceCandidateDecisionResult"
        )
    return payload
