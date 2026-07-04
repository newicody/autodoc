from pathlib import Path

from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection
from runtime.fake_route_transport import (
    FakeLocalRouteTransport,
    load_fake_bus_messages,
    write_projection_to_fake_runtime,
)
from runtime.shm_runtime_schema import DataHandle, EventBusMessage, ContextBusMessage, RouteMessage


def _report() -> dict:
    return {
        "ok": True,
        "retrieval": {
            "retrieved_ids": ["baby-silicone-fork", "rounded-stainless-soft-handle"],
            "rejected_ids": ["nasa-antenna"],
        },
        "variant_generator_stub": {
            "generated_variants": [
                {"variant_id": "variant-1", "label": "soft silicone baby fork", "score": 0.86},
                {"variant_id": "variant-2", "label": "rounded stainless with soft handle", "score": 0.74},
            ]
        },
        "final_context": {
            "context_id": "ctx-baby-fork-001",
            "context_version": 2,
            "selected_variant_id": "variant-1",
        },
    }


def test_fake_route_transport_send_receive_and_drain(tmp_path: Path) -> None:
    projection = build_baby_fork_runtime_projection(_report())
    transport = FakeLocalRouteTransport(tmp_path)

    sent = transport.send(projection.routes[0])
    received = transport.receive(sent.route_id)

    assert received == (sent,)
    assert transport.route_ids() == ("baby_fork.retrieval",)

    drained = transport.drain(sent.route_id)
    assert drained == (sent,)
    assert transport.receive(sent.route_id) == ()


def test_write_projection_to_fake_runtime_surface(tmp_path: Path) -> None:
    projection = build_baby_fork_runtime_projection(_report())

    snapshot = write_projection_to_fake_runtime(
        tmp_path,
        data_handles=projection.data_handles,
        events=projection.events,
        contexts=projection.contexts,
        routes=projection.routes,
    )

    assert snapshot.data_handle_count == 1
    assert snapshot.event_count == 2
    assert snapshot.context_count == 1
    assert snapshot.route_message_count == 3
    assert snapshot.route_ids == (
        "baby_fork.context_gate",
        "baby_fork.retrieval",
        "baby_fork.variant_stub",
    )

    assert (tmp_path / "data.index.jsonl").exists()
    assert (tmp_path / "event.bus.jsonl").exists()
    assert (tmp_path / "context.bus.jsonl").exists()
    assert (tmp_path / "routes" / "baby_fork.retrieval" / "messages.jsonl").exists()


def test_fake_runtime_bus_files_load_as_validated_messages(tmp_path: Path) -> None:
    projection = build_baby_fork_runtime_projection(_report())
    write_projection_to_fake_runtime(
        tmp_path,
        data_handles=projection.data_handles,
        events=projection.events,
        contexts=projection.contexts,
        routes=projection.routes,
    )

    data_messages = load_fake_bus_messages(tmp_path / "data.index.jsonl")
    event_messages = load_fake_bus_messages(tmp_path / "event.bus.jsonl")
    context_messages = load_fake_bus_messages(tmp_path / "context.bus.jsonl")

    assert isinstance(data_messages[0], DataHandle)
    assert all(isinstance(message, EventBusMessage) for message in event_messages)
    assert isinstance(context_messages[0], ContextBusMessage)


def test_fake_transport_snapshot_contains_routes(tmp_path: Path) -> None:
    projection = build_baby_fork_runtime_projection(_report())
    transport = FakeLocalRouteTransport(tmp_path)

    for message in projection.routes:
        transport.send(message)

    snapshot = transport.snapshot()

    assert set(snapshot) == {
        "baby_fork.retrieval",
        "baby_fork.variant_stub",
        "baby_fork.context_gate",
    }
    assert snapshot["baby_fork.variant_stub"][0]["payload"]["variant_count"] == 2
