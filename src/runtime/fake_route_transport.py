"""Fake local route transport for schema-level runtime tests.

This module implements the P5-prep fake route transport.

It deliberately does not:
- create shared memory
- create semaphores
- implement a ring buffer
- watch ControlFS
- call Scheduler
- call RouteProxy
- access ZFS
- implement NetworkBridge or HardwareBridge

It stores validated runtime messages as JSONL files under a caller-provided
directory so tests can exercise route/event/context/data-handle flow before
real /dev/shm transport exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import shutil
from typing import Iterable, Mapping, Any

from runtime.shm_runtime_schema import (
    ContextBusMessage,
    DataHandle,
    EventBusMessage,
    RouteMessage,
    parse_runtime_message,
)


@dataclass(frozen=True)
class FakeRuntimeSnapshot:
    """Counts written into the fake runtime surface."""

    data_handle_count: int
    event_count: int
    context_count: int
    route_message_count: int
    route_ids: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "data_handle_count": self.data_handle_count,
            "event_count": self.event_count,
            "context_count": self.context_count,
            "route_message_count": self.route_message_count,
            "route_ids": list(self.route_ids),
        }


class FakeLocalRouteTransport:
    """File-backed fake local route transport.

    Layout:

    <root>/
      routes/<route_id>/messages.jsonl

    The class validates every RouteMessage before appending it. It is not a
    concurrent transport and it is not the future shm implementation.
    """

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.routes_root = self.root / "routes"

    def send(self, message: RouteMessage | Mapping[str, Any]) -> RouteMessage:
        """Append a validated RouteMessage to its route JSONL file."""

        parsed = _route_message(message)
        path = self._route_file(parsed.route_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(parsed.to_mapping(), sort_keys=True, separators=(",", ":")))
            handle.write("\n")
        return parsed

    def receive(self, route_id: str) -> tuple[RouteMessage, ...]:
        """Read all messages currently stored for a route."""

        path = self._route_file(route_id)
        if not path.exists():
            return ()

        messages: list[RouteMessage] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parsed = parse_runtime_message(json.loads(line))
            if not isinstance(parsed, RouteMessage):
                raise TypeError(f"route file contained non-route message: {type(parsed).__name__}")
            messages.append(parsed)
        return tuple(messages)

    def drain(self, route_id: str) -> tuple[RouteMessage, ...]:
        """Read and remove all messages for a route."""

        messages = self.receive(route_id)
        path = self._route_file(route_id)
        if path.exists():
            path.write_text("", encoding="utf-8")
        return messages

    def route_ids(self) -> tuple[str, ...]:
        """Return route IDs that have a fake route file."""

        if not self.routes_root.exists():
            return ()
        return tuple(
            child.name
            for child in sorted(self.routes_root.iterdir())
            if child.is_dir() and (child / "messages.jsonl").exists()
        )

    def snapshot(self) -> dict[str, list[dict[str, Any]]]:
        """Return all route messages as a JSON-serializable snapshot."""

        return {
            route_id: [message.to_mapping() for message in self.receive(route_id)]
            for route_id in self.route_ids()
        }

    def _route_file(self, route_id: str) -> Path:
        if "/" in route_id or "\\" in route_id or ".." in route_id or not route_id:
            raise ValueError("route_id must be a logical route id, not a path")
        return self.routes_root / route_id / "messages.jsonl"


def write_projection_to_fake_runtime(
    root: Path | str,
    *,
    data_handles: Iterable[DataHandle],
    events: Iterable[EventBusMessage],
    contexts: Iterable[ContextBusMessage],
    routes: Iterable[RouteMessage],
    replace_routes: bool = True,
) -> FakeRuntimeSnapshot:
    """Write a runtime projection to a fake local runtime surface.

    Layout:

    <root>/
      data.index.jsonl
      event.bus.jsonl
      context.bus.jsonl
      routes/<route_id>/messages.jsonl

    This simulates the future local runtime vocabulary without implementing
    shared memory or semaphores.

    By default route files are replaced, not appended, so repeated end-to-end
    smoke runs remain deterministic. Use FakeLocalRouteTransport.send directly
    when append semantics are wanted.
    """

    runtime_root = Path(root)
    runtime_root.mkdir(parents=True, exist_ok=True)

    routes_root = runtime_root / "routes"
    if replace_routes and routes_root.exists():
        shutil.rmtree(routes_root)

    data_handle_items = tuple(data_handles)
    event_items = tuple(events)
    context_items = tuple(contexts)
    route_items = tuple(routes)

    _write_jsonl(runtime_root / "data.index.jsonl", (item.to_mapping() for item in data_handle_items))
    _write_jsonl(runtime_root / "event.bus.jsonl", (item.to_mapping() for item in event_items))
    _write_jsonl(runtime_root / "context.bus.jsonl", (item.to_mapping() for item in context_items))

    transport = FakeLocalRouteTransport(runtime_root)
    for route in route_items:
        transport.send(route)

    route_ids = transport.route_ids()
    return FakeRuntimeSnapshot(
        data_handle_count=len(data_handle_items),
        event_count=len(event_items),
        context_count=len(context_items),
        route_message_count=len(route_items),
        route_ids=route_ids,
    )


def load_fake_bus_messages(path: Path | str) -> tuple[DataHandle | EventBusMessage | ContextBusMessage | RouteMessage, ...]:
    """Load validated runtime messages from a fake JSONL bus/index file."""

    p = Path(path)
    if not p.exists():
        return ()

    messages = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        messages.append(parse_runtime_message(json.loads(line)))
    return tuple(messages)


def _route_message(message: RouteMessage | Mapping[str, Any]) -> RouteMessage:
    if isinstance(message, RouteMessage):
        return message
    parsed = parse_runtime_message(message)
    if not isinstance(parsed, RouteMessage):
        raise TypeError(f"expected RouteMessage, got {type(parsed).__name__}")
    return parsed


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, separators=(",", ":")))
            handle.write("\n")
