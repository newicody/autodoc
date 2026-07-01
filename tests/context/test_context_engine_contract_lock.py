from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

import pytest

from contracts.context import InferenceContext, freeze_mapping
from context.engine import ContextEngine


@dataclass(frozen=True, slots=True)
class _Snapshot:
    components: Mapping[str, object]


class _Collector:
    def __init__(self, snapshot: _Snapshot) -> None:
        self.snapshot = snapshot

    async def collect(self) -> _Snapshot:
        return self.snapshot


class _Reducer:
    def reduce(self, snapshot: _Snapshot) -> _Snapshot:
        return snapshot


class _Builder:
    def __init__(self, inference_context: InferenceContext) -> None:
        self.inference_context = inference_context

    def build(self, snapshot: _Snapshot) -> InferenceContext:
        assert "Ctx" in snapshot.components
        return self.inference_context


def _inference_context(name: str = "manual") -> InferenceContext:
    return InferenceContext(
        features=freeze_mapping({name: {"status": "ready"}}),
        priorities=freeze_mapping({name: 10}),
    )


def test_context_engine_keeps_legacy_constructor_dependencies() -> None:
    registry = object()
    scheduler = object()
    event_bus = object()

    engine = ContextEngine(registry, scheduler, event_bus)

    assert engine.registry is registry
    assert engine.scheduler is scheduler
    assert engine.event_bus is event_bus
    assert engine.current_inference_context.features == {}
    assert engine.current_inference_context.priorities == {}


def test_context_engine_accepts_direct_inference_context_constructor() -> None:
    inference_context = _inference_context()

    engine = ContextEngine(inference_context)

    assert engine.registry is None
    assert engine.scheduler is None
    assert engine.event_bus is None
    assert engine.current_inference_context is inference_context


@pytest.mark.asyncio
async def test_execute_tick_returns_snapshot_and_updates_current_inference_context() -> None:
    snapshot = _Snapshot(components={"Ctx": {"value": "from component"}})
    built_context = _inference_context("tick_context")
    engine = ContextEngine(object(), object(), object())
    engine.collector = _Collector(snapshot)
    engine.reducer = _Reducer()
    engine.builder = _Builder(built_context)

    returned = await engine.execute_tick()

    assert returned is snapshot
    assert returned.components["Ctx"]["value"] == "from component"
    assert engine.last_snapshot is snapshot
    assert engine.current_inference_context is built_context
    assert engine.current_inference_context.features["tick_context"]["status"] == "ready"


def test_e5_intake_surface_remains_explicit() -> None:
    engine = ContextEngine(_inference_context("base"))

    assert hasattr(engine, "attach_e5_artifact_dir")
    assert hasattr(engine, "attach_e5_runtime_context")
    assert "e5_local_context" not in engine.current_inference_context.features


def test_set_inference_context_is_explicit_and_replaces_current_context() -> None:
    engine = ContextEngine(_inference_context("old"))
    replacement = _inference_context("replacement")

    engine.set_inference_context(replacement)

    assert engine.current_inference_context is replacement
    assert "old" not in engine.current_inference_context.features
    assert engine.current_inference_context.features["replacement"]["status"] == "ready"
