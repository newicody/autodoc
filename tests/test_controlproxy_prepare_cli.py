import json
import subprocess
import sys
from pathlib import Path

from runtime.fake_route_transport import FakeLocalRouteTransport, load_fake_bus_messages
from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA, ContextBusMessage, EventBusMessage


def _route_message() -> dict:
    return {
        "schema": ROUTE_MESSAGE_SCHEMA,
        "route_id": "baby_fork.variant_stub",
        "message_id": "msg:baby_fork.variant_stub.event",
        "kind": "event",
        "source": "variant_generator_stub",
        "target": "scheduler",
        "occurred_at": "2026-07-04T20:00:00Z",
        "payload_schema": "missipy.baby_fork.variants_generated.v1",
        "payload": {
            "context_id": "ctx-baby-fork-001",
            "variant_count": 2,
            "variant_ids": ["variant-1", "variant-2"],
        },
    }


def test_prepare_fake_routes_controlproxy_cli_writes_bus_state(tmp_path: Path) -> None:
    transport = FakeLocalRouteTransport(tmp_path)
    transport.send(_route_message())

    result = subprocess.run(
        [
            sys.executable,
            "tools/prepare_fake_routes_controlproxy.py",
            str(tmp_path),
            "--task-id",
            "ctx-baby-fork-001",
            "--replace-bus",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )

    summary = json.loads(result.stdout)
    assert summary["request_count"] == 1
    assert summary["decision_count"] == 1
    assert summary["decisions"][0]["status"] == "ready"

    event_messages = load_fake_bus_messages(tmp_path / "event.bus.jsonl")
    context_messages = load_fake_bus_messages(tmp_path / "context.bus.jsonl")
    assert isinstance(event_messages[0], EventBusMessage)
    assert isinstance(context_messages[0], ContextBusMessage)
