from pathlib import Path
import json

import pytest

from context.github_artifact_context_bus_scheduler_intake import (
    ContextBusSchedulerIntakeReaderError,
    build_github_artifact_scheduler_intake_from_context_bus_message,
    read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl,
)
from context.github_artifact_dataset_bus_observation import (
    append_github_artifact_dataset_bus_observation,
)
from runtime.scheduler_route_adapter import SCHEDULER_ROUTE_REQUEST_SCHEMA
from runtime.shm_runtime_schema import CONTEXT_BUS_MESSAGE_SCHEMA


def _dataset_observation() -> dict[str, object]:
    return {
        "report_ref": "report:github-artifact:0178",
        "repository": "newicody/autodoc-ideas",
        "run_id": "run0178",
        "artifact_id": "artifact0178",
        "status": "queued",
        "dataset_root_ref": "server-dataset:github-artifacts",
        "raw_count": 2,
        "queued_count": 1,
        "failed_count": 0,
        "occurred_at": "2026-07-07T00:00:00Z",
    }


def test_0178_reads_context_bus_message_emitted_by_0176(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(
        runtime_root=tmp_path,
        raw=_dataset_observation(),
    )

    plans = read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl(
        tmp_path / "context.bus.jsonl"
    )

    assert len(plans) == 1
    plan = plans[0]
    assert plan.authorized is False
    assert plan.scheduler_route_request is None
    assert plan.candidate.observation_ref.startswith("ctx:")
    assert plan.candidate.repository == "newicody/autodoc-ideas"
    assert plan.candidate.status == "queued"


def test_0178_can_emit_authorized_route_request_from_context_bus(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(
        runtime_root=tmp_path,
        raw=_dataset_observation(),
    )

    plans = read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl(
        tmp_path / "context.bus.jsonl",
        policy_decision_id="policy:allow:github-artifact:0178",
        authorized=True,
    )

    assert len(plans) == 1
    request = plans[0].scheduler_route_request
    assert request is not None
    assert request["schema"] == SCHEDULER_ROUTE_REQUEST_SCHEMA
    assert request["authorized"] is True
    assert request["policy_decision_id"] == "policy:allow:github-artifact:0178"


def test_0178_rejects_non_matching_context_bus_message(tmp_path: Path) -> None:
    path = tmp_path / "context.bus.jsonl"
    path.write_text(
        json.dumps(
            {
                "schema": CONTEXT_BUS_MESSAGE_SCHEMA,
                "context_id": "ctx:other",
                "context_version": 1,
                "topic": "other.topic",
                "source": "test",
                "occurred_at": "2026-07-07T00:00:00Z",
                "zone": "server",
                "payload_schema": "missipy.other.schema.v1",
                "payload": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    plans = read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl(path)
    assert plans == []

    with pytest.raises(ContextBusSchedulerIntakeReaderError, match="non matching context bus message"):
        read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl(
            path,
            include_non_matching=True,
        )


def test_0178_single_message_builder_requires_context_bus_fact(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(
        runtime_root=tmp_path,
        raw=_dataset_observation(),
    )
    message = json.loads((tmp_path / "context.bus.jsonl").read_text(encoding="utf-8"))

    plan = build_github_artifact_scheduler_intake_from_context_bus_message(message)
    assert plan.candidate.dataset_root_ref == "server-dataset:github-artifacts"
