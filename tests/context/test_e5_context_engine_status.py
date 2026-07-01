from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType

import pytest

from contracts.context import InferenceContext, freeze_mapping
from context.e5_context_engine_status import (
    E5ContextEngineStatusPolicy,
    inspect_e5_context_engine,
    inspect_e5_inference_context,
)
from context.engine import ContextEngine


@dataclass(frozen=True, slots=True)
class Snapshot:
    components: Mapping[str, object]


def _context() -> InferenceContext:
    return InferenceContext(
        features=freeze_mapping(
            {
                "manual_note": {"status": "kept"},
                "e5_local_context": {
                    "status": "ready",
                    "query": "OpenVINO local",
                    "selected_item_count": 5,
                    "used_context_chars": 1469,
                    "prompt_chars": 1849,
                },
            }
        ),
        priorities=freeze_mapping({"manual_note": 3, "e5_local_context": 20}),
    )


def test_status_reads_e5_feature_without_mutating_context() -> None:
    inference_context = _context()

    status = inspect_e5_inference_context(inference_context)

    assert status.attached is True
    assert status.ready is True
    assert status.priority == 20
    assert status.query == "OpenVINO local"
    assert status.selected_item_count == 5
    assert status.used_context_chars == 1469
    assert status.prompt_chars == 1849
    assert inference_context.features["e5_local_context"]["status"] == "ready"


def test_status_json_projection_is_stable() -> None:
    payload = inspect_e5_inference_context(_context()).to_json_dict()

    assert payload == {
        "schema": "missipy.e5.context_engine_status.v1",
        "component_name": "e5_local_context",
        "feature_count": 2,
        "priority_count": 2,
        "attached": True,
        "ready": True,
        "priority": 20,
        "query": "OpenVINO local",
        "selected_item_count": 5,
        "used_context_chars": 1469,
        "prompt_chars": 1849,
        "snapshot_available": False,
        "snapshot_component_count": None,
    }


def test_status_text_projection_is_readable() -> None:
    text = inspect_e5_inference_context(_context()).to_text()

    assert "schema: missipy.e5.context_engine_status.v1" in text
    assert "attached: true" in text
    assert "ready: true" in text
    assert "query: OpenVINO local" in text


def test_status_reports_absent_component() -> None:
    inference_context = InferenceContext(
        features=freeze_mapping({"manual_note": {"status": "kept"}}),
        priorities=freeze_mapping({"manual_note": 3}),
    )

    status = inspect_e5_inference_context(inference_context)

    assert status.attached is False
    assert status.ready is False
    assert status.priority is None
    assert status.query is None


def test_status_can_inspect_context_engine_snapshot() -> None:
    engine = ContextEngine(_context())
    engine.last_snapshot = Snapshot(components=MappingProxyType({"Ctx": object()}))

    status = inspect_e5_context_engine(engine)

    assert status.snapshot_available is True
    assert status.snapshot_component_count == 1
    assert status.attached is True


def test_status_policy_can_select_component_name() -> None:
    inference_context = InferenceContext(
        features=freeze_mapping({"custom_e5": {"status": "ready", "query": "custom"}}),
        priorities=freeze_mapping({"custom_e5": 11}),
    )

    status = inspect_e5_inference_context(
        inference_context,
        E5ContextEngineStatusPolicy(component_name="custom_e5"),
    )

    assert status.component_name == "custom_e5"
    assert status.ready is True
    assert status.priority == 11
    assert status.query == "custom"


def test_status_policy_rejects_empty_component_name() -> None:
    with pytest.raises(ValueError, match="component_name must not be empty"):
        E5ContextEngineStatusPolicy(component_name=" ")
