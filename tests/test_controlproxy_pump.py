import json
from pathlib import Path

from context.baby_fork_controlfs import build_route_sizing_hints_from_messages, write_baby_fork_desired_manifests
from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection
from runtime.controlfs_manifest import RouteManifest, route_manifest_path
from runtime.controlproxy_active_routes import active_status_path
from runtime.controlproxy_pump import route_prepare_decision_from_manifest, tick_controlproxy
from runtime.fake_route_transport import load_fake_bus_messages
from runtime.shm_runtime_schema import ContextBusMessage, EventBusMessage


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


def _write_desired(controlfs_root: Path) -> None:
    projection = build_baby_fork_runtime_projection(_report())
    hints = build_route_sizing_hints_from_messages(projection.routes)
    write_baby_fork_desired_manifests(
        controlfs_root,
        context_id="ctx-baby-fork-001",
        sizing_hints=hints,
    )


def test_route_prepare_decision_from_manifest_uses_accepted_sizing(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    _write_desired(controlfs_root)

    manifest = RouteManifest.from_path(route_manifest_path(controlfs_root, "baby_fork.retrieval"))
    decision = route_prepare_decision_from_manifest(manifest)

    assert decision.status == "ready"
    assert decision.route_handle == "baby_fork.retrieval@g1"
    assert decision.slot_size == manifest.slot_size
    assert decision.slot_count == manifest.slot_count
    assert decision.max_frame_bytes == manifest.max_frame_bytes
    assert decision.required_frame_bytes == manifest.observed_frame_bytes


def test_controlproxy_pump_materializes_missing_desired_routes(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    result = tick_controlproxy(controlfs_root=controlfs_root, runtime_root=runtime_root)

    assert result.materialized_count == 3
    assert result.error_count == 0
    assert {action.status for action in result.actions} == {"ok"}
    assert (runtime_root / "routes" / "baby_fork.retrieval@g1" / "ring.bin").exists()
    assert active_status_path(controlfs_root, "baby_fork.retrieval").exists()

    status = json.loads(active_status_path(controlfs_root, "baby_fork.retrieval").read_text(encoding="utf-8"))
    assert status["route_handle"] == "baby_fork.retrieval@g1"
    assert status["lease_state"] == "not_leased"

    after_actions = [item["action"] for item in result.plan_after["items"]]
    assert set(after_actions) == {"noop"}


def test_controlproxy_pump_second_tick_is_noop(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    tick_controlproxy(controlfs_root=controlfs_root, runtime_root=runtime_root)
    result = tick_controlproxy(controlfs_root=controlfs_root, runtime_root=runtime_root)

    assert result.materialized_count == 0
    assert result.skipped_count == 3
    assert {action.action for action in result.actions} == {"noop"}


def test_controlproxy_pump_publishes_bus_facts(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    result = tick_controlproxy(controlfs_root=controlfs_root, runtime_root=runtime_root)

    assert result.bus_event_count == 3
    assert result.bus_context_count == 3

    events = load_fake_bus_messages(runtime_root / "event.bus.jsonl")
    contexts = load_fake_bus_messages(runtime_root / "context.bus.jsonl")

    assert len(events) == 3
    assert len(contexts) == 3
    assert all(isinstance(event, EventBusMessage) for event in events)
    assert all(isinstance(context, ContextBusMessage) for context in contexts)
    assert {event.topic for event in events} == {"controlproxy.pump.route_materialized"}
    assert {context.topic for context in contexts} == {"controlproxy.pump.active_route"}


def test_controlproxy_pump_does_not_issue_lease(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)

    tick_controlproxy(controlfs_root=controlfs_root, runtime_root=runtime_root)

    assert not (controlfs_root / "active" / "routes" / "baby_fork.retrieval" / "lease.json").exists()
    status = json.loads(active_status_path(controlfs_root, "baby_fork.retrieval").read_text(encoding="utf-8"))
    assert status["lease_state"] == "not_leased"


def test_controlproxy_pump_skips_update_instead_of_live_resize(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "runtime"
    _write_desired(controlfs_root)
    tick_controlproxy(controlfs_root=controlfs_root, runtime_root=runtime_root)

    manifest_path = route_manifest_path(controlfs_root, "baby_fork.retrieval")
    desired = json.loads(manifest_path.read_text(encoding="utf-8"))
    desired["slot_size"] = 4096
    desired["max_frame_bytes"] = 4096
    manifest_path.write_text(json.dumps(desired, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = tick_controlproxy(controlfs_root=controlfs_root, runtime_root=runtime_root)

    update_actions = [action for action in result.actions if action.route_id == "baby_fork.retrieval"]
    assert update_actions[0].action == "update"
    assert update_actions[0].status == "skipped"
    assert "live mmap resize is forbidden" in update_actions[0].reason
