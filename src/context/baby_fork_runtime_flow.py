"""Baby-fork end-to-end runtime flow CLI helpers.

This module implements phase 0074.

It deliberately does not:
- run the real Scheduler
- start RouteProxy
- create shared memory
- create semaphores
- implement a ring buffer
- mutate active/routes
- mutate revoked/routes
- require ZFS
- implement NetworkBridge or HardwareBridge

It only orchestrates already-validated local pieces:
baby-fork report -> runtime projection -> fake runtime -> recorder journal
and optionally writes ControlFS desired manifests plus a RouteProxy dry-run plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any, Mapping

from context.baby_fork_controlfs import (
    baby_fork_controlfs_summary,
    build_baby_fork_routeproxy_plan,
    build_route_sizing_hints_from_messages,
)
from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection
from runtime.fake_route_transport import write_projection_to_fake_runtime
from runtime.fake_runtime_recorder import ingest_fake_runtime_to_journal


@dataclass(frozen=True)
class BabyForkRuntimeFlowSummary:
    """End-to-end baby-fork runtime flow summary."""

    report_path: str
    fake_runtime_root: str
    journal_path: str
    projection: dict[str, int]
    fake_runtime: dict[str, Any]
    recorder: dict[str, Any]
    controlfs: dict[str, Any] | None = None

    def to_mapping(self) -> dict[str, Any]:
        payload = {
            "report_path": self.report_path,
            "fake_runtime_root": self.fake_runtime_root,
            "journal_path": self.journal_path,
            "projection": self.projection,
            "fake_runtime": self.fake_runtime,
            "recorder": self.recorder,
        }
        if self.controlfs is not None:
            payload["controlfs"] = self.controlfs
        return payload


def run_baby_fork_runtime_flow(
    report_path: Path | str,
    fake_runtime_root: Path | str,
    journal_path: Path | str,
    *,
    occurred_at: str = "2026-07-04T20:00:00Z",
    append_journal: bool = False,
    controlfs_root: Path | str | None = None,
    context_id: str | None = None,
) -> BabyForkRuntimeFlowSummary:
    """Run the file-backed end-to-end baby-fork runtime flow.

    The flow writes/updates:
      - fake runtime files
      - runtime recorder journal
      - optional ControlFS desired manifests

    It does not create active routes or real shared memory.
    """

    report_file = Path(report_path)
    fake_root = Path(fake_runtime_root)
    journal = Path(journal_path)

    report = _load_report(report_file)
    effective_context_id = context_id or _context_id_from_report(report)

    projection = build_baby_fork_runtime_projection(
        report,
        report_uri=str(report_file),
        occurred_at=occurred_at,
    )

    fake_snapshot = write_projection_to_fake_runtime(
        fake_root,
        data_handles=projection.data_handles,
        events=projection.events,
        contexts=projection.contexts,
        routes=projection.routes,
    )

    recorder_summary = ingest_fake_runtime_to_journal(
        fake_root,
        journal,
        append=append_journal,
    )

    controlfs_summary: dict[str, Any] | None = None
    if controlfs_root is not None:
        sizing_hints = build_route_sizing_hints_from_messages(projection.routes)
        plan = build_baby_fork_routeproxy_plan(
            controlfs_root,
            context_id=effective_context_id,
            sizing_hints=sizing_hints,
        )
        controlfs_summary = baby_fork_controlfs_summary(controlfs_root, plan)

    return BabyForkRuntimeFlowSummary(
        report_path=str(report_file),
        fake_runtime_root=str(fake_root),
        journal_path=str(journal),
        projection={
            "data_handle_count": len(projection.data_handles),
            "event_count": len(projection.events),
            "context_count": len(projection.contexts),
            "route_message_count": len(projection.routes),
        },
        fake_runtime=fake_snapshot.to_mapping(),
        recorder=recorder_summary.to_mapping(),
        controlfs=controlfs_summary,
    )


def _load_report(path: Path) -> Mapping[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid baby-fork report JSON: {exc}") from exc

    if not isinstance(report, dict):
        raise ValueError("baby-fork report must be a JSON object")
    return report


def _context_id_from_report(report: Mapping[str, Any]) -> str:
    final_context = report.get("final_context")
    if isinstance(final_context, Mapping):
        value = final_context.get("context_id")
        if value:
            return str(value)

    value = report.get("context_id")
    if value:
        return str(value)

    return "baby_fork_smoke"
