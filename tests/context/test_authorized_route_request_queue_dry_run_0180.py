from pathlib import Path
import json

import pytest

from context.authorized_route_request_queue import append_authorized_route_requests_from_context_bus
from context.authorized_route_request_queue_dry_run import (
    EXPECTED_HANDLER_SURFACES,
    RouteRequestQueueDryRunAuditError,
    audit_authorized_route_request_queue_dry_run,
)
from context.github_artifact_dataset_bus_observation import append_github_artifact_dataset_bus_observation


ROOT = Path(__file__).resolve().parents[2]


def _observation() -> dict[str, object]:
    return {
        "report_ref": "report:github-artifact:0180",
        "repository": "newicody/autodoc-ideas",
        "run_id": "run0180",
        "artifact_id": "artifact0180",
        "status": "queued",
        "dataset_root_ref": "server-dataset:github-artifacts",
        "raw_count": 1,
        "queued_count": 1,
        "failed_count": 0,
        "occurred_at": "2026-07-07T00:00:00Z",
    }


def test_0180_dry_run_audits_authorized_route_request_queue(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(runtime_root=tmp_path, raw=_observation())
    handoff = append_authorized_route_requests_from_context_bus(
        context_bus_path=tmp_path / "context.bus.jsonl",
        runtime_root=tmp_path,
        policy_decision_id="policy:allow:github-artifact:0180",
    )

    report = audit_authorized_route_request_queue_dry_run(handoff.queue_path, repo_root=ROOT)

    assert report.item_count == 1
    assert report.ready_count == 1
    assert report.blocked_count == 0
    assert report.dry_run_only is True
    assert report.scheduler_modified is False
    assert report.handler_called is False
    assert report.frames_written is False
    assert report.items[0].ready_for_later_handler_handoff is True
    assert report.items[0].policy_decision_id == "policy:allow:github-artifact:0180"


def test_0180_reports_expected_handler_surface_presence(tmp_path: Path) -> None:
    append_github_artifact_dataset_bus_observation(runtime_root=tmp_path, raw=_observation())
    handoff = append_authorized_route_requests_from_context_bus(
        context_bus_path=tmp_path / "context.bus.jsonl",
        runtime_root=tmp_path,
        policy_decision_id="policy:allow:github-artifact:0180-surfaces",
    )

    report = audit_authorized_route_request_queue_dry_run(handoff.queue_path, repo_root=ROOT)
    assert set(report.handler_surfaces) == set(EXPECTED_HANDLER_SURFACES)
    assert report.handler_surfaces["src/runtime/scheduler_route_adapter.py"] is True


def test_0180_empty_queue_is_valid_dry_run(tmp_path: Path) -> None:
    queue = tmp_path / "scheduler.route_requests.jsonl"
    queue.write_text("", encoding="utf-8")

    report = audit_authorized_route_request_queue_dry_run(queue, repo_root=ROOT)
    assert report.item_count == 0
    assert report.ready_count == 0
    assert report.blocked_count == 0


def test_0180_rejects_malformed_queue_json(tmp_path: Path) -> None:
    queue = tmp_path / "scheduler.route_requests.jsonl"
    queue.write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(Exception):
        audit_authorized_route_request_queue_dry_run(queue, repo_root=ROOT)
