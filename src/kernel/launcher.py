# kernel/launcher.py
import asyncio
from .registry import Registry
from .scheduler import Scheduler
from .event_bus import EventBus
from .dispatcher import Dispatcher
from .queue import PriorityQueue
from runtime.loader import load_components
from runtime.component import ComponentProxy
from .lifecycle import LifecycleManager

class Launcher:
    def __init__(self):
        self.registry = Registry()
        self.event_bus = EventBus()
        self.dispatcher = Dispatcher(self.event_bus)
        self.queue = PriorityQueue()
        self.scheduler = Scheduler(self.queue, self.dispatcher, self.event_bus)

    async def boot(self):
        # 1. Découverte et chargement des composants réels
        components = load_components()
        for comp in components:
            proxy = ComponentProxy(comp, self.scheduler)
            self.registry.register(comp.name, proxy)

        # 2. Enregistrement des handlers de base (cycle de vie)
        LifecycleManager.register_handlers(self.dispatcher)

        # 3. Lancement du scheduler
        await self.scheduler.run()
