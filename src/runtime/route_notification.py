"""Route notification primitive.

This module implements phase 0082.

It provides a Python importable notification abstraction for mmap routes:

    writer writes RouteMessage frame to mmap route
    writer calls notifier.notify(1)
    reader/select loop sees notifier.fileno() readable
    reader drains notifier counter
    reader drains mmap route frames

Implementation choices:

- Prefer Linux eventfd through Python's os.eventfd when available.
- Fall back to libc eventfd through ctypes when Python lacks os.eventfd.
- Fall back to a non-blocking pipe when eventfd is unavailable or when tests
  request backend="pipe".

This uses existing kernel/Python/libc primitives from Python. It does not
require a custom C extension.

It deliberately does not:
- create a daemon
- start a service
- use OpenRC
- watch ControlFS
- call Scheduler
- issue leases
- implement lease handoff
- mutate mmap route layout
- resize live mmap routes
- create POSIX shm_open objects
- require /dev/shm
- implement inter-process ownership rules
- implement VisPy

It is a primitive, not a CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import errno
import os
import selectors
import struct
from typing import Literal


NotificationBackend = Literal["auto", "eventfd", "pipe"]
ResolvedBackend = Literal["eventfd", "pipe"]

_U64_NATIVE = "Q"


class RouteNotificationError(RuntimeError):
    """Base error for route notification failures."""


class RouteNotificationClosedError(RouteNotificationError):
    """Raised when using a closed notifier."""


class RouteNotificationWouldBlock(RouteNotificationError):
    """Raised when notify cannot write without blocking."""


@dataclass(frozen=True)
class RouteNotificationStats:
    """User-visible notification state."""

    route_handle: str
    backend: ResolvedBackend
    read_fd: int
    write_fd: int
    pending_last_drain: int
    closed: bool

    def to_mapping(self) -> dict[str, int | str | bool]:
        return {
            "route_handle": self.route_handle,
            "backend": self.backend,
            "read_fd": self.read_fd,
            "write_fd": self.write_fd,
            "pending_last_drain": self.pending_last_drain,
            "closed": self.closed,
        }


class RouteNotifier:
    """Notification primitive usable with selectors.

    `fileno()` returns the readable file descriptor. A consumer can register it
    in `selectors.DefaultSelector` and drain the mmap route after readability.
    """

    def __init__(
        self,
        *,
        route_handle: str,
        backend: ResolvedBackend,
        read_fd: int,
        write_fd: int,
        owns_read_fd: bool = True,
        owns_write_fd: bool = True,
    ):
        self.route_handle = _safe_handle(route_handle)
        self.backend = backend
        self._read_fd = read_fd
        self._write_fd = write_fd
        self._owns_read_fd = owns_read_fd
        self._owns_write_fd = owns_write_fd
        self._closed = False
        self._pending_last_drain = 0

    @classmethod
    def create(
        cls,
        route_handle: str,
        *,
        backend: NotificationBackend = "auto",
        nonblocking: bool = True,
    ) -> "RouteNotifier":
        """Create a notifier.

        `auto` selects eventfd when available, otherwise pipe.
        """

        if backend not in ("auto", "eventfd", "pipe"):
            raise ValueError("backend must be auto, eventfd or pipe")

        if backend in ("auto", "eventfd"):
            fd = _create_eventfd(nonblocking=nonblocking)
            if fd is not None:
                return cls(
                    route_handle=route_handle,
                    backend="eventfd",
                    read_fd=fd,
                    write_fd=fd,
                    owns_read_fd=True,
                    owns_write_fd=False,
                )
            if backend == "eventfd":
                raise RouteNotificationError("eventfd is not available on this platform")

        read_fd, write_fd = os.pipe()
        if nonblocking:
            os.set_blocking(read_fd, False)
            os.set_blocking(write_fd, False)
        return cls(
            route_handle=route_handle,
            backend="pipe",
            read_fd=read_fd,
            write_fd=write_fd,
            owns_read_fd=True,
            owns_write_fd=True,
        )

    def fileno(self) -> int:
        """Return readable fd for selectors."""

        self._ensure_open()
        return self._read_fd

    def notify(self, count: int = 1) -> None:
        """Signal that count route items are available."""

        self._ensure_open()
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("count must be a positive integer")
        if count >= 2**64:
            raise ValueError("count must fit in uint64")

        payload = struct.pack(_U64_NATIVE, count)
        try:
            os.write(self._write_fd, payload)
        except BlockingIOError as exc:
            raise RouteNotificationWouldBlock("notification fd would block") from exc
        except OSError as exc:
            raise RouteNotificationError(str(exc)) from exc

    def drain(self) -> int:
        """Drain all currently available notification counts."""

        self._ensure_open()
        total = 0

        while True:
            try:
                raw = os.read(self._read_fd, 8)
            except BlockingIOError:
                break
            except OSError as exc:
                if exc.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    break
                raise RouteNotificationError(str(exc)) from exc

            if raw == b"":
                break
            if len(raw) != 8:
                raise RouteNotificationError("partial notification counter read")
            total += struct.unpack(_U64_NATIVE, raw)[0]

            if self.backend == "eventfd":
                # eventfd returns the whole counter in one read.
                break

        self._pending_last_drain = total
        return total

    def wait_once(self, timeout: float | None = 0.0) -> bool:
        """Return True when the notifier is readable within timeout."""

        self._ensure_open()
        selector = selectors.DefaultSelector()
        try:
            selector.register(self._read_fd, selectors.EVENT_READ)
            return bool(selector.select(timeout))
        finally:
            selector.close()

    def stats(self) -> RouteNotificationStats:
        return RouteNotificationStats(
            route_handle=self.route_handle,
            backend=self.backend,
            read_fd=self._read_fd,
            write_fd=self._write_fd,
            pending_last_drain=self._pending_last_drain,
            closed=self._closed,
        )

    def close(self) -> None:
        if self._closed:
            return
        if self._owns_read_fd:
            _close_fd(self._read_fd)
        if self._owns_write_fd and self._write_fd != self._read_fd:
            _close_fd(self._write_fd)
        self._closed = True

    def __enter__(self) -> "RouteNotifier":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RouteNotificationClosedError("route notifier is closed")


def notify_after_write(notifier: RouteNotifier, *, written_count: int = 1) -> None:
    """Tiny helper to make write-then-notify call sites explicit."""

    notifier.notify(written_count)


def drain_ready_count(notifier: RouteNotifier) -> int:
    """Tiny helper to make select-then-drain call sites explicit."""

    return notifier.drain()


def eventfd_available() -> bool:
    """Return whether eventfd can be created from this Python process."""

    fd = _create_eventfd(nonblocking=True)
    if fd is None:
        return False
    _close_fd(fd)
    return True


def _create_eventfd(*, nonblocking: bool) -> int | None:
    flags = 0
    if nonblocking:
        flags |= getattr(os, "EFD_NONBLOCK", 0x800)
    flags |= getattr(os, "EFD_CLOEXEC", 0x80000)

    if hasattr(os, "eventfd"):
        try:
            return os.eventfd(0, flags)  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass

    return _create_eventfd_ctypes(flags)


def _create_eventfd_ctypes(flags: int) -> int | None:
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        eventfd = getattr(libc, "eventfd")
    except (AttributeError, OSError):
        return None

    eventfd.argtypes = [ctypes.c_uint, ctypes.c_int]
    eventfd.restype = ctypes.c_int
    fd = int(eventfd(0, flags))
    if fd < 0:
        err = ctypes.get_errno()
        if err in (errno.ENOSYS, errno.EINVAL, errno.EPERM):
            return None
        return None
    return fd


def _safe_handle(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("route_handle must be a non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise ValueError("route_handle must not contain path traversal")
    return value


def _close_fd(fd: int) -> None:
    try:
        os.close(fd)
    except OSError:
        pass
