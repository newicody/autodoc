# kernel/dispatcher.py
from typing import Dict, Any
from contracts.event import Event, EventType
from .event_bus import EventBus

class Dispatcher:
    def __init__(self, event_bus: EventBus):
        self.handlers: Dict[EventType, Any] = {}
        self.event_bus = event_bus

    def register(self, event_type: EventType, handler):
        self.handlers[event_type] = handler

    async def dispatch(self, event: Event):
        await self.event_bus.publish(event)
        handler = self.handlers.get(event.type)
        if handler:
            await handler.handle(event)
