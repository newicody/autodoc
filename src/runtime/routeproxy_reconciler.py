"""RouteProxy dry-run reconciler.

This module implements the P2 dry-run phase of the ControlFS architecture.

It deliberately does not:
- create shared memory
- create semaphores
- watch with inotify
- run as a daemon
- call Scheduler
- decide security
- mutate ControlFS

It only compares desired/routes and active/routes and returns a plan that a
future passive RouteProxy can execute.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

from runtime.controlfs_manifest import ManifestValidationError, RouteManifest, normalize_route_id


RoutePlanAction = Literal["create", "delete", "update", "noop", "error"]


@dataclass(frozen=True)
class RoutePlanItem:
    """One dry-run action for a route."""

    action: RoutePlanAction
    route_id: str
    reason: str
    desired: RouteManifest | None = None
    active: RouteManifest | None = None
    error: str | None = None

    def to_mapping(self) -> dict:
        """Return a JSON-serializable representation."""

        payload = {
            "action": self.action,
            "route_id": self.route_id,
            "reason": self.reason,
        }
        if self.desired is not None:
            payload["desired"] = self.desired.to_mapping()
        if self.active is not None:
            payload["active"] = self.active.to_mapping()
        if self.error is not None:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True)
class RouteProxyPlan:
    """Dry-run reconciliation plan for ControlFS routes."""

    controlfs_root: str
    items: tuple[RoutePlanItem, ...]

    def by_action(self, action: RoutePlanAction) -> tuple[RoutePlanItem, ...]:
        """Return plan items matching an action."""

        return tuple(item for item in self.items if item.action == action)

    def has_errors(self) -> bool:
        """Return True when the plan contains invalid route state."""

        return any(item.action == "error" for item in self.items)

    def to_mapping(self) -> dict:
        """Return a JSON-serializable representation."""

        return {
            "controlfs_root": self.controlfs_root,
            "items": [item.to_mapping() for item in self.items],
        }


def build_routeproxy_plan(controlfs_root: Path | str, include_noop: bool = False) -> RouteProxyPlan:
    """Build a dry-run RouteProxy reconciliation plan.

    Directory contract:

    desired route manifest:
      <root>/desired/routes/<route_id>/manifest.json

    active route manifest:
      <root>/active/routes/<route_id>/manifest.json

    Actions:

    - create: desired route exists but active route does not.
    - delete: active route exists but desired route does not.
    - update: both exist but normalized manifests differ.
    - noop: both exist and match, only returned when include_noop=True.
    - error: manifest is invalid or route directory name is unsafe.
    """

    root = Path(controlfs_root)
    desired_root = root / "desired" / "routes"
    active_root = root / "active" / "routes"

    desired_ids = _safe_route_ids(desired_root)
    active_ids = _safe_route_ids(active_root)
    route_ids = sorted(set(desired_ids.valid) | set(active_ids.valid) | set(desired_ids.invalid) | set(active_ids.invalid))

    items: list[RoutePlanItem] = []

    for route_id in route_ids:
        if route_id in desired_ids.invalid:
            items.append(
                RoutePlanItem(
                    action="error",
                    route_id=route_id,
                    reason="invalid desired route directory name",
                    error=desired_ids.invalid[route_id],
                )
            )
            continue

        if route_id in active_ids.invalid:
            items.append(
                RoutePlanItem(
                    action="error",
                    route_id=route_id,
                    reason="invalid active route directory name",
                    error=active_ids.invalid[route_id],
                )
            )
            continue

        desired = _load_optional_manifest(desired_root, route_id, "desired")
        active = _load_optional_manifest(active_root, route_id, "active")

        if isinstance(desired, RoutePlanItem):
            items.append(desired)
            continue
        if isinstance(active, RoutePlanItem):
            items.append(active)
            continue

        if desired is not None and active is None:
            items.append(
                RoutePlanItem(
                    action="create",
                    route_id=route_id,
                    reason="desired route is missing from active routes",
                    desired=desired,
                )
            )
            continue

        if desired is None and active is not None:
            items.append(
                RoutePlanItem(
                    action="delete",
                    route_id=route_id,
                    reason="active route is no longer desired",
                    active=active,
                )
            )
            continue

        if desired is not None and active is not None:
            if desired.to_mapping() != active.to_mapping():
                items.append(
                    RoutePlanItem(
                        action="update",
                        route_id=route_id,
                        reason="desired and active manifests differ",
                        desired=desired,
                        active=active,
                    )
                )
            elif include_noop:
                items.append(
                    RoutePlanItem(
                        action="noop",
                        route_id=route_id,
                        reason="desired and active manifests already match",
                        desired=desired,
                        active=active,
                    )
                )

    return RouteProxyPlan(controlfs_root=str(root), items=tuple(items))


@dataclass(frozen=True)
class _RouteIdScan:
    valid: frozenset[str]
    invalid: dict[str, str]


def _safe_route_ids(routes_root: Path) -> _RouteIdScan:
    if not routes_root.exists():
        return _RouteIdScan(valid=frozenset(), invalid={})

    valid: set[str] = set()
    invalid: dict[str, str] = {}

    for child in sorted(routes_root.iterdir()):
        if not child.is_dir():
            continue
        route_id = child.name
        try:
            normalize_route_id(route_id)
        except ManifestValidationError as exc:
            invalid[route_id] = str(exc)
            continue
        valid.add(route_id)

    return _RouteIdScan(valid=frozenset(valid), invalid=invalid)


def _load_optional_manifest(
    routes_root: Path,
    route_id: str,
    side: Literal["desired", "active"],
) -> RouteManifest | RoutePlanItem | None:
    manifest_path = routes_root / route_id / "manifest.json"
    if not manifest_path.exists():
        return None

    try:
        manifest = RouteManifest.from_path(manifest_path)
    except (ManifestValidationError, OSError) as exc:
        return RoutePlanItem(
            action="error",
            route_id=route_id,
            reason=f"invalid {side} route manifest",
            error=str(exc),
        )

    if manifest.route_id != route_id:
        return RoutePlanItem(
            action="error",
            route_id=route_id,
            reason=f"{side} route manifest route_id does not match directory name",
            error=f"manifest route_id={manifest.route_id!r}, directory={route_id!r}",
        )

    return manifest


def summarize_plan(plan: RouteProxyPlan) -> dict[str, int]:
    """Return action counts for a plan."""

    counts = {"create": 0, "delete": 0, "update": 0, "noop": 0, "error": 0}
    for item in plan.items:
        counts[item.action] += 1
    return counts
