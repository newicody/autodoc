# kernel/event_bus.py
import asyncio
from collections import defaultdict
from contracts.event import Event

class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)  # event_type -> list of queues

    def subscribe(self, event_type=None):
        q = asyncio.Queue()
        self._subscribers[event_type].append(q)
        return q

    async def publish(self, event: Event):
        # Notifier les abonnés génériques (None = tous)
        for q in self._subscribers.get(None, []):
            await q.put(event)
        # Notifier les abonnés spécifiques au type
        for q in self._subscribers.get(event.type, []):
            await q.put(event)
