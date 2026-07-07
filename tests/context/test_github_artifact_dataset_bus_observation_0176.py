from pathlib import Path
import json

import pytest

from context.github_artifact_dataset_bus_observation import (
    GITHUB_ARTIFACT_DATASET_CONTEXT_SCHEMA,
    GITHUB_ARTIFACT_DATASET_OBSERVATION_SCHEMA,
    GithubArtifactDatasetBusObservationError,
    append_github_artifact_dataset_bus_observation,
    build_github_artifact_dataset_bus_observation,
)
from runtime.shm_runtime_schema import (
    CONTEXT_BUS_MESSAGE_SCHEMA,
    EVENT_BUS_MESSAGE_SCHEMA,
    ContextBusMessage,
    EventBusMessage,
)


def _raw() -> dict[str, object]:
    return {
        "report_ref": "report:github-artifact:0167",
        "repository": "newicody/autodoc-ideas",
        "run_id": "run0176",
        "artifact_id": "artifact0176",
        "status": "synced",
        "dataset_root_ref": "server-dataset:github-artifacts",
        "raw_count": 3,
        "queued_count": 2,
        "failed_count": 0,
        "occurred_at": "2026-07-07T00:00:00Z",
    }


def test_0176_builds_existing_event_and_context_bus_messages() -> None:
    projection = build_github_artifact_dataset_bus_observation(_raw())

    assert isinstance(projection.event, EventBusMessage)
    assert isinstance(projection.context, ContextBusMessage)
    assert projection.event.schema == EVENT_BUS_MESSAGE_SCHEMA
    assert projection.context.schema == CONTEXT_BUS_MESSAGE_SCHEMA
    assert projection.event.payload_schema == GITHUB_ARTIFACT_DATASET_OBSERVATION_SCHEMA
    assert projection.context.payload_schema == GITHUB_ARTIFACT_DATASET_CONTEXT_SCHEMA
    assert projection.event.payload["observation_only"] is True
    assert projection.event.payload["vispy_direct_write"] is False
    assert projection.context.payload["scheduler_modified"] is False
    assert projection.to_mapping()["creates_parallel_bus"] is False


def test_0176_appends_jsonl_to_existing_bus_files(tmp_path: Path) -> None:
    projection = append_github_artifact_dataset_bus_observation(
        runtime_root=tmp_path,
        raw=_raw(),
    )

    event_lines = (tmp_path / "event.bus.jsonl").read_text(encoding="utf-8").splitlines()
    context_lines = (tmp_path / "context.bus.jsonl").read_text(encoding="utf-8").splitlines()

    assert len(event_lines) == projection.event_count == 1
    assert len(context_lines) == projection.context_count == 1
    event = EventBusMessage.from_mapping(json.loads(event_lines[0]))
    context = ContextBusMessage.from_mapping(json.loads(context_lines[0]))
    assert event.topic == "github.artifact_dataset.observed"
    assert context.topic == "github.artifact_dataset.context"


def test_0176_rejects_unknown_status() -> None:
    raw = _raw()
    raw["status"] = "abandoned"
    with pytest.raises(GithubArtifactDatasetBusObservationError, match="locked activity vocabulary"):
        build_github_artifact_dataset_bus_observation(raw)
