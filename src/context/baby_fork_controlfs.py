"""Baby-fork ControlFS desired route manifests.

This module implements phases 0071 and 0072 for the baby-fork smoke path.

It deliberately does not:
- create shared memory
- create semaphores
- start RouteProxy
- start Scheduler
- decide security
- write active/routes
- mutate revoked/routes
- implement NetworkBridge or HardwareBridge

It only writes desired route manifests for the known baby-fork routes and can
run the existing RouteProxy dry-run reconciler against that ControlFS root.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any, Iterable

from context.baby_fork_runtime_projection import (
    BABY_FORK_CONTEXT_GATE_ROUTE,
    BABY_FORK_CONTEXT_ID,
    BABY_FORK_RETRIEVAL_ROUTE,
    BABY_FORK_VARIANT_ROUTE,
)
from runtime.controlfs_manifest import ROUTE_MANIFEST_SCHEMA, RouteManifest, route_manifest_path
from runtime.routeproxy_reconciler import RouteProxyPlan, build_routeproxy_plan


BABY_FORK_CONTROLFS_CREATED_AT = "2026-07-04T20:00:00Z"
BABY_FORK_ROUTE_MESSAGE_SCHEMA = "missipy.shm.route_message.v1"


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

    def to_manifest(self) -> RouteManifest:
        return RouteManifest.from_mapping(
            {
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
        )


def baby_fork_route_specs(context_id: str = BABY_FORK_CONTEXT_ID) -> tuple[BabyForkRouteSpec, ...]:
    """Return the locked desired routes for the baby-fork smoke project."""

    return (
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


def write_baby_fork_desired_manifests(
    controlfs_root: Path | str,
    *,
    context_id: str = BABY_FORK_CONTEXT_ID,
) -> tuple[Path, ...]:
    """Write baby-fork desired route manifests under ControlFS.

    Files written:

    desired/routes/baby_fork.retrieval/manifest.json
    desired/routes/baby_fork.variant_stub/manifest.json
    desired/routes/baby_fork.context_gate/manifest.json
    """

    root = Path(controlfs_root)
    written: list[Path] = []

    for spec in baby_fork_route_specs(context_id=context_id):
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
) -> RouteProxyPlan:
    """Build a RouteProxy dry-run plan for baby-fork routes.

    By default this writes desired route manifests first, then runs the
    existing dry-run reconciler. It does not write active routes.
    """

    if write_desired:
        write_baby_fork_desired_manifests(controlfs_root, context_id=context_id)
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
