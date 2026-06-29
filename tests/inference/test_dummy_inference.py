from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator

import pytest

from contracts.component import Component
from contracts.event import Event, EventType
from contracts.inference import InferenceRequest, InferenceResult
from inference.adapter import InferenceAdapter
from inference.backend import DummyInferenceBackend
from inference.handlers import InferenceRequestHandler
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.lifecycle import LifecycleManager
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler
from runtime.component import ComponentProxy


class InferenceProbe(Component):
    name = "InferenceProbe"

    def __init__(self) -> None:
        self.result: InferenceResult | None = None

    async def tick(self) -> AsyncGenerator[Event, Any]:
        payload = InferenceRequest(
            prompt="ping",
            context={"source": self.name},
            model="dummy",
        )
        self.result = yield Event(
            EventType.INFERENCE_REQUEST,
            source=self.name,
            dest="inference",
            payload=payload,
        )

    async def context(self) -> dict[str, Any]:
        return {
            "has_result": self.result is not None,
        }


class UppercaseBackend:
    name = "upper"

    async def infer(self, request: InferenceRequest) -> InferenceResult:
        return InferenceResult(
            text=request.prompt.upper(),
            confidence=0.5,
            backend=self.name,
        )


@pytest.mark.asyncio
async def test_dummy_inference_backend_is_deterministic() -> None:
    backend = DummyInferenceBackend()
    request = InferenceRequest(prompt="hello", model="dummy")

    result = await backend.infer(request)

    assert result.backend == "dummy"
    assert result.confidence == 1.0
    assert result.text == "dummy://dummy: hello"
    assert result.metadata["prompt_length"] == 5


@pytest.mark.asyncio
async def test_inference_adapter_selects_registered_backend() -> None:
    adapter = InferenceAdapter(DummyInferenceBackend())
    adapter.register_backend(UppercaseBackend())
    request = InferenceRequest(prompt="hello", model="upper")

    result = await adapter.infer(request)

    assert result.backend == "upper"
    assert result.text == "HELLO"
    assert tuple(sorted(adapter.backends)) == ("dummy", "upper")


@pytest.mark.asyncio
async def test_inference_adapter_rejects_unknown_backend() -> None:
    adapter = InferenceAdapter(DummyInferenceBackend())
    request = InferenceRequest(prompt="hello", model="missing")

    with pytest.raises(LookupError, match="missing"):
        await adapter.infer(request)


@pytest.mark.asyncio
async def test_inference_handler_publishes_observable_result() -> None:
    bus = EventBus()
    observed = bus.subscribe(EventType.INFERENCE_RESULT)
    adapter = InferenceAdapter(DummyInferenceBackend())
    handler = InferenceRequestHandler(adapter, bus)
    request = InferenceRequest(prompt="hello")
    event = Event(EventType.INFERENCE_REQUEST, source="test", payload=request)

    result = await handler.handle(event)
    observed_event = await observed.get()

    assert result.text == "dummy://dummy: hello"
    assert observed_event.type is EventType.INFERENCE_RESULT
    assert observed_event.source == "inference-adapter"
    assert observed_event.dest == "test"
    assert observed_event.correlation_id == event.id
    assert observed_event.payload == result


@pytest.mark.asyncio
async def test_component_can_roundtrip_through_dummy_inference_handler() -> None:
    registry = Registry()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    lifecycle = LifecycleManager()
    lifecycle.register_handlers(dispatcher)
    adapter = InferenceAdapter(DummyInferenceBackend())
    dispatcher.register(
        EventType.INFERENCE_REQUEST,
        InferenceRequestHandler(adapter, bus),
    )
    observed = bus.subscribe(EventType.INFERENCE_RESULT)
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, registry, context_interval=60.0)
    component = InferenceProbe()
    proxy = ComponentProxy(component, scheduler)
    registry.register(proxy.name, proxy)
    scheduler_task = asyncio.create_task(scheduler.run())

    await proxy.start()
    await proxy.wait()
    result_event = await observed.get()
    await scheduler.shutdown()
    await scheduler_task

    assert isinstance(component.result, InferenceResult)
    assert component.result.text == "dummy://dummy: ping"
    assert result_event.payload == component.result
