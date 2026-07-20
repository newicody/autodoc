"""Bind an authorized Scheduler route request to explicit ControlProxy roots.

This module is the concrete one-argument adapter expected by
``runtime.controlproxy_scheduler_handler``.  It does not decide admission or
security policy: ``SchedulerRouteRequest`` has already been authorized by the
canonical Scheduler path.  Its narrow responsibilities are:

* require an explicit ControlFS root;
* prepare the existing explicit ``/dev/shm`` route runtime root;
* persist one idempotent desired-route manifest on the temporary ControlFS
  declarative surface;
* delegate the handshake to ``runtime.scheduler_route_adapter``.

No Scheduler, Dispatcher, PriorityQueue, EventBus, daemon, thread, process,
SQL store, Qdrant client or durable JSON queue is created here.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from runtime.controlfs_manifest import (
    ROUTE_MANIFEST_SCHEMA,
    RouteManifest,
    load_desired_route_manifest,
    route_manifest_path,
)
from runtime.controlproxy_prepare import (
    ROUTE_PREPARE_REQUEST_SCHEMA,
    RoutePrepareRequest,
    decide_route_prepare,
)
from runtime.route_dev_shm_runtime import prepare_dev_shm_route_runtime_root
from runtime.scheduler_route_adapter import (
    SchedulerRouteReply,
    SchedulerRouteRequest,
    handle_scheduler_route_request as _handle_scheduler_route_request,
)
from runtime.shm_runtime_schema import ROUTE_MESSAGE_SCHEMA


CONTROLFS_ROOT_ENV = "AUTODOC_CONTROLFS_ROOT"
_CONTROL_ROUTE_ZONE = "scheduler"
_CONTROL_ROUTE_PRODUCER = "scheduler"
_CONTROL_ROUTE_CONSUMER = "love_laboratory"
_CONTROL_ROUTE_MIN_FRAME_BYTES = 4096


class ControlProxySchedulerAdapterError(RuntimeError):
    """Raised when the explicit Scheduler-to-ControlProxy binding is invalid."""


def handle_scheduler_route_request(request: object) -> SchedulerRouteReply:
    """Handle one already-authorized route request with explicit local roots.

    The function has deliberately one positional argument because it is loaded
    by ``ControlProxySchedulerRouteRequestHandler``.  Root selection is not
    inferred: ControlFS is required through ``AUTODOC_CONTROLFS_ROOT`` and the
    route data plane is prepared by the existing strict ``/dev/shm`` adapter.
    """

    parsed = _parse_authorized_request(request)
    controlfs_root = _explicit_controlfs_root()
    runtime_binding = prepare_dev_shm_route_runtime_root()

    ensure_desired_scheduler_route_manifest(
        controlfs_root=controlfs_root,
        request=parsed,
    )

    return _handle_scheduler_route_request(
        controlfs_root=controlfs_root,
        runtime_root=runtime_binding.runtime_root,
        request=parsed,
        publish_bus=False,
    )


def ensure_desired_scheduler_route_manifest(
    *,
    controlfs_root: Path | str,
    request: SchedulerRouteRequest | Mapping[str, Any],
) -> RouteManifest:
    """Create or verify the desired ControlFS manifest for one route request.

    The write is idempotent and create-only.  An existing incompatible manifest
    is rejected instead of being overwritten.  The JSON document is a temporary
    ControlFS boundary projection, never Scheduler state or durable authority.
    """

    parsed = (
        request
        if isinstance(request, SchedulerRouteRequest)
        else SchedulerRouteRequest.from_mapping(request)
    )
    root = _validated_controlfs_root(controlfs_root)
    expected = _desired_manifest_from_request(parsed)
    path = route_manifest_path(root, parsed.route_id)

    existing = _load_existing_manifest(path, root=root, route_id=parsed.route_id)
    if existing is not None:
        _ensure_same_manifest(existing, expected)
        return existing

    _write_manifest_create_only(path, expected)
    stored = load_desired_route_manifest(root, parsed.route_id)
    _ensure_same_manifest(stored, expected)
    return stored


def _parse_authorized_request(request: object) -> SchedulerRouteRequest:
    if isinstance(request, SchedulerRouteRequest):
        return request
    if not isinstance(request, Mapping):
        raise ControlProxySchedulerAdapterError(
            "Scheduler route request must be a mapping or SchedulerRouteRequest"
        )
    try:
        return SchedulerRouteRequest.from_mapping(request)
    except (TypeError, ValueError, RuntimeError) as exc:
        raise ControlProxySchedulerAdapterError(str(exc)) from exc


def _explicit_controlfs_root() -> Path:
    raw = os.environ.get(CONTROLFS_ROOT_ENV, "").strip()
    if not raw:
        raise ControlProxySchedulerAdapterError(
            f"{CONTROLFS_ROOT_ENV} must name an explicit ControlFS root"
        )
    path = Path(raw)
    if not path.is_absolute():
        raise ControlProxySchedulerAdapterError(
            f"{CONTROLFS_ROOT_ENV} must be an absolute path"
        )
    return _validated_controlfs_root(path)


def _validated_controlfs_root(value: Path | str) -> Path:
    root = Path(value)
    if not root.is_absolute():
        raise ControlProxySchedulerAdapterError(
            "ControlFS root must be an absolute path"
        )
    if root.is_symlink():
        raise ControlProxySchedulerAdapterError(
            "ControlFS root must not be a symlink"
        )
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ControlProxySchedulerAdapterError(
            "ControlFS root must be a real directory"
        )
    return root


def _desired_manifest_from_request(request: SchedulerRouteRequest) -> RouteManifest:
    canonical_request = json.dumps(
        request.to_mapping(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    required_frame_bytes = max(
        _CONTROL_ROUTE_MIN_FRAME_BYTES,
        len(canonical_request) + 1024,
    )
    prepare_request = RoutePrepareRequest.from_mapping(
        {
            "schema": ROUTE_PREPARE_REQUEST_SCHEMA,
            "request_id": f"prep:{request.request_id}",
            "route_id": request.route_id,
            "task_id": request.task_id,
            "zone": _CONTROL_ROUTE_ZONE,
            "scope": request.scope,
            "producer": _CONTROL_ROUTE_PRODUCER,
            "consumer": _CONTROL_ROUTE_CONSUMER,
            "required_frame_bytes": required_frame_bytes,
            "message_schema": ROUTE_MESSAGE_SCHEMA,
            "payload_kind": "scheduler_route_refs",
            "ttl_seconds": request.ttl_seconds,
            "requested_by": "scheduler",
            "requested_at": request.requested_at,
        }
    )
    decision = decide_route_prepare(
        prepare_request,
        decided_at=request.requested_at,
    )
    if decision.status != "ready":
        raise ControlProxySchedulerAdapterError(
            "ControlProxy sizing denied the Scheduler route: " + decision.reason
        )
    required_values = {
        "slot_size": decision.slot_size,
        "slot_count": decision.slot_count,
        "max_frame_bytes": decision.max_frame_bytes,
        "notify": decision.notify,
        "overflow_policy": decision.overflow_policy,
    }
    missing = sorted(name for name, value in required_values.items() if value is None)
    if missing:
        raise ControlProxySchedulerAdapterError(
            "ControlProxy sizing result is incomplete: " + ", ".join(missing)
        )

    return RouteManifest.from_mapping(
        {
            "schema": ROUTE_MANIFEST_SCHEMA,
            "route_id": request.route_id,
            "task_id": request.task_id,
            "zone": _CONTROL_ROUTE_ZONE,
            "scope": request.scope,
            "producer": _CONTROL_ROUTE_PRODUCER,
            "consumer": _CONTROL_ROUTE_CONSUMER,
            "ttl_seconds": request.ttl_seconds,
            "mode": "rw",
            "message_schema": ROUTE_MESSAGE_SCHEMA,
            "created_by": "scheduler",
            "created_at": request.requested_at,
            "transport": "mmap.fixed_slot",
            "slot_size": decision.slot_size,
            "slot_count": decision.slot_count,
            "max_frame_bytes": decision.max_frame_bytes,
            "overflow_policy": decision.overflow_policy,
            "notify": decision.notify,
            "sizing_source": "scheduler.route_request.refs_only",
            "observed_frame_bytes": required_frame_bytes,
        }
    )


def _load_existing_manifest(
    path: Path,
    *,
    root: Path,
    route_id: str,
) -> RouteManifest | None:
    route_dir = path.parent
    if route_dir.is_symlink():
        raise ControlProxySchedulerAdapterError(
            "ControlFS desired route directory must not be a symlink"
        )
    if not path.exists():
        return None
    if path.is_symlink():
        raise ControlProxySchedulerAdapterError(
            "ControlFS desired manifest must not be a symlink"
        )
    try:
        return load_desired_route_manifest(root, route_id)
    except (OSError, TypeError, ValueError) as exc:
        raise ControlProxySchedulerAdapterError(
            f"existing ControlFS desired manifest is invalid: {exc}"
        ) from exc


def _ensure_same_manifest(actual: RouteManifest, expected: RouteManifest) -> None:
    if actual != expected:
        raise ControlProxySchedulerAdapterError(
            "existing ControlFS desired manifest conflicts with authorized request"
        )


def _write_manifest_create_only(path: Path, manifest: RouteManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ControlProxySchedulerAdapterError(
            "ControlFS desired route directory must not be a symlink"
        )
    payload = json.dumps(
        manifest.to_mapping(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".manifest.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            return
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


__all__ = (
    "CONTROLFS_ROOT_ENV",
    "ControlProxySchedulerAdapterError",
    "ensure_desired_scheduler_route_manifest",
    "handle_scheduler_route_request",
)
