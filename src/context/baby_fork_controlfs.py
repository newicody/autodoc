"""Baby-fork ControlProxy desired route manifests.

This module implements 0079-r2 for the baby-fork smoke path.

Architecture vocabulary:

    ControlProxy = ControlFS declarative surface + RouteProxy materializer.

It deliberately does not:
- create shared memory
- create semaphores
- implement mmap
- resize a live mmap ring
- start Scheduler
- decide security
- write active/routes
- mutate revoked/routes
- implement NetworkBridge or HardwareBridge

It writes desired route manifests for known baby-fork routes and can run the
existing dry-run reconciler against that ControlFS root.

0079-r2 adds sizing hints measured from encoded RouteMessage frames.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any, Mapping, Sequence

from context.baby_fork_runtime_projection import (
    BABY_FORK_CONTEXT_GATE_ROUTE,
    BABY_FORK_CONTEXT_ID,
    BABY_FORK_RETRIEVAL_ROUTE,
    BABY_FORK_VARIANT_ROUTE,
)
from runtime.controlfs_manifest import ROUTE_MANIFEST_SCHEMA, RouteManifest, route_manifest_path
from runtime.route_frame_codec import encode_route_message_frame
from runtime.routeproxy_reconciler import RouteProxyPlan, build_routeproxy_plan
from runtime.shm_runtime_schema import RouteMessage


BABY_FORK_CONTROLFS_CREATED_AT = "2026-07-04T20:00:00Z"
BABY_FORK_ROUTE_MESSAGE_SCHEMA = "missipy.shm.route_message.v1"
DEFAULT_SLOT_CLASSES = (512, 1024, 2048, 4096, 8192, 16384, 32768)


@dataclass(frozen=True)
class RouteSizingHint:
    """Per-route sizing hint written to ControlProxy/ControlFS desired manifest."""

    route_id: str
    observed_frame_bytes: int
    slot_size: int
    slot_count: int = 16
    max_frame_bytes: int | None = None
    transport: str = "mmap.fixed_slot"
    overflow_policy: str = "reject"
    notify: str = "semaphore"
    sizing_source: str = "controlproxy.prepare"

    def normalized_max_frame_bytes(self) -> int:
        return self.max_frame_bytes if self.max_frame_bytes is not None else self.slot_size


@dataclass(frozen=True)
class BabyForkRouteSpec:
    """Static desired-route spec for the baby-fork smoke project."""

    route_id: str
    task_id: str
    zone: str
    scope: str
    producer: str
    consumer: str
    ttl_seconds: int
    mode: str
    message_schema: str = BABY_FORK_ROUTE_MESSAGE_SCHEMA
    created_by: str = "scheduler"
    created_at: str = BABY_FORK_CONTROLFS_CREATED_AT
    transport: str | None = "mmap.fixed_slot"
    slot_size: int | None = 2048
    slot_count: int | None = 16
    max_frame_bytes: int | None = 2048
    overflow_policy: str | None = "reject"
    notify: str | None = "semaphore"
    sizing_source: str | None = "static.default"
    observed_frame_bytes: int | None = None

    def with_sizing(self, hint: RouteSizingHint | None) -> "BabyForkRouteSpec":
        if hint is None:
            return self
        return BabyForkRouteSpec(
            route_id=self.route_id,
            task_id=self.task_id,
            zone=self.zone,
            scope=self.scope,
            producer=self.producer,
            consumer=self.consumer,
            ttl_seconds=self.ttl_seconds,
            mode=self.mode,
            message_schema=self.message_schema,
            created_by=self.created_by,
            created_at=self.created_at,
            transport=hint.transport,
            slot_size=hint.slot_size,
            slot_count=hint.slot_count,
            max_frame_bytes=hint.normalized_max_frame_bytes(),
            overflow_policy=hint.overflow_policy,
            notify=hint.notify,
            sizing_source=hint.sizing_source,
            observed_frame_bytes=hint.observed_frame_bytes,
        )

    def to_manifest(self) -> RouteManifest:
        raw: dict[str, Any] = {
            "schema": ROUTE_MANIFEST_SCHEMA,
            "route_id": self.route_id,
            "task_id": self.task_id,
            "zone": self.zone,
            "scope": self.scope,
            "producer": self.producer,
            "consumer": self.consumer,
            "ttl_seconds": self.ttl_seconds,
            "mode": self.mode,
            "message_schema": self.message_schema,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }
        for key, value in {
            "transport": self.transport,
            "slot_size": self.slot_size,
            "slot_count": self.slot_count,
            "max_frame_bytes": self.max_frame_bytes,
            "overflow_policy": self.overflow_policy,
            "notify": self.notify,
            "sizing_source": self.sizing_source,
            "observed_frame_bytes": self.observed_frame_bytes,
        }.items():
            if value is not None:
                raw[key] = value
        return RouteManifest.from_mapping(raw)


def baby_fork_route_specs(
    context_id: str = BABY_FORK_CONTEXT_ID,
    *,
    sizing_hints: Mapping[str, RouteSizingHint] | None = None,
) -> tuple[BabyForkRouteSpec, ...]:
    """Return the locked desired routes for the baby-fork smoke project."""

    hints = sizing_hints or {}
    specs = (
        BabyForkRouteSpec(
            route_id=BABY_FORK_RETRIEVAL_ROUTE,
            task_id=context_id,
            zone="workers",
            scope="context.read",
            producer="scheduler",
            consumer="retrieval_worker",
            ttl_seconds=300,
            mode="rw",
        ),
        BabyForkRouteSpec(
            route_id=BABY_FORK_VARIANT_ROUTE,
            task_id=context_id,
            zone="workers",
            scope="context.read",
            producer="scheduler",
            consumer="variant_generator_stub",
            ttl_seconds=300,
            mode="rw",
        ),
        BabyForkRouteSpec(
            route_id=BABY_FORK_CONTEXT_GATE_ROUTE,
            task_id=context_id,
            zone="context",
            scope="context.patch",
            producer="context_gate",
            consumer="scheduler",
            ttl_seconds=300,
            mode="rw",
        ),
    )
    return tuple(spec.with_sizing(hints.get(spec.route_id)) for spec in specs)


def choose_slot_size(
    observed_frame_bytes: int,
    *,
    headroom_bytes: int = 256,
    slot_classes: Sequence[int] = DEFAULT_SLOT_CLASSES,
) -> int:
    """Pick the smallest configured slot class that can hold the observed frame."""

    if not isinstance(observed_frame_bytes, int) or isinstance(observed_frame_bytes, bool) or observed_frame_bytes < 1:
        raise ValueError("observed_frame_bytes must be a positive integer")
    if headroom_bytes < 0:
        raise ValueError("headroom_bytes must be non-negative")

    required = observed_frame_bytes + headroom_bytes
    for slot_size in slot_classes:
        if required <= slot_size:
            return slot_size
    return max(required, slot_classes[-1])


def build_route_sizing_hints_from_messages(
    routes: Sequence[RouteMessage],
    *,
    slot_count: int = 16,
    headroom_bytes: int = 256,
    slot_classes: Sequence[int] = DEFAULT_SLOT_CLASSES,
) -> dict[str, RouteSizingHint]:
    """Measure RouteMessage frame sizes and return ControlProxy sizing hints."""

    observed: dict[str, int] = {}
    for message in routes:
        frame_size = len(encode_route_message_frame(message))
        observed[message.route_id] = max(observed.get(message.route_id, 0), frame_size)

    return {
        route_id: RouteSizingHint(
            route_id=route_id,
            observed_frame_bytes=frame_size,
            slot_size=choose_slot_size(
                frame_size,
                headroom_bytes=headroom_bytes,
                slot_classes=slot_classes,
            ),
            slot_count=slot_count,
        )
        for route_id, frame_size in observed.items()
    }


def write_baby_fork_desired_manifests(
    controlfs_root: Path | str,
    *,
    context_id: str = BABY_FORK_CONTEXT_ID,
    sizing_hints: Mapping[str, RouteSizingHint] | None = None,
) -> tuple[Path, ...]:
    """Write baby-fork desired route manifests under ControlProxy/ControlFS."""

    root = Path(controlfs_root)
    written: list[Path] = []

    for spec in baby_fork_route_specs(context_id=context_id, sizing_hints=sizing_hints):
        manifest = spec.to_manifest()
        path = route_manifest_path(root, manifest.route_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(manifest.to_mapping(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(path)

    return tuple(written)


def build_baby_fork_routeproxy_plan(
    controlfs_root: Path | str,
    *,
    context_id: str = BABY_FORK_CONTEXT_ID,
    include_noop: bool = False,
    write_desired: bool = True,
    sizing_hints: Mapping[str, RouteSizingHint] | None = None,
) -> RouteProxyPlan:
    """Build a dry-run ControlProxy/RouteProxy plan for baby-fork routes."""

    if write_desired:
        write_baby_fork_desired_manifests(
            controlfs_root,
            context_id=context_id,
            sizing_hints=sizing_hints,
        )
    return build_routeproxy_plan(controlfs_root, include_noop=include_noop)


def baby_fork_controlfs_summary(controlfs_root: Path | str, plan: RouteProxyPlan) -> dict[str, Any]:
    """Return a JSON-serializable summary for CLI tools."""

    return {
        "controlfs_root": str(Path(controlfs_root)),
        "desired_routes": [spec.route_id for spec in baby_fork_route_specs()],
        "plan": plan.to_mapping(),
        "action_counts": {
            "create": len(plan.by_action("create")),
            "delete": len(plan.by_action("delete")),
            "update": len(plan.by_action("update")),
            "noop": len(plan.by_action("noop")),
            "error": len(plan.by_action("error")),
        },
    }
