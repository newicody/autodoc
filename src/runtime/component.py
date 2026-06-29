from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from contracts.component import Component
from contracts.event import Event, EventType, Request
from contracts.lifecycle import ComponentState

if TYPE_CHECKING:
    from kernel.scheduler import Scheduler


class ComponentProxy:
    """Isolation minimale autour d'un Component réel.

    Le proxy est la seule surface visible par le kernel : il démarre le composant,
    intercepte les Events, ajoute un canal de réponse et fournit le contexte.
    """

    def __init__(self, real: Component, scheduler: "Scheduler") -> None:
        self._real = real
        self.name = getattr(real, "name", real.__class__.__name__)
        self.scheduler = scheduler
        self._tick_task: asyncio.Task[None] | None = None
        self._started = False
        self._stopped = False
        self.state = ComponentState.CREATED
        self.last_error: BaseException | None = None

    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        self.state = ComponentState.LOADED
        await self.scheduler.emit(Event(EventType.LOAD, source=self.name))
        self._tick_task = asyncio.create_task(self._tick_loop(), name=f"component:{self.name}")
        self.state = ComponentState.STARTED
        await self.scheduler.emit(Event(EventType.START, source=self.name))

    async def wait(self) -> None:
        if self._tick_task is not None:
            await self._tick_task

    async def stop(self) -> None:
        self.state = ComponentState.STOPPING
        if self._tick_task is not None and not self._tick_task.done():
            self._tick_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._tick_task
        await self._emit_stop_once()

    async def _tick_loop(self) -> None:
        try:
            self.state = ComponentState.RUNNING
            gen = self._real.tick()
            event = await gen.__anext__()
            while True:
                result = await self._dispatch_event(event)
                event = await gen.asend(result)
        except StopAsyncIteration:
            await self._emit_stop_once()
        except asyncio.CancelledError:
            await self._emit_stop_once()
            raise
        except BaseException as exc:
            self.last_error = exc
            self.state = ComponentState.ERROR
            await self.scheduler.emit(
                Event(
                    EventType.ERROR,
                    source=self.name,
                    payload={"error": repr(exc), "class": exc.__class__.__name__},
                    priority=-100,
                )
            )
            await self._emit_stop_once()

    async def _dispatch_event(self, event: Event) -> Any:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Any] = loop.create_future()
        timeout = event.request.timeout if event.request else 5.0
        request = Request(reply=future, timeout=timeout)
        outbound = replace(event, source=event.source or self.name, request=request)
        await self.scheduler.emit(outbound)
        return await asyncio.wait_for(future, timeout=timeout)

    async def _emit_stop_once(self) -> None:
        if not self._stopped:
            self._stopped = True
            if self.state != ComponentState.ERROR:
                self.state = ComponentState.STOPPED
            await self.scheduler.emit(Event(EventType.STOP, source=self.name))

    async def context(self) -> dict[str, Any]:
        ctx = await self._real.context()
        return {
            "proxy_state": self.state.name,
            "component": ctx,
        }
