"""File-backed fixed-slot mmap route prototype.

This module implements phase 0080.

It consumes ControlProxy route decisions produced by 0079-r2/r3 and creates a
single-process file-backed mmap ring with fixed-size slots.

It deliberately does not:
- create POSIX shared memory with shm_open
- require /dev/shm
- create semaphores
- create eventfd
- create futex
- start a ControlProxy daemon
- watch ControlFS
- call Scheduler
- implement lease handoff
- implement live mmap resize
- implement inter-process safety
- implement VisPy

The mmap file is the data surface. Notification remains future work.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import mmap
from pathlib import Path
import struct
from typing import Any, Iterable, Mapping

from runtime.controlproxy_prepare import RoutePrepareDecision
from runtime.route_frame_codec import decode_route_message_frame, encode_route_message_frame
from runtime.shm_runtime_schema import RouteMessage


RING_MAGIC = b"MSPYMMR1"
RING_VERSION = 1
RING_HEADER_SIZE = 128
RING_HEADER_FORMAT = ">8sHHIQQQQQ"
RING_HEADER_STRUCT_SIZE = struct.calcsize(RING_HEADER_FORMAT)

SLOT_STATE_EMPTY = 0
SLOT_STATE_COMMITTED = 1
SLOT_HEADER_SIZE = 64
SLOT_HEADER_FORMAT = ">B7xQQI32s4x"
SLOT_HEADER_STRUCT_SIZE = struct.calcsize(SLOT_HEADER_FORMAT)

STATUS_SCHEMA = "missipy.mmap.fixed_slot_route_status.v1"


class MmapFixedSlotRouteError(RuntimeError):
    """Base error for mmap fixed-slot route failures."""


class MmapRouteFullError(MmapFixedSlotRouteError):
    """Raised when the ring is full and overflow policy is reject."""


class MmapFrameTooLargeError(MmapFixedSlotRouteError):
    """Raised when a frame does not fit into the fixed slot size."""


class MmapRouteCorruptionError(MmapFixedSlotRouteError):
    """Raised when a slot/header checksum or sequence is invalid."""


@dataclass(frozen=True)
class MmapRouteHeader:
    """Header stored at the start of ring.bin."""

    slot_size: int
    slot_count: int
    write_sequence: int
    read_sequence: int
    dropped_count: int

    def to_mapping(self) -> dict[str, int]:
        return {
            "slot_size": self.slot_size,
            "slot_count": self.slot_count,
            "write_sequence": self.write_sequence,
            "read_sequence": self.read_sequence,
            "dropped_count": self.dropped_count,
        }


@dataclass(frozen=True)
class MmapSlot:
    """One drained mmap slot."""

    sequence: int
    frame: bytes

    @property
    def frame_size(self) -> int:
        return len(self.frame)

    @property
    def frame_sha256(self) -> str:
        return "sha256:" + hashlib.sha256(self.frame).hexdigest()

    def message(self) -> RouteMessage:
        return decode_route_message_frame(self.frame).message

    def to_mapping(self) -> dict[str, Any]:
        msg = self.message()
        return {
            "sequence": self.sequence,
            "frame_size": self.frame_size,
            "frame_sha256": self.frame_sha256,
            "route_id": msg.route_id,
            "message_id": msg.message_id,
        }


@dataclass(frozen=True)
class MmapRouteStats:
    """Stats for a materialized mmap fixed-slot route."""

    route_handle: str
    ring_path: str
    status_path: str
    slot_size: int
    slot_count: int
    file_size: int
    write_sequence: int
    read_sequence: int
    dropped_count: int
    occupancy: int
    overflow_policy: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "route_handle": self.route_handle,
            "ring_path": self.ring_path,
            "status_path": self.status_path,
            "slot_size": self.slot_size,
            "slot_count": self.slot_count,
            "file_size": self.file_size,
            "write_sequence": self.write_sequence,
            "read_sequence": self.read_sequence,
            "dropped_count": self.dropped_count,
            "occupancy": self.occupancy,
            "overflow_policy": self.overflow_policy,
        }


def route_file_size(slot_size: int, slot_count: int) -> int:
    """Return ring.bin size for slot_size and slot_count."""

    _validate_positive_int(slot_size, "slot_size")
    _validate_positive_int(slot_count, "slot_count")
    return RING_HEADER_SIZE + slot_count * (SLOT_HEADER_SIZE + slot_size)


def route_dir_for_handle(runtime_root: Path | str, route_handle: str) -> Path:
    """Return routes/<route_handle> after rejecting path traversal."""

    safe = _safe_handle(route_handle)
    return Path(runtime_root) / "routes" / safe


def create_mmap_route_from_decision(
    runtime_root: Path | str,
    decision: RoutePrepareDecision,
    *,
    replace: bool = True,
) -> "MmapFixedSlotRoute":
    """Materialize a file-backed mmap route from a ready ControlProxy decision."""

    if decision.status != "ready":
        raise ValueError("only ready ControlProxy decisions can materialize mmap routes")
    if decision.route_handle is None:
        raise ValueError("ready decision must include route_handle")
    if decision.slot_size is None or decision.slot_count is None:
        raise ValueError("ready decision must include slot_size and slot_count")
    if decision.max_frame_bytes is not None and decision.max_frame_bytes > decision.slot_size:
        raise ValueError("max_frame_bytes must be <= slot_size")

    route_dir = route_dir_for_handle(runtime_root, decision.route_handle)
    route_dir.mkdir(parents=True, exist_ok=True)
    ring_path = route_dir / "ring.bin"
    status_path = route_dir / "status.json"

    if ring_path.exists() and not replace:
        route = MmapFixedSlotRoute.open(
            ring_path,
            route_handle=decision.route_handle,
            status_path=status_path,
            overflow_policy=decision.overflow_policy or "reject",
        )
        route.write_status(extra={"materialized_from": decision.to_mapping()})
        return route

    file_size = route_file_size(decision.slot_size, decision.slot_count)
    with ring_path.open("wb") as handle:
        handle.truncate(file_size)

    route = MmapFixedSlotRoute.open(
        ring_path,
        route_handle=decision.route_handle,
        status_path=status_path,
        overflow_policy=decision.overflow_policy or "reject",
    )
    route.initialize(slot_size=decision.slot_size, slot_count=decision.slot_count)
    route.write_status(extra={"materialized_from": decision.to_mapping()})
    return route


class MmapFixedSlotRoute:
    """Single-process file-backed fixed-slot mmap route."""

    def __init__(
        self,
        ring_path: Path,
        *,
        route_handle: str,
        status_path: Path,
        overflow_policy: str = "reject",
    ):
        self.ring_path = ring_path
        self.route_handle = _safe_handle(route_handle)
        self.status_path = status_path
        if overflow_policy not in ("reject", "drop_oldest"):
            raise ValueError("overflow_policy must be reject or drop_oldest")
        self.overflow_policy = overflow_policy
        self._file = None
        self._mmap: mmap.mmap | None = None

    @classmethod
    def open(
        cls,
        ring_path: Path | str,
        *,
        route_handle: str,
        status_path: Path | str | None = None,
        overflow_policy: str = "reject",
    ) -> "MmapFixedSlotRoute":
        ring = Path(ring_path)
        status = Path(status_path) if status_path is not None else ring.with_name("status.json")
        route = cls(
            ring,
            route_handle=route_handle,
            status_path=status,
            overflow_policy=overflow_policy,
        )
        route._file = ring.open("r+b")
        route._mmap = mmap.mmap(route._file.fileno(), 0)
        return route

    def close(self) -> None:
        if self._mmap is not None:
            self._mmap.flush()
            self._mmap.close()
            self._mmap = None
        if self._file is not None:
            self._file.close()
            self._file = None

    def __enter__(self) -> "MmapFixedSlotRoute":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def initialize(self, *, slot_size: int, slot_count: int) -> None:
        """Initialize an empty ring header and empty slot headers."""

        _validate_positive_int(slot_size, "slot_size")
        _validate_positive_int(slot_count, "slot_count")
        expected = route_file_size(slot_size, slot_count)
        actual = self.ring_path.stat().st_size
        if actual != expected:
            raise ValueError(f"ring file has {actual} bytes, expected {expected}")

        mm = self._require_mmap()
        self._write_header(
            MmapRouteHeader(
                slot_size=slot_size,
                slot_count=slot_count,
                write_sequence=0,
                read_sequence=0,
                dropped_count=0,
            )
        )
        for index in range(slot_count):
            self._write_slot_header(index, state=SLOT_STATE_EMPTY, sequence=0, frame_size=0, frame_sha256=b"\x00" * 32)
        mm.flush()

    def header(self) -> MmapRouteHeader:
        """Read and validate the ring header."""

        mm = self._require_mmap()
        raw = mm[:RING_HEADER_STRUCT_SIZE]
        magic, version, _flags, header_size, slot_size, slot_count, write_sequence, read_sequence, dropped_count = struct.unpack(
            RING_HEADER_FORMAT, raw
        )
        if magic != RING_MAGIC:
            raise MmapRouteCorruptionError("invalid ring magic")
        if version != RING_VERSION:
            raise MmapRouteCorruptionError("unsupported ring version")
        if header_size != RING_HEADER_SIZE:
            raise MmapRouteCorruptionError("invalid ring header size")
        return MmapRouteHeader(
            slot_size=slot_size,
            slot_count=slot_count,
            write_sequence=write_sequence,
            read_sequence=read_sequence,
            dropped_count=dropped_count,
        )

    def write_message(self, message: RouteMessage | Mapping[str, Any]) -> MmapSlot:
        """Encode and write a RouteMessage frame to the mmap ring."""

        return self.write_frame(encode_route_message_frame(message))

    def write_frame(self, frame: bytes | bytearray | memoryview) -> MmapSlot:
        """Write an already encoded RouteMessage frame to the mmap ring."""

        raw = bytes(frame)
        decode_route_message_frame(raw)  # validates frame before mutation
        header = self.header()
        if len(raw) > header.slot_size:
            raise MmapFrameTooLargeError(
                f"frame has {len(raw)} bytes, slot_size is {header.slot_size}"
            )

        occupancy = self._occupancy(header)
        if occupancy >= header.slot_count:
            if self.overflow_policy == "reject":
                raise MmapRouteFullError("mmap route is full")
            old_index = header.read_sequence % header.slot_count
            self._write_slot_header(
                old_index,
                state=SLOT_STATE_EMPTY,
                sequence=header.read_sequence,
                frame_size=0,
                frame_sha256=b"\x00" * 32,
            )
            header = MmapRouteHeader(
                slot_size=header.slot_size,
                slot_count=header.slot_count,
                write_sequence=header.write_sequence,
                read_sequence=header.read_sequence + 1,
                dropped_count=header.dropped_count + 1,
            )
            self._write_header(header)

        sequence = header.write_sequence
        index = sequence % header.slot_count
        digest = hashlib.sha256(raw).digest()

        # Write as empty first, then commit after frame bytes are complete.
        self._write_slot_header(
            index,
            state=SLOT_STATE_EMPTY,
            sequence=sequence,
            frame_size=len(raw),
            frame_sha256=digest,
        )

        start = self._frame_offset(index)
        mm = self._require_mmap()
        mm[start:start + header.slot_size] = b"\x00" * header.slot_size
        mm[start:start + len(raw)] = raw

        self._write_slot_header(
            index,
            state=SLOT_STATE_COMMITTED,
            sequence=sequence,
            frame_size=len(raw),
            frame_sha256=digest,
        )
        self._write_header(
            MmapRouteHeader(
                slot_size=header.slot_size,
                slot_count=header.slot_count,
                write_sequence=sequence + 1,
                read_sequence=header.read_sequence,
                dropped_count=header.dropped_count,
            )
        )
        mm.flush()
        return MmapSlot(sequence=sequence, frame=raw)

    def drain(self, max_items: int | None = None) -> tuple[MmapSlot, ...]:
        """Read and remove committed frames in FIFO order."""

        if max_items is not None and max_items < 0:
            raise ValueError("max_items must be non-negative")

        drained: list[MmapSlot] = []
        header = self.header()
        limit = self._occupancy(header) if max_items is None else min(max_items, self._occupancy(header))

        for _ in range(limit):
            index = header.read_sequence % header.slot_count
            state, sequence, frame_size, digest = self._read_slot_header(index)
            if state != SLOT_STATE_COMMITTED:
                break
            if sequence != header.read_sequence:
                raise MmapRouteCorruptionError(
                    f"slot sequence mismatch: expected {header.read_sequence}, got {sequence}"
                )
            frame = self._read_frame(index, frame_size, digest)
            drained.append(MmapSlot(sequence=sequence, frame=frame))
            self._write_slot_header(
                index,
                state=SLOT_STATE_EMPTY,
                sequence=sequence,
                frame_size=0,
                frame_sha256=b"\x00" * 32,
            )
            header = MmapRouteHeader(
                slot_size=header.slot_size,
                slot_count=header.slot_count,
                write_sequence=header.write_sequence,
                read_sequence=header.read_sequence + 1,
                dropped_count=header.dropped_count,
            )
            self._write_header(header)

        self._require_mmap().flush()
        return tuple(drained)

    def stats(self) -> MmapRouteStats:
        header = self.header()
        return MmapRouteStats(
            route_handle=self.route_handle,
            ring_path=str(self.ring_path),
            status_path=str(self.status_path),
            slot_size=header.slot_size,
            slot_count=header.slot_count,
            file_size=self.ring_path.stat().st_size,
            write_sequence=header.write_sequence,
            read_sequence=header.read_sequence,
            dropped_count=header.dropped_count,
            occupancy=self._occupancy(header),
            overflow_policy=self.overflow_policy,
        )

    def write_status(self, *, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            "schema": STATUS_SCHEMA,
            "route_handle": self.route_handle,
            "status": "materialized",
            "transport": "mmap.fixed_slot",
            **self.stats().to_mapping(),
        }
        if extra:
            payload.update(dict(extra))
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        self.status_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return payload

    def _require_mmap(self) -> mmap.mmap:
        if self._mmap is None:
            raise MmapFixedSlotRouteError("route is closed")
        return self._mmap

    def _write_header(self, header: MmapRouteHeader) -> None:
        mm = self._require_mmap()
        packed = struct.pack(
            RING_HEADER_FORMAT,
            RING_MAGIC,
            RING_VERSION,
            0,
            RING_HEADER_SIZE,
            header.slot_size,
            header.slot_count,
            header.write_sequence,
            header.read_sequence,
            header.dropped_count,
        )
        mm[:RING_HEADER_SIZE] = packed + b"\x00" * (RING_HEADER_SIZE - len(packed))

    def _slot_offset(self, index: int) -> int:
        header = self.header()
        if index < 0 or index >= header.slot_count:
            raise IndexError("slot index out of range")
        return RING_HEADER_SIZE + index * (SLOT_HEADER_SIZE + header.slot_size)

    def _frame_offset(self, index: int) -> int:
        return self._slot_offset(index) + SLOT_HEADER_SIZE

    def _write_slot_header(
        self,
        index: int,
        *,
        state: int,
        sequence: int,
        frame_size: int,
        frame_sha256: bytes,
    ) -> None:
        if state not in (SLOT_STATE_EMPTY, SLOT_STATE_COMMITTED):
            raise ValueError("invalid slot state")
        if len(frame_sha256) != 32:
            raise ValueError("frame_sha256 must be 32 raw bytes")
        packed = struct.pack(SLOT_HEADER_FORMAT, state, sequence, sequence, frame_size, frame_sha256)
        offset = self._slot_offset(index)
        self._require_mmap()[offset:offset + SLOT_HEADER_SIZE] = packed

    def _read_slot_header(self, index: int) -> tuple[int, int, int, bytes]:
        offset = self._slot_offset(index)
        raw = self._require_mmap()[offset:offset + SLOT_HEADER_STRUCT_SIZE]
        state, sequence_a, sequence_b, frame_size, digest = struct.unpack(SLOT_HEADER_FORMAT, raw)
        if sequence_a != sequence_b:
            raise MmapRouteCorruptionError("slot sequence mirror mismatch")
        return state, sequence_a, frame_size, digest

    def _read_frame(self, index: int, frame_size: int, digest: bytes) -> bytes:
        header = self.header()
        if frame_size < 1 or frame_size > header.slot_size:
            raise MmapRouteCorruptionError("invalid frame size in slot")
        offset = self._frame_offset(index)
        frame = bytes(self._require_mmap()[offset:offset + frame_size])
        if hashlib.sha256(frame).digest() != digest:
            raise MmapRouteCorruptionError("slot frame checksum mismatch")
        decode_route_message_frame(frame)
        return frame

    @staticmethod
    def _occupancy(header: MmapRouteHeader) -> int:
        return max(0, min(header.slot_count, header.write_sequence - header.read_sequence))


def materialize_decisions(
    runtime_root: Path | str,
    decisions: Iterable[RoutePrepareDecision],
    *,
    replace: bool = True,
) -> tuple[MmapFixedSlotRoute, ...]:
    """Materialize all ready ControlProxy decisions as mmap fixed-slot routes."""

    routes: list[MmapFixedSlotRoute] = []
    for decision in decisions:
        if decision.status == "ready":
            routes.append(create_mmap_route_from_decision(runtime_root, decision, replace=replace))
    return tuple(routes)


def _safe_handle(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("route handle must be a non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise ValueError("route handle must not contain path traversal")
    return value


def _validate_positive_int(value: int, field: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
