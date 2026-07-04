import json
from pathlib import Path

import pytest

from runtime.controlproxy_prepare import decide_route_prepare, route_prepare_request_from_message
from runtime.mmap_fixed_slot_route import (
    MmapFrameTooLargeError,
    MmapFixedSlotRoute,
    MmapRouteFullError,
    create_mmap_route_from_decision,
    materialize_decisions,
    route_file_size,
)
from runtime.route_frame_codec import encode_route_message_frame
from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA


def _message(message_id: str = "msg:baby_fork.retrieval.reply", route_id: str = "baby_fork.retrieval") -> dict:
    return {
        "schema": ROUTE_MESSAGE_SCHEMA,
        "route_id": route_id,
        "message_id": message_id,
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


def _decision(message: dict | None = None):
    msg = message or _message()
    request = route_prepare_request_from_message(
        msg,
        task_id="ctx-baby-fork-001",
        zone="workers",
        scope="context.read",
    )
    return decide_route_prepare(request)


def test_route_file_size_includes_header_and_fixed_slots() -> None:
    assert route_file_size(1024, 16) == 128 + 16 * (64 + 1024)


def test_create_mmap_route_from_controlproxy_decision(tmp_path: Path) -> None:
    decision = _decision()

    route = create_mmap_route_from_decision(tmp_path, decision)
    try:
        stats = route.stats()
        assert stats.route_handle == "baby_fork.retrieval@g1"
        assert stats.slot_size >= decision.required_frame_bytes
        assert stats.slot_count == 16
        assert stats.occupancy == 0
        assert Path(stats.ring_path).exists()
        assert Path(stats.status_path).exists()

        status = json.loads(Path(stats.status_path).read_text(encoding="utf-8"))
        assert status["schema"] == "missipy.mmap.fixed_slot_route_status.v1"
        assert status["transport"] == "mmap.fixed_slot"
        assert status["materialized_from"]["schema"] == "missipy.controlproxy.route_prepare_status.v1"
    finally:
        route.close()


def test_mmap_route_write_drain_and_decode(tmp_path: Path) -> None:
    route = create_mmap_route_from_decision(tmp_path, _decision())
    try:
        slot = route.write_message(_message())
        assert slot.sequence == 0
        assert route.stats().occupancy == 1

        drained = route.drain()
        assert len(drained) == 1
        assert drained[0].message().message_id == "msg:baby_fork.retrieval.reply"
        assert route.stats().occupancy == 0
        assert route.stats().read_sequence == 1
    finally:
        route.close()


def test_mmap_route_rejects_frame_larger_than_slot(tmp_path: Path) -> None:
    route_dir = tmp_path / "routes" / "tiny@g1"
    route_dir.mkdir(parents=True)
    ring = route_dir / "ring.bin"
    ring.write_bytes(b"\x00" * route_file_size(128, 1))
    route = MmapFixedSlotRoute.open(ring, route_handle="tiny@g1")
    try:
        route.initialize(slot_size=128, slot_count=1)
        with pytest.raises(MmapFrameTooLargeError):
            route.write_message(_message())
    finally:
        route.close()


def test_mmap_route_rejects_full_ring_by_default(tmp_path: Path) -> None:
    msg = _message()
    decision = _decision(msg)
    route = create_mmap_route_from_decision(tmp_path, decision)
    try:
        # Reinitialize small count with the same slot size.
        route.close()
        ring = tmp_path / "routes" / decision.route_handle / "ring.bin"
        ring.write_bytes(b"\x00" * route_file_size(decision.slot_size, 1))
        route = MmapFixedSlotRoute.open(ring, route_handle=decision.route_handle)
        route.initialize(slot_size=decision.slot_size, slot_count=1)

        route.write_message(_message("msg:one"))
        with pytest.raises(MmapRouteFullError):
            route.write_message(_message("msg:two"))
    finally:
        route.close()


def test_mmap_route_drop_oldest_mode(tmp_path: Path) -> None:
    msg = _message()
    decision = _decision(msg)
    route_dir = tmp_path / "routes" / "drop@g1"
    route_dir.mkdir(parents=True)
    ring = route_dir / "ring.bin"
    ring.write_bytes(b"\x00" * route_file_size(decision.slot_size, 1))
    route = MmapFixedSlotRoute.open(ring, route_handle="drop@g1", overflow_policy="drop_oldest")
    try:
        route.initialize(slot_size=decision.slot_size, slot_count=1)
        route.write_message(_message("msg:one"))
        route.write_message(_message("msg:two"))

        assert route.stats().dropped_count == 1
        drained = route.drain()
        assert len(drained) == 1
        assert drained[0].message().message_id == "msg:two"
    finally:
        route.close()


def test_materialize_decisions_filters_denied(tmp_path: Path) -> None:
    decision = _decision()
    routes = materialize_decisions(tmp_path, [decision])
    try:
        assert len(routes) == 1
        assert routes[0].route_handle == "baby_fork.retrieval@g1"
    finally:
        for route in routes:
            route.close()


def test_mmap_route_accepts_preencoded_frame(tmp_path: Path) -> None:
    decision = _decision()
    route = create_mmap_route_from_decision(tmp_path, decision)
    try:
        frame = encode_route_message_frame(_message())
        route.write_frame(frame)
        drained = route.drain()
        assert drained[0].frame == frame
    finally:
        route.close()
