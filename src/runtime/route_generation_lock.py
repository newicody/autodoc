"""Inter-process lock for the ControlProxy route generation table.

This module implements phase 0094. It adds a small importable fcntl.flock
primitive around the ControlProxy generation table so that two local
ControlProxy actors cannot allocate the same g2/g3 route generation at the same
time.

Operational intent:
- protect active/routes/<route_id>/generation_state.json updates;
- keep route_id -> current_generation allocation deterministic;
- increment only when a new route generation is materialized by the caller;
- keep /dev/shm placement separate from the lock contract.

Boundaries deliberately kept out of this module:
- No CLI.
- No OpenRC service and no resident daemon.
- No watcher or inotify loop.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher or Component tick contract modification.
- No live mmap resize.
- No route generation allocation by the lock itself.
- ControlProxy does not decide security.
- Scheduler/policy/zone remain the authority.
- standard library only.

The lock is an IO boundary for local ControlFS coordination. It does not command
components and it does not publish policy decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
import errno
import os
from pathlib import Path
from types import TracebackType
from typing import Any, Literal, Self

try:  # POSIX-only, intentionally isolated in this runtime adapter.
    import fcntl
except ImportError:  # pragma: no cover - exercised only on non-POSIX hosts.
    fcntl = None  # type: ignore[assignment]

from runtime.controlfs_manifest import normalize_route_id

ROUTE_GENERATION_LOCK_SCHEMA = "missipy.controlproxy.route_generation_lock.v1"
LockState = Literal["locked", "released"]


class RouteGenerationLockError(RuntimeError):
    """Raised when a route generation lock cannot be used safely."""


class RouteGenerationLockUnavailable(RouteGenerationLockError):
    """Raised when a non-blocking route generation lock is already held."""


@dataclass(frozen=True, slots=True)
class RouteGenerationLockInfo:
    """Serializable description of one route generation lock state."""

    schema: str
    route_id: str
    lock_path: str
    state: LockState
    blocking: bool

    def to_mapping(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready projection."""

        return {
            "blocking": self.blocking,
            "lock_path": self.lock_path,
            "route_id": self.route_id,
            "schema": self.schema,
            "state": self.state,
        }


class RouteGenerationFileLock:
    """Context manager for one route generation table inter-process lock.

    The context manager owns only the lock file descriptor. It does not read or
    write the generation table and it does not allocate a new generation. Callers
    should keep the critical section small: load table, validate next_generation,
    materialize the generation, then persist the table.
    """

    def __init__(
        self,
        *,
        controlfs_root: Path | str,
        route_id: str,
        blocking: bool = True,
    ) -> None:
        self.route_id = normalize_route_id(route_id)
        self.lock_path = route_generation_lock_path(controlfs_root, self.route_id)
        self.blocking = bool(blocking)
        self._fd: int | None = None

    def acquire(self) -> RouteGenerationLockInfo:
        """Acquire the route generation lock and return its locked projection."""

        if fcntl is None:
            raise RouteGenerationLockError("fcntl.flock is required for inter-process locking")
        if self._fd is not None:
            raise RouteGenerationLockError("route generation lock is already acquired")
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        flags = fcntl.LOCK_EX
        if not self.blocking:
            flags |= fcntl.LOCK_NB
        try:
            fcntl.flock(fd, flags)
        except OSError as exc:
            os.close(fd)
            if exc.errno in {errno.EACCES, errno.EAGAIN}:
                raise RouteGenerationLockUnavailable("route generation lock is already held") from exc
            raise RouteGenerationLockError(f"could not acquire route generation lock: {exc}") from exc
        self._fd = fd
        return self.info("locked")

    def release(self) -> RouteGenerationLockInfo:
        """Release the lock and close its file descriptor."""

        fd = self._fd
        if fd is None:
            raise RouteGenerationLockError("route generation lock is not acquired")
        if fcntl is None:
            raise RouteGenerationLockError("fcntl.flock is required for inter-process locking")
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
            self._fd = None
        return self.info("released")

    def info(self, state: LockState | None = None) -> RouteGenerationLockInfo:
        """Return the current lock projection without mutating the lock."""

        current_state: LockState = state or ("locked" if self._fd is not None else "released")
        return RouteGenerationLockInfo(
            schema=ROUTE_GENERATION_LOCK_SCHEMA,
            route_id=self.route_id,
            lock_path=str(self.lock_path),
            state=current_state,
            blocking=self.blocking,
        )

    def __enter__(self) -> RouteGenerationLockInfo:
        return self.acquire()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._fd is not None:
            self.release()


def route_generation_lock_path(controlfs_root: Path | str, route_id: str) -> Path:
    """Return the sidecar ControlFS lock path for one logical route."""

    safe_route_id = normalize_route_id(route_id)
    return Path(controlfs_root) / "active" / "routes" / safe_route_id / "generation.lock"


def acquire_route_generation_lock(
    *,
    controlfs_root: Path | str,
    route_id: str,
    blocking: bool = True,
) -> RouteGenerationFileLock:
    """Build an importable lock context manager for callers.

    Example:

    ```python
    with acquire_route_generation_lock(controlfs_root=root, route_id="route-a"):
        ...  # load generation table, materialize g2/g3, persist table
    ```
    """

    return RouteGenerationFileLock(
        controlfs_root=controlfs_root,
        route_id=route_id,
        blocking=blocking,
    )
