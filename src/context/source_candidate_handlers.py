
from __future__ import annotations

from typing import Any

from contracts.event import Event, EventType
from kernel.event_bus import EventBus

from .source_candidate_intake import (
    SourceCandidateIntakeCommand,
    SourceCandidateIntakeResult,
    run_source_candidate_intake,
)
from .source_candidate_review import (
    SourceCandidateReviewCommand,
    SourceCandidateReviewResult,
    run_source_candidate_review,
)


class SourceCandidateIntakeHandler:
    """Handler Scheduler pour l'intake SourceCandidate local.

    Il constitue le chemin vivant Phase 6.1-r1 : une commande typée traverse le
    Scheduler, le Dispatcher et ce handler avant d'atteindre le store JSON réel.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    async def handle(self, event: Event) -> SourceCandidateIntakeResult:
        if not isinstance(event.payload, SourceCandidateIntakeCommand):
            raise ValueError("SOURCE_CANDIDATE_INTAKE payload must be SourceCandidateIntakeCommand")
        result = run_source_candidate_intake(event.payload)
        await self.event_bus.publish(
            Event(
                EventType.SOURCE_CANDIDATE_INTAKE_RESULT,
                source="source_candidate.intake",
                dest=event.source,
                payload=result,
                priority=event.priority,
                correlation_id=event.id,
                metadata={"schema": "missipy.source_candidate.intake_result_event.v1"},
            )
        )
        return result


class SourceCandidateReviewHandler:
    """Handler Scheduler pour la projection opérateur SourceCandidate.

    La Phase 6.2 lit le store JSON réel en lecture seule, produit une projection de
    revue et publie un résultat observable. Elle ne contacte pas GitHub.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    async def handle(self, event: Event) -> SourceCandidateReviewResult:
        if not isinstance(event.payload, SourceCandidateReviewCommand):
            raise ValueError("SOURCE_CANDIDATE_REVIEW payload must be SourceCandidateReviewCommand")
        result = run_source_candidate_review(event.payload)
        await self.event_bus.publish(
            Event(
                EventType.SOURCE_CANDIDATE_REVIEW_RESULT,
                source="source_candidate.review",
                dest=event.source,
                payload=result,
                priority=event.priority,
                correlation_id=event.id,
                metadata={"schema": "missipy.source_candidate.review_result_event.v1"},
            )
        )
        return result


def source_candidate_intake_result_payload(event: Event) -> SourceCandidateIntakeResult:
    """Extrait un payload typé de résultat observable SourceCandidate intake."""

    payload: Any = event.payload
    if not isinstance(payload, SourceCandidateIntakeResult):
        raise ValueError("source candidate result event payload must be SourceCandidateIntakeResult")
    return payload


def source_candidate_review_result_payload(event: Event) -> SourceCandidateReviewResult:
    """Extrait un payload typé de résultat observable SourceCandidate review."""

    payload: Any = event.payload
    if not isinstance(payload, SourceCandidateReviewResult):
        raise ValueError("source candidate review event payload must be SourceCandidateReviewResult")
    return payload
