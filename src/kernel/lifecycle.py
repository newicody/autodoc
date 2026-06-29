# kernel/lifecycle
from contracts.event import Event, EventType
from .dispatcher import Dispatcher

class LifecycleManager:
    @staticmethod
    def register_handlers(dispatcher: Dispatcher):
        dispatcher.register(EventType.LOAD, LoadHandler())
        dispatcher.register(EventType.START, StartHandler())
        dispatcher.register(EventType.STOP, StopHandler())

class LoadHandler:
    async def handle(self, event: Event):
        print(f"[Lifecycle] LOAD: {event.source}")

class StartHandler:
    async def handle(self, event: Event):
        print(f"[Lifecycle] START: {event.source}")

class StopHandler:
    async def handle(self, event: Event):
        print(f"[Lifecycle] STOP: {event.source}")
