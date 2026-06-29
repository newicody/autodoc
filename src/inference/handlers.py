from __future__ import annotations

from contracts.event import Event, EventType
from contracts.inference import InferenceRequest, InferenceResult
from kernel.event_bus import EventBus

from .adapter import InferenceAdapter


class InferenceRequestHandler:
    """Handler d'inférence indépendant du Scheduler et des backends concrets.

    Le Scheduler route uniquement l'événement. Le handler valide le payload,
    délègue à l'adapter et publie un ``INFERENCE_RESULT`` observable.
    """

    def __init__(self, adapter: InferenceAdapter, event_bus: EventBus) -> None:
        self.adapter = adapter
        self.event_bus = event_bus

    async def handle(self, event: Event) -> InferenceResult:
        if not isinstance(event.payload, InferenceRequest):
            raise TypeError(
                "INFERENCE_REQUEST payload must be an InferenceRequest, "
                f"got {type(event.payload).__name__}"
            )

        result = await self.adapter.infer(event.payload)
        await self.event_bus.publish(
            Event(
                EventType.INFERENCE_RESULT,
                source=self.adapter.name,
                dest=event.source,
                payload=result,
                correlation_id=event.id,
                priority=event.priority,
            )
        )
        return result
