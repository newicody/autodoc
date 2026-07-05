"""Explicit /dev/shm runtime root for route data plane segments.

Phase 0111 reinforces real inter-process data plane placement without changing
Scheduler, PolicyEngine, PriorityQueue, Dispatcher or Handler.  It is a narrow
adapter that prepares an explicit /dev/shm runtime root and can build a
RouteRuntimeManager from that root.

Operational intent locked by this module:
- explicit /dev/shm runtime root, never implicit discovery by ControlProxy code.
- no implicit file fallback when /dev/shm placement is requested.
- real inter-process data plane preparation, not a new bus.
- Route mmap/eventfd is data plane, not EventBus.
- EventBus remains observation only.
- No ControlProxyBus.
- No RouteBus.
- No VisualizationBus.
- builds RouteRuntimeManager with explicit roots.
- does not modify Scheduler.run().
- PolicyEngine remains minimal admission before queue.
- PriorityQueue remains deterministic execution order.
- Dispatcher remains EventType -> Handler only.
- stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from runtime.route_runtime_manager import RouteRuntimeManager

ROUTE_DEV_SHM_RUNTIME_ROOT_SCHEMA = "missipy.controlproxy.route_dev_shm_runtime_root.v1"


class RouteDevShmRuntimeError(ValueError):
    """Raised when an explicit /dev/shm runtime root is unsafe or unavailable."""


@dataclass(frozen=True, slots=True)
class RouteDevShmRuntimePolicy:
    """Explicit policy for preparing the /dev/shm route runtime root.

    The policy is intentionally separate from Scheduler priorities and admission.
    It only validates where mmap/eventfd route data plane files may be placed.
    """

    dev_shm_root: Path | str = Path("/dev/shm")
    namespace: str = "autodoc"
    create: bool = True
    require_tmpfs: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "dev_shm_root", Path(self.dev_shm_root))
        _validate_namespace(self.namespace)
        if not isinstance(self.create, bool):
            raise RouteDevShmRuntimeError("create must be a bool")
        if not isinstance(self.require_tmpfs, bool):
            raise RouteDevShmRuntimeError("require_tmpfs must be a bool")


@dataclass(frozen=True, slots=True)
class RouteDevShmRuntimeRoot:
    """Stable projection for the prepared /dev/shm route runtime root."""

    schema: str
    dev_shm_root: str
    namespace: str
    runtime_root: str
    tmpfs_required: bool
    tmpfs_verified: bool
    created: bool

    def __post_init__(self) -> None:
        if self.schema != ROUTE_DEV_SHM_RUNTIME_ROOT_SCHEMA:
            raise RouteDevShmRuntimeError("unsupported dev_shm runtime root schema")
        if not self.dev_shm_root:
            raise RouteDevShmRuntimeError("dev_shm_root is required")
        _validate_namespace(self.namespace)
        if not self.runtime_root:
            raise RouteDevShmRuntimeError("runtime_root is required")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "dev_shm_root": self.dev_shm_root,
            "namespace": self.namespace,
            "runtime_root": self.runtime_root,
            "tmpfs_required": self.tmpfs_required,
            "tmpfs_verified": self.tmpfs_verified,
            "created": self.created,
        }


@dataclass(frozen=True, slots=True)
class RouteDevShmRuntimeManagerBinding:
    """RouteRuntimeManager plus the explicit /dev/shm root used to build it."""

    root: RouteDevShmRuntimeRoot
    manager: RouteRuntimeManager

    def to_mapping(self) -> dict[str, Any]:
        return {
            "root": self.root.to_mapping(),
            "manager": {
                "controlfs_root": str(self.manager.controlfs_root),
                "runtime_root": str(self.manager.runtime_root),
            },
        }


def prepare_dev_shm_route_runtime_root(
    policy: RouteDevShmRuntimePolicy | None = None,
) -> RouteDevShmRuntimeRoot:
    """Validate and prepare the explicit /dev/shm route runtime root.

    This function never falls back to file placement.  If the requested root is
    missing, unsafe, not a directory, symlinked, or not tmpfs when tmpfs is
    required, it raises RouteDevShmRuntimeError.
    """

    policy = policy or RouteDevShmRuntimePolicy()
    root = Path(policy.dev_shm_root)
    if not root.exists():
        raise RouteDevShmRuntimeError("/dev/shm runtime root does not exist")
    if not root.is_dir():
        raise RouteDevShmRuntimeError("/dev/shm runtime root must be a directory")
    _reject_symlink(root, label="dev_shm_root")

    tmpfs_verified = _path_is_tmpfs(root) if policy.require_tmpfs else False
    if policy.require_tmpfs and not tmpfs_verified:
        raise RouteDevShmRuntimeError("/dev/shm runtime root must be backed by tmpfs")

    namespace_root = root / policy.namespace
    runtime_root = namespace_root / "routes-runtime"
    _ensure_relative_to_root(root=root, child=runtime_root)
    _reject_existing_symlink(namespace_root, label="namespace root")
    _reject_existing_symlink(runtime_root, label="routes runtime root")

    existed_before = runtime_root.exists()
    if policy.create:
        runtime_root.mkdir(parents=True, exist_ok=True)
    elif not existed_before:
        raise RouteDevShmRuntimeError("routes runtime root does not exist and create is false")

    _reject_existing_symlink(namespace_root, label="namespace root")
    _reject_existing_symlink(runtime_root, label="routes runtime root")
    if not runtime_root.is_dir():
        raise RouteDevShmRuntimeError("routes runtime root must be a directory")

    return RouteDevShmRuntimeRoot(
        schema=ROUTE_DEV_SHM_RUNTIME_ROOT_SCHEMA,
        dev_shm_root=str(root),
        namespace=policy.namespace,
        runtime_root=str(runtime_root),
        tmpfs_required=policy.require_tmpfs,
        tmpfs_verified=tmpfs_verified,
        created=not existed_before,
    )


def build_dev_shm_route_runtime_manager(
    *,
    controlfs_root: Path | str,
    policy: RouteDevShmRuntimePolicy | None = None,
    blocking_lock: bool = True,
) -> RouteDevShmRuntimeManagerBinding:
    """Build RouteRuntimeManager from an explicit prepared /dev/shm root."""

    root = prepare_dev_shm_route_runtime_root(policy)
    manager = RouteRuntimeManager.from_roots(
        controlfs_root=controlfs_root,
        runtime_root=root.runtime_root,
        blocking_lock=blocking_lock,
    )
    return RouteDevShmRuntimeManagerBinding(root=root, manager=manager)


def route_dev_shm_runtime_root_from_mapping(raw: Mapping[str, Any]) -> RouteDevShmRuntimeRoot:
    """Load a stable mapping emitted by RouteDevShmRuntimeRoot.to_mapping()."""

    schema = _require_str(raw, "schema")
    if schema != ROUTE_DEV_SHM_RUNTIME_ROOT_SCHEMA:
        raise RouteDevShmRuntimeError("unsupported dev_shm runtime root schema")
    return RouteDevShmRuntimeRoot(
        schema=schema,
        dev_shm_root=_require_str(raw, "dev_shm_root"),
        namespace=_require_str(raw, "namespace"),
        runtime_root=_require_str(raw, "runtime_root"),
        tmpfs_required=_require_bool(raw, "tmpfs_required"),
        tmpfs_verified=_require_bool(raw, "tmpfs_verified"),
        created=_require_bool(raw, "created"),
    )


def _validate_namespace(namespace: str) -> str:
    if not isinstance(namespace, str) or not namespace:
        raise RouteDevShmRuntimeError("namespace is required")
    if namespace in {".", ".."}:
        raise RouteDevShmRuntimeError("namespace must not be a traversal marker")
    if "/" in namespace or "\\" in namespace:
        raise RouteDevShmRuntimeError("namespace must be one path segment")
    return namespace


def _ensure_relative_to_root(*, root: Path, child: Path) -> None:
    try:
        child.resolve(strict=False).relative_to(root.resolve(strict=True))
    except ValueError as exc:
        raise RouteDevShmRuntimeError("namespace root must remain under dev_shm_root") from exc


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise RouteDevShmRuntimeError(f"{label} must not be a symlink")


def _reject_existing_symlink(path: Path, *, label: str) -> None:
    if path.exists() or path.is_symlink():
        _reject_symlink(path, label=label)


def _path_is_tmpfs(path: Path) -> bool:
    """Return True when path is under a tmpfs mount according to /proc/mounts."""

    mounts = _read_linux_mounts()
    if not mounts:
        return False
    try:
        target = path.resolve(strict=True)
    except (FileNotFoundError, PermissionError, OSError):
        return False

    best_match: tuple[int, str] | None = None
    for mount_point, fs_type in mounts:
        try:
            mount_path = Path(mount_point).resolve(strict=True)
        except (FileNotFoundError, PermissionError, OSError):
            continue
        try:
            target.relative_to(mount_path)
        except ValueError:
            continue
        depth = len(mount_path.parts)
        if best_match is None or depth > best_match[0]:
            best_match = (depth, fs_type)
    return best_match is not None and best_match[1] == "tmpfs"


def _read_linux_mounts() -> tuple[tuple[str, str], ...]:
    mounts_path = Path("/proc/mounts")
    if not mounts_path.exists():
        return ()
    records: list[tuple[str, str]] = []
    for line in mounts_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 3:
            records.append((parts[1], parts[2]))
    return tuple(records)


def _require_str(raw: Mapping[str, Any], field: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value:
        raise RouteDevShmRuntimeError(f"{field} must be a non-empty string")
    return value


def _require_bool(raw: Mapping[str, Any], field: str) -> bool:
    value = raw.get(field)
    if not isinstance(value, bool):
        raise RouteDevShmRuntimeError(f"{field} must be a bool")
    return value


__all__ = (
    "ROUTE_DEV_SHM_RUNTIME_ROOT_SCHEMA",
    "RouteDevShmRuntimeError",
    "RouteDevShmRuntimeManagerBinding",
    "RouteDevShmRuntimePolicy",
    "RouteDevShmRuntimeRoot",
    "build_dev_shm_route_runtime_manager",
    "prepare_dev_shm_route_runtime_root",
    "route_dev_shm_runtime_root_from_mapping",
)
