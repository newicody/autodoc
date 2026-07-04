import selectors
from pathlib import Path

import pytest

from context.baby_fork_controlfs import build_route_sizing_hints_from_messages, write_baby_fork_desired_manifests
from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection
from runtime.controlfs_manifest import RouteManifest, route_manifest_path
from runtime.controlproxy_active_routes import materialize_active_route
from runtime.controlproxy_prepare import decide_route_prepare, route_prepare_request_from_message
from runtime.mmap_fixed_slot_route import MmapFixedSlotRoute
from runtime.route_notification import (
    RouteNotificationClosedError,
    RouteNotifier,
    drain_ready_count,
    eventfd_available,
    notify_after_write,
)
from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA


def _message(route_id: str = "baby_fork.retrieval") -> dict:
    return {
        "schema": ROUTE_MESSAGE_SCHEMA,
        "route_id": route_id,
        "message_id": "msg:baby_fork.retrieval.reply",
        "kind": "reply",
        "source": "retrieval_worker",
        "target": "scheduler",
        "occurred_at": "2026-07-04T20:00:00Z",
        "payload_schema": "missipy.baby_fork.route_reply.v1",
        "payload": {
            "context_id": "ctx-baby-fork-001",
            "retrieved_ids": ["baby-silicone-fork", "rounded-stainless-soft-handle"],
            "rejected_ids": ["nasa-antenna"],
        },
    }


def _report() -> dict:
    return {
        "retrieval": {
            "retrieved_ids": ["baby-silicone-fork", "rounded-stainless-soft-handle"],
            "rejected_ids": ["nasa-antenna"],
        },
        "variant_generator_stub": {
            "generated_variants": [
                {"variant_id": "variant-1"},
                {"variant_id": "variant-2"},
            ]
        },
        "final_context": {
            "context_id": "ctx-baby-fork-001",
            "context_version": 2,
            "selected_variant_id": "variant-1",
        },
    }


def _active_record(tmp_path: Path):
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    projection = build_baby_fork_runtime_projection(_report())
    hints = build_route_sizing_hints_from_messages(projection.routes)
    write_baby_fork_desired_manifests(
        controlfs_root,
        context_id="ctx-baby-fork-001",
        sizing_hints=hints,
    )
    manifest = RouteManifest.from_path(route_manifest_path(controlfs_root, "baby_fork.retrieval"))
    request = route_prepare_request_from_message(
        _message(),
        task_id=manifest.task_id,
        zone=manifest.zone,
        scope=manifest.scope,
    )
    decision = decide_route_prepare(request)
    decision = type(decision)(
        schema=decision.schema,
        request_id=decision.request_id,
        route_id=decision.route_id,
        route_handle=decision.route_handle,
        task_id=decision.task_id,
        zone=decision.zone,
        status=decision.status,
        action=decision.action,
        reason=decision.reason,
        required_frame_bytes=decision.required_frame_bytes,
        current_generation=decision.current_generation,
        next_generation=decision.next_generation,
        current_slot_size=decision.current_slot_size,
        slot_size=manifest.slot_size,
        slot_count=manifest.slot_count,
        max_frame_bytes=manifest.max_frame_bytes,
        max_ring_bytes=decision.max_ring_bytes,
        max_prepare_ms=decision.max_prepare_ms,
        drain_timeout_ms=decision.drain_timeout_ms,
        lease_switch_timeout_ms=decision.lease_switch_timeout_ms,
        notify=manifest.notify,
        overflow_policy=manifest.overflow_policy,
        decided_at=decision.decided_at,
    )
    return materialize_active_route(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        decision=decision,
        desired_manifest=manifest,
    )


def test_pipe_notifier_counts_and_selects() -> None:
    with RouteNotifier.create("baby_fork.retrieval@g1", backend="pipe") as notifier:
        assert notifier.backend == "pipe"
        assert not notifier.wait_once(timeout=0.0)

        notifier.notify(2)
        assert notifier.wait_once(timeout=0.1)
        assert notifier.drain() == 2
        assert notifier.drain() == 0

        stats = notifier.stats()
        assert stats.route_handle == "baby_fork.retrieval@g1"
        assert stats.backend == "pipe"
        assert stats.closed is False


def test_auto_notifier_uses_eventfd_or_pipe() -> None:
    with RouteNotifier.create("baby_fork.retrieval@g1", backend="auto") as notifier:
        assert notifier.backend in ("eventfd", "pipe")
        notifier.notify()
        assert notifier.wait_once(timeout=0.1)
        assert notifier.drain() == 1


def test_notifier_is_selector_friendly() -> None:
    with RouteNotifier.create("baby_fork.retrieval@g1", backend="pipe") as notifier:
        selector = selectors.DefaultSelector()
        try:
            selector.register(notifier.fileno(), selectors.EVENT_READ)
            notifier.notify(3)
            events = selector.select(timeout=0.1)
            assert events
            assert notifier.drain() == 3
        finally:
            selector.close()


def test_notifier_rejects_invalid_count() -> None:
    with RouteNotifier.create("baby_fork.retrieval@g1", backend="pipe") as notifier:
        with pytest.raises(ValueError):
            notifier.notify(0)


def test_notifier_close_blocks_future_use() -> None:
    notifier = RouteNotifier.create("baby_fork.retrieval@g1", backend="pipe")
    notifier.close()

    with pytest.raises(RouteNotificationClosedError):
        notifier.notify()


def test_eventfd_availability_probe_returns_bool() -> None:
    assert isinstance(eventfd_available(), bool)


def test_notification_integrates_with_mmap_route_write_and_drain(tmp_path: Path) -> None:
    record = _active_record(tmp_path)

    with RouteNotifier.create(record.route_handle, backend="auto") as notifier:
        route = MmapFixedSlotRoute.open(
            record.ring_path,
            route_handle=record.route_handle,
            status_path=record.mmap_status_path,
            overflow_policy=record.overflow_policy,
        )
        try:
            route.write_message(_message())
            notify_after_write(notifier, written_count=1)

            assert notifier.wait_once(timeout=0.1)
            assert drain_ready_count(notifier) == 1

            drained = route.drain()
            assert len(drained) == 1
            assert drained[0].message().route_id == "baby_fork.retrieval"
        finally:
            route.close()
