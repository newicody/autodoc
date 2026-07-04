import json
from pathlib import Path

import pytest

from context.baby_fork_controlfs import (
    build_baby_fork_routeproxy_plan,
    build_route_sizing_hints_from_messages,
    choose_slot_size,
    write_baby_fork_desired_manifests,
)
from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection
from runtime.controlfs_manifest import ManifestValidationError, ROUTE_MANIFEST_SCHEMA, RouteManifest
from runtime.controlproxy_prepare import (
    ROUTE_PREPARE_REQUEST_SCHEMA,
    ControlProxyZonePolicy,
    controlproxy_decision_to_context,
    controlproxy_decision_to_event,
    decide_route_prepare,
    route_prepare_request_from_message,
    write_controlproxy_decisions_to_fake_bus,
)
from runtime.fake_route_transport import load_fake_bus_messages
from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA, ContextBusMessage, EventBusMessage


def _base_manifest() -> dict:
    return {
        "schema": ROUTE_MANIFEST_SCHEMA,
        "route_id": "baby_fork.retrieval",
        "task_id": "ctx-baby-fork-001",
        "zone": "workers",
        "scope": "context.read",
        "producer": "scheduler",
        "consumer": "retrieval_worker",
        "ttl_seconds": 300,
        "mode": "rw",
        "message_schema": "missipy.shm.route_message.v1",
        "created_by": "scheduler",
        "created_at": "2026-07-04T20:00:00Z",
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


def _route_message(route_id: str = "baby_fork.retrieval") -> dict:
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


def _active_manifest(slot_size: int) -> RouteManifest:
    raw = _base_manifest()
    raw.update(
        {
            "transport": "mmap.fixed_slot",
            "slot_size": slot_size,
            "slot_count": 16,
            "max_frame_bytes": slot_size,
            "overflow_policy": "reject",
            "notify": "semaphore",
        }
    )
    return RouteManifest.from_mapping(raw)


def test_route_manifest_accepts_controlproxy_sizing_fields() -> None:
    raw = _base_manifest()
    raw.update(
        {
            "transport": "mmap.fixed_slot",
            "slot_size": 2048,
            "slot_count": 16,
            "max_frame_bytes": 2048,
            "overflow_policy": "reject",
            "notify": "semaphore",
            "sizing_source": "controlproxy.prepare",
            "observed_frame_bytes": 890,
        }
    )

    manifest = RouteManifest.from_mapping(raw)

    assert manifest.transport == "mmap.fixed_slot"
    assert manifest.slot_size == 2048
    assert manifest.notify == "semaphore"
    assert manifest.to_mapping()["observed_frame_bytes"] == 890


def test_route_manifest_rejects_frame_larger_than_slot() -> None:
    raw = _base_manifest()
    raw.update(
        {
            "transport": "mmap.fixed_slot",
            "slot_size": 1024,
            "slot_count": 16,
            "max_frame_bytes": 2048,
            "overflow_policy": "reject",
            "notify": "semaphore",
        }
    )

    with pytest.raises(ManifestValidationError, match="max_frame_bytes"):
        RouteManifest.from_mapping(raw)


def test_baby_fork_sizing_hints_are_measured_from_encoded_frames() -> None:
    projection = build_baby_fork_runtime_projection(_report())
    hints = build_route_sizing_hints_from_messages(projection.routes)

    assert set(hints) == {
        "baby_fork.context_gate",
        "baby_fork.retrieval",
        "baby_fork.variant_stub",
    }
    assert choose_slot_size(475, headroom_bytes=256) == 1024
    assert choose_slot_size(890, headroom_bytes=256) == 2048
    assert all(hint.slot_size >= hint.observed_frame_bytes for hint in hints.values())


def test_routeproxy_plan_sees_sizing_change_as_update(tmp_path: Path) -> None:
    projection = build_baby_fork_runtime_projection(_report())
    hints = build_route_sizing_hints_from_messages(projection.routes)

    write_baby_fork_desired_manifests(
        tmp_path,
        context_id="ctx-baby-fork-001",
        sizing_hints=hints,
    )

    active_manifest = json.loads(
        (tmp_path / "desired" / "routes" / "baby_fork.retrieval" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    active_manifest["slot_size"] = 1024
    active_manifest["max_frame_bytes"] = 1024
    active_manifest["sizing_source"] = "old.active"

    active_path = tmp_path / "active" / "routes" / "baby_fork.retrieval" / "manifest.json"
    active_path.parent.mkdir(parents=True)
    active_path.write_text(json.dumps(active_manifest), encoding="utf-8")

    plan = build_baby_fork_routeproxy_plan(
        tmp_path,
        context_id="ctx-baby-fork-001",
        write_desired=False,
    )

    update_items = [item for item in plan.by_action("update") if item.route_id == "baby_fork.retrieval"]
    assert len(update_items) == 1
    assert update_items[0].desired.slot_size != update_items[0].active.slot_size


def test_prepare_request_is_short_and_contains_required_frame_size() -> None:
    request = route_prepare_request_from_message(
        _route_message(),
        task_id="ctx-baby-fork-001",
        zone="workers",
        scope="context.read",
    )

    assert request.schema == ROUTE_PREPARE_REQUEST_SCHEMA
    assert request.route_id == "baby_fork.retrieval"
    assert request.required_frame_bytes > 0
    assert "payload" not in request.to_mapping()


def test_controlproxy_decision_actions() -> None:
    request = route_prepare_request_from_message(
        _route_message(),
        task_id="ctx-baby-fork-001",
        zone="workers",
        scope="context.read",
    )

    first = decide_route_prepare(request)
    reuse = decide_route_prepare(request, active_manifest=_active_manifest(4096))
    next_gen = decide_route_prepare(request, active_manifest=_active_manifest(64))

    assert first.action == "create_route_generation"
    assert first.route_handle == "baby_fork.retrieval@g1"
    assert reuse.action == "reuse_active"
    assert next_gen.action == "create_next_generation"
    assert next_gen.route_handle == "baby_fork.retrieval@g2"


def test_controlproxy_denies_when_zone_budget_is_too_small() -> None:
    request = route_prepare_request_from_message(
        _route_message(),
        task_id="ctx-baby-fork-001",
        zone="workers",
        scope="context.read",
    )
    policies = {
        "workers": ControlProxyZonePolicy(
            zone="workers",
            max_slot_size=128,
            default_slot_count=16,
            max_ring_bytes=4096,
        )
    }

    decision = decide_route_prepare(request, zone_policies=policies)

    assert decision.status == "denied"
    assert decision.action == "deny"


def test_controlproxy_decision_projects_to_event_and_context_bus(tmp_path: Path) -> None:
    request = route_prepare_request_from_message(
        _route_message(),
        task_id="ctx-baby-fork-001",
        zone="workers",
        scope="context.read",
    )
    decision = decide_route_prepare(request)

    event = controlproxy_decision_to_event(decision)
    context = controlproxy_decision_to_context(decision)
    counts = write_controlproxy_decisions_to_fake_bus(tmp_path, [decision], append=False)

    assert isinstance(event, EventBusMessage)
    assert isinstance(context, ContextBusMessage)
    assert event.topic == "controlproxy.route.ready"
    assert context.topic == "controlproxy.route.state"
    assert counts == {"decision_count": 1, "event_count": 1, "context_count": 1}
    assert isinstance(load_fake_bus_messages(tmp_path / "event.bus.jsonl")[0], EventBusMessage)
    assert isinstance(load_fake_bus_messages(tmp_path / "context.bus.jsonl")[0], ContextBusMessage)
