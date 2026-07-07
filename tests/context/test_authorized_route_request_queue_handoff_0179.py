from pathlib import Path
import json

import pytest

from context.authorized_route_request_queue import (
    AuthorizedRouteRequestQueueError,
    append_authorized_route_requests_from_context_bus,
    iter_authorized_route_request_queue,
)
from context.github_artifact_dataset_bus_observation import append_github_artifact_dataset_bus_observation
from runtime.scheduler_route_adapter import SchedulerRouteRequest


def _observation(run_id: str = "run0179") -> dict[str, object]:
    return {
        "report_ref": f"report:github-artifact:{run_id}",
        "repository": "newicody/autodoc-ideas",
        "run_id": run_id,
        "artifact_id": f"artifact-{run_id}",
        "status": "queued",
        "dataset_root_ref": "server-dataset:github-artifacts",
        "raw_count": 1,
        "queued_count": 1,
        "failed_count": 0,
        "occurred_at": "2026-07-07T00:00:00Z",
    }


def test_0179_appends_authorized_route_request_queue_from_context_bus(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(runtime_root=tmp_path, raw=_observation())

    report = append_authorized_route_requests_from_context_bus(
        context_bus_path=tmp_path / "context.bus.jsonl",
        runtime_root=tmp_path,
        policy_decision_id="policy:allow:github-artifact:0179",
    )

    assert report.queued_count == 1
    assert report.authorized_only is True
    assert report.scheduler_modified is False
    assert report.handler_called is False
    queue_path = Path(report.queue_path)
    assert queue_path.name == "scheduler.route_requests.jsonl"
    line = queue_path.read_text(encoding="utf-8").strip()
    request = SchedulerRouteRequest.from_mapping(json.loads(line))
    assert request.authorized is True
    assert request.policy_decision_id == "policy:allow:github-artifact:0179"


def test_0179_queue_reader_yields_authorized_requests(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(runtime_root=tmp_path, raw=_observation("run0179reader"))
    report = append_authorized_route_requests_from_context_bus(
        context_bus_path=tmp_path / "context.bus.jsonl",
        runtime_root=tmp_path,
        policy_decision_id="policy:allow:github-artifact:reader0179",
    )

    requests = list(iter_authorized_route_request_queue(report.queue_path))
    assert len(requests) == 1
    assert requests[0].authorized is True
    assert requests[0].route_id.startswith("route-")


def test_0179_requires_policy_decision_id(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(runtime_root=tmp_path, raw=_observation("run0179missingpolicy"))
    with pytest.raises(AuthorizedRouteRequestQueueError, match="policy_decision_id is required"):
        append_authorized_route_requests_from_context_bus(
            context_bus_path=tmp_path / "context.bus.jsonl",
            runtime_root=tmp_path,
            policy_decision_id="",
        )


def test_0179_rejects_unsafe_queue_name(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(runtime_root=tmp_path, raw=_observation("run0179unsafequeue"))
    with pytest.raises(AuthorizedRouteRequestQueueError, match="local filename"):
        append_authorized_route_requests_from_context_bus(
            context_bus_path=tmp_path / "context.bus.jsonl",
            runtime_root=tmp_path,
            policy_decision_id="policy:allow:github-artifact:unsafequeue",
            queue_name="../bad.jsonl",
        )
