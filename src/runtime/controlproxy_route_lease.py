"""ControlProxy route lease state.

This module implements phase 0083.

It adds a file-backed route lease state machine on top of the active route
materializer from 0081.

The lease state is explicit ControlFS state:

    active/routes/<route_id>/lease.json
    active/routes/<route_id>/status.json

Allowed transition path:

    not_leased -> leased -> active -> draining -> closed

The Scheduler can later call these importable functions directly. There is no
daemon, no service and no CLI.

Compatibility rule phrase: There is no daemon, no service and no CLI.

It deliberately does not:
- create a daemon
- start a service
- use OpenRC
- watch ControlFS
- call Scheduler
- decide security policy
- create mmap routes
- write RouteMessage frames
- notify eventfd
- resize live mmap routes
- implement inter-process locks
- implement VisPy

It is lease state only, not the lease authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal, Mapping

from runtime.controlfs_manifest import normalize_route_id
from runtime.controlproxy_active_routes import (
    ACTIVE_ROUTE_STATUS_SCHEMA,
    ActiveRouteMaterializationError,
    active_route_dir,
    active_status_path,
)


ROUTE_LEASE_SCHEMA = "missipy.controlproxy.route_lease.v1"
ROUTE_LEASE_TRANSITION_SCHEMA = "missipy.controlproxy.route_lease_transition.v1"
DEFAULT_LEASED_AT = "2026-07-04T20:00:00Z"

RouteLeaseState = Literal["leased", "active", "draining", "closed"]

_ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "not_leased": ("leased",),
    "leased": ("active", "closed"),
    "active": ("draining",),
    "draining": ("closed",),
    "closed": (),
}


class RouteLeaseError(RuntimeError):
    """Raised when route lease state is invalid."""


class RouteLeaseTransitionError(RouteLeaseError):
    """Raised when a route lease transition is not allowed."""


@dataclass(frozen=True)
class RouteLease:
    """Lease record stored under active/routes/<route_id>/lease.json."""

    schema: str
    lease_id: str
    route_id: str
    route_handle: str
    task_id: str
    holder: str
    scope: str
    state: RouteLeaseState
    acquired_at: str
    ttl_seconds: int
    updated_at: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "RouteLease":
        if raw.get("schema") != ROUTE_LEASE_SCHEMA:
            raise RouteLeaseError("unsupported route lease schema")
        state = _require_id(raw, "state")
        if state not in ("leased", "active", "draining", "closed"):
            raise RouteLeaseError("unsupported route lease state")
        return cls(
            schema=str(raw["schema"]),
            lease_id=_require_id(raw, "lease_id"),
            route_id=normalize_route_id(_require_str(raw, "route_id")),
            route_handle=_require_handle(raw, "route_handle"),
            task_id=_require_id(raw, "task_id"),
            holder=_require_id(raw, "holder"),
            scope=_require_scope(raw, "scope"),
            state=state,  # type: ignore[arg-type]
            acquired_at=_require_timestamp(raw, "acquired_at"),
            ttl_seconds=_require_positive_int(raw, "ttl_seconds"),
            updated_at=_require_timestamp(raw, "updated_at"),
        )

    @classmethod
    def from_path(cls, path: Path | str) -> "RouteLease":
        return cls.from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "lease_id": self.lease_id,
            "route_id": self.route_id,
            "route_handle": self.route_handle,
            "task_id": self.task_id,
            "holder": self.holder,
            "scope": self.scope,
            "state": self.state,
            "acquired_at": self.acquired_at,
            "ttl_seconds": self.ttl_seconds,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class RouteLeaseTransition:
    """Transition fact returned by lease state updates."""

    schema: str
    lease_id: str
    route_id: str
    route_handle: str
    previous_state: str
    next_state: str
    transitioned_at: str
    reason: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "lease_id": self.lease_id,
            "route_id": self.route_id,
            "route_handle": self.route_handle,
            "previous_state": self.previous_state,
            "next_state": self.next_state,
            "transitioned_at": self.transitioned_at,
            "reason": self.reason,
        }


def lease_path(controlfs_root: Path | str, route_id: str) -> Path:
    """Return active/routes/<route_id>/lease.json."""

    return active_route_dir(controlfs_root, route_id) / "lease.json"


def acquire_route_lease(
    *,
    controlfs_root: Path | str,
    route_id: str,
    holder: str,
    scope: str,
    lease_id: str | None = None,
    ttl_seconds: int = 300,
    acquired_at: str = DEFAULT_LEASED_AT,
) -> RouteLease:
    """Move an active route from not_leased to leased.

    This does not grant security by itself. Security remains Scheduler/policy
    responsibility. This function only records the state transition.
    """

    safe_route_id = normalize_route_id(route_id)
    status_path = active_status_path(controlfs_root, safe_route_id)
    status = _load_active_status(status_path)
    current = str(status.get("lease_state", "not_leased"))
    _ensure_transition(current, "leased")

    holder_id = _require_literal_id(holder, "holder")
    scope_id = _require_literal_scope(scope, "scope")
    lease = RouteLease(
        schema=ROUTE_LEASE_SCHEMA,
        lease_id=lease_id or f"lease:{safe_route_id}:g1:{holder_id}",
        route_id=safe_route_id,
        route_handle=_require_status_str(status, "route_handle"),
        task_id=_require_status_str(status, "task_id"),
        holder=holder_id,
        scope=scope_id,
        state="leased",
        acquired_at=_require_literal_timestamp(acquired_at, "acquired_at"),
        ttl_seconds=_require_positive_literal_int(ttl_seconds, "ttl_seconds"),
        updated_at=acquired_at,
    )

    _write_lease(controlfs_root, lease)
    _update_active_status(status_path, status, lease, previous_state=current, next_state="leased", updated_at=acquired_at)
    return lease


def transition_route_lease(
    *,
    controlfs_root: Path | str,
    route_id: str,
    next_state: RouteLeaseState,
    transitioned_at: str = DEFAULT_LEASED_AT,
    reason: str = "state transition requested",
) -> RouteLeaseTransition:
    """Transition an existing route lease."""

    safe_route_id = normalize_route_id(route_id)
    if next_state not in ("leased", "active", "draining", "closed"):
        raise RouteLeaseTransitionError("unsupported next route lease state")

    status_path = active_status_path(controlfs_root, safe_route_id)
    status = _load_active_status(status_path)
    lease = RouteLease.from_path(lease_path(controlfs_root, safe_route_id))

    current = lease.state
    _ensure_transition(current, next_state)

    updated = RouteLease(
        schema=lease.schema,
        lease_id=lease.lease_id,
        route_id=lease.route_id,
        route_handle=lease.route_handle,
        task_id=lease.task_id,
        holder=lease.holder,
        scope=lease.scope,
        state=next_state,
        acquired_at=lease.acquired_at,
        ttl_seconds=lease.ttl_seconds,
        updated_at=transitioned_at,
    )
    _write_lease(controlfs_root, updated)
    _update_active_status(status_path, status, updated, previous_state=current, next_state=next_state, updated_at=transitioned_at)

    return RouteLeaseTransition(
        schema=ROUTE_LEASE_TRANSITION_SCHEMA,
        lease_id=updated.lease_id,
        route_id=updated.route_id,
        route_handle=updated.route_handle,
        previous_state=current,
        next_state=next_state,
        transitioned_at=transitioned_at,
        reason=reason,
    )


def activate_route_lease(*, controlfs_root: Path | str, route_id: str, transitioned_at: str = DEFAULT_LEASED_AT) -> RouteLeaseTransition:
    """Move leased -> active."""

    return transition_route_lease(
        controlfs_root=controlfs_root,
        route_id=route_id,
        next_state="active",
        transitioned_at=transitioned_at,
        reason="route lease activated",
    )


def begin_route_drain(*, controlfs_root: Path | str, route_id: str, transitioned_at: str = DEFAULT_LEASED_AT) -> RouteLeaseTransition:
    """Move active -> draining."""

    return transition_route_lease(
        controlfs_root=controlfs_root,
        route_id=route_id,
        next_state="draining",
        transitioned_at=transitioned_at,
        reason="route drain requested",
    )


def close_route_lease(*, controlfs_root: Path | str, route_id: str, transitioned_at: str = DEFAULT_LEASED_AT) -> RouteLeaseTransition:
    """Move leased/draining -> closed."""

    return transition_route_lease(
        controlfs_root=controlfs_root,
        route_id=route_id,
        next_state="closed",
        transitioned_at=transitioned_at,
        reason="route lease closed",
    )


def load_route_lease(controlfs_root: Path | str, route_id: str) -> RouteLease:
    """Load active/routes/<route_id>/lease.json."""

    return RouteLease.from_path(lease_path(controlfs_root, route_id))


def route_lease_summary(controlfs_root: Path | str, route_id: str) -> dict[str, Any]:
    """Return compact route lease and active status summary."""

    status = _load_active_status(active_status_path(controlfs_root, route_id))
    lease = load_route_lease(controlfs_root, route_id)
    return {
        "route_id": route_id,
        "lease_state": status.get("lease_state"),
        "active_state": status.get("state"),
        "current_lease_id": status.get("current_lease_id"),
        "current_lease_holder": status.get("current_lease_holder"),
        "lease": lease.to_mapping(),
    }


def _write_lease(controlfs_root: Path | str, lease: RouteLease) -> None:
    path = lease_path(controlfs_root, lease.route_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lease.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_active_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ActiveRouteMaterializationError(f"missing active route status: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") != ACTIVE_ROUTE_STATUS_SCHEMA:
        raise ActiveRouteMaterializationError("unsupported active route status schema")
    return raw


def _update_active_status(path: Path, status: dict[str, Any], lease: RouteLease, *, previous_state: str, next_state: str, updated_at: str) -> None:
    status["lease_state"] = next_state
    status["current_lease_id"] = lease.lease_id
    status["current_lease_holder"] = lease.holder
    status["current_lease_scope"] = lease.scope
    status["current_lease_updated_at"] = updated_at
    status["previous_lease_state"] = previous_state
    if next_state == "closed":
        status["state"] = "closed"
    path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ensure_transition(current: str, next_state: str) -> None:
    allowed = _ALLOWED_TRANSITIONS.get(current)
    if allowed is None:
        raise RouteLeaseTransitionError(f"unknown current lease state: {current}")
    if next_state not in allowed:
        raise RouteLeaseTransitionError(f"invalid route lease transition: {current} -> {next_state}")


def _require_status_str(status: Mapping[str, Any], field: str) -> str:
    value = status.get(field)
    if not isinstance(value, str) or not value:
        raise RouteLeaseError(f"active status missing {field}")
    return value


def _require_str(raw: Mapping[str, Any], field: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value:
        raise RouteLeaseError(f"{field} must be a non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise RouteLeaseError(f"{field} must not contain path traversal")
    return value


def _require_id(raw: Mapping[str, Any], field: str) -> str:
    return _require_literal_id(_require_str(raw, field), field)


def _require_scope(raw: Mapping[str, Any], field: str) -> str:
    return _require_literal_scope(_require_str(raw, field), field)


def _require_timestamp(raw: Mapping[str, Any], field: str) -> str:
    return _require_literal_timestamp(_require_str(raw, field), field)


def _require_positive_int(raw: Mapping[str, Any], field: str) -> int:
    return _require_positive_literal_int(raw.get(field), field)


def _require_handle(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if "/" in value or "\\" in value or ".." in value:
        raise RouteLeaseError(f"{field} must not contain path traversal")
    return value


def _require_literal_id(value: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise RouteLeaseError(f"{field} must be a non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise RouteLeaseError(f"{field} must not contain path traversal")
    if not value.replace("_", "").replace(".", "").replace(":", "").replace("-", "").isalnum():
        raise RouteLeaseError(f"{field} contains invalid characters")
    return value


def _require_literal_scope(value: str, field: str) -> str:
    value = _require_literal_id(value, field)
    if "." not in value:
        raise RouteLeaseError(f"{field} should use subsystem.permission form")
    return value


def _require_literal_timestamp(value: str, field: str) -> str:
    if not isinstance(value, str) or "T" not in value or "Z" not in value:
        raise RouteLeaseError(f"{field} must look like a UTC timestamp")
    return value


def _require_positive_literal_int(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise RouteLeaseError(f"{field} must be a positive integer")
    return value
