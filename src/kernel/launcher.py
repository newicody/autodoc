from __future__ import annotations

import asyncio
from contextlib import suppress

from .dispatcher import Dispatcher
from .event_bus import EventBus
from .lifecycle import LifecycleManager
from .queue import PriorityQueue
from .registry import Registry
from .scheduler import Scheduler
from runtime.component import ComponentProxy
from runtime.loader import load_components


class Launcher:
    """Assemble le kernel Phase 1 et démarre les composants."""

    def __init__(self) -> None:
        self.registry = Registry()
        self.event_bus = EventBus()
        self.dispatcher = Dispatcher(self.event_bus)
        self.queue = PriorityQueue()
        self.scheduler = Scheduler(self.queue, self.dispatcher, self.event_bus, self.registry)
        self._proxies: list[ComponentProxy] = []

    async def boot(self, run_forever: bool = False) -> None:
        components = load_components()
        for component in components:
            proxy = ComponentProxy(component, self.scheduler)
            self.registry.register(proxy.name, proxy)
            self._proxies.append(proxy)

        LifecycleManager.register_handlers(self.dispatcher)

        scheduler_task = asyncio.create_task(self.scheduler.run(), name="missipy-scheduler")
        try:
            for proxy in self._proxies:
                await proxy.start()

            if run_forever:
                await scheduler_task
            else:
                await asyncio.gather(*(proxy.wait() for proxy in self._proxies))
                await self.scheduler.shutdown()
                await scheduler_task
        finally:
            for proxy in self._proxies:
                await proxy.stop()
            if not scheduler_task.done():
                scheduler_task.cancel()
                with suppress(asyncio.CancelledError):
                    await scheduler_task
