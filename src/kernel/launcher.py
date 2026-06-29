from __future__ import annotations

import asyncio
from contextlib import suppress

from context.handlers import ContextRequestHandler
from contracts.event import EventType
from inference.adapter import InferenceAdapter
from inference.backend import DummyInferenceBackend
from inference.registry import BackendRegistry
from inference.handlers import InferenceRequestHandler
from observability.recorder import EventRecorder
from observability.telemetry import KernelTelemetry
from policy.engine import PolicyEngine
from runtime.component import ComponentProxy
from runtime.loader import load_components

from .dispatcher import Dispatcher
from .event_bus import EventBus
from .lifecycle import LifecycleManager
from .queue import PriorityQueue
from .registry import Registry
from .scheduler import Scheduler


class Launcher:
    """Assemble le kernel et démarre les composants Phase 1.7."""

    def __init__(self, context_interval: float = 1.0) -> None:
        self.registry = Registry()
        self.event_bus = EventBus()
        self.dispatcher = Dispatcher(self.event_bus)
        self.queue = PriorityQueue()
        self.lifecycle = LifecycleManager()
        self.policy_engine = PolicyEngine()
        self.telemetry = KernelTelemetry()
        self.event_recorder = EventRecorder(self.event_bus)
        self.inference_backend = DummyInferenceBackend()
        self.inference_registry = BackendRegistry()
        self.inference_registry.register(self.inference_backend, make_default=True)
        self.inference_adapter = InferenceAdapter(self.inference_registry)
        self.scheduler = Scheduler(
            self.queue,
            self.dispatcher,
            self.event_bus,
            self.registry,
            context_interval=context_interval,
            policy_engine=self.policy_engine,
            telemetry=self.telemetry,
        )
        self._proxies: list[ComponentProxy] = []

    async def boot(self, run_forever: bool = False) -> None:
        self._register_kernel_handlers()
        components = load_components()
        for component in components:
            proxy = ComponentProxy(component, self.scheduler)
            self.registry.register(proxy.name, proxy)
            self._proxies.append(proxy)

        await self.event_recorder.start()
        scheduler_task = asyncio.create_task(
            self.scheduler.run(),
            name="missipy-scheduler",
        )
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
            await self.event_recorder.stop()
            if not scheduler_task.done():
                scheduler_task.cancel()
                with suppress(asyncio.CancelledError):
                    await scheduler_task

    def _register_kernel_handlers(self) -> None:
        self.lifecycle.register_handlers(self.dispatcher)
        self.dispatcher.register(
            EventType.CONTEXT_REQUEST,
            ContextRequestHandler(self.registry),
        )
        self.dispatcher.register(
            EventType.INFERENCE_REQUEST,
            InferenceRequestHandler(self.inference_adapter, self.event_bus),
        )
