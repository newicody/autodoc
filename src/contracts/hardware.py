from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math
import re
from collections.abc import Mapping
from typing import Any


HARDWARE_SAMPLE_SCHEMA = "missipy.hardware_sample.v1"
HARDWARE_CELL_SCHEMA = "missipy.hardware_cell.v1"

_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_METRIC_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")


class HardwareContractError(ValueError):
    """Invalid immutable hardware observation contract."""


class HardwareCollectionStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class HardwareMetricUnit(str, Enum):
    PERCENT = "percent"
    COUNT = "count"
    BYTES = "bytes"
    BYTES_PER_SECOND = "bytes_per_second"
    PACKETS_PER_SECOND = "packets_per_second"
    LOAD = "load"
    CELSIUS = "celsius"


class HardwareResourceKind(str, Enum):
    HOST = "host"
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    GPU = "gpu"
    ACCELERATOR = "accelerator"


class HardwareFreshness(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


class HardwareAvailability(str, Enum):
    AVAILABLE = "available"
    CONSTRAINED = "constrained"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class HardwareMetric:
    metric: str
    resource_ref: str
    value: int | float
    unit: HardwareMetricUnit
    source_ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.metric, str) or _METRIC_RE.fullmatch(self.metric) is None:
            raise HardwareContractError("metric must be a dotted lower-case identifier")
        _require_ref("resource_ref", self.resource_ref, "resource:")
        _require_ref("source_ref", self.source_ref, "hardware-source:")
        _require_finite_number("value", self.value)
        if not isinstance(self.unit, HardwareMetricUnit):
            raise HardwareContractError("unit must be HardwareMetricUnit")
        if self.unit is HardwareMetricUnit.PERCENT and not 0 <= self.value <= 100:
            raise HardwareContractError("percent values must be between 0 and 100")
        if self.unit is not HardwareMetricUnit.CELSIUS and self.value < 0:
            raise HardwareContractError("non-temperature metrics cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "resource_ref": self.resource_ref,
            "source_ref": self.source_ref,
            "unit": self.unit.value,
            "value": self.value,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> HardwareMetric:
        return cls(
            metric=value["metric"],
            resource_ref=value["resource_ref"],
            value=value["value"],
            unit=HardwareMetricUnit(value["unit"]),
            source_ref=value["source_ref"],
        )


@dataclass(frozen=True, slots=True)
class HardwareCollectionError:
    source_ref: str
    error_type: str
    message: str
    retryable: bool = False

    def __post_init__(self) -> None:
        _require_ref("source_ref", self.source_ref, "hardware-source:")
        _require_text("error_type", self.error_type)
        _require_text("message", self.message)
        if not isinstance(self.retryable, bool):
            raise HardwareContractError("retryable must be bool")

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "retryable": self.retryable,
            "source_ref": self.source_ref,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> HardwareCollectionError:
        return cls(
            source_ref=value["source_ref"],
            error_type=value["error_type"],
            message=value["message"],
            retryable=value.get("retryable", False),
        )


@dataclass(frozen=True, slots=True)
class HardwareSample:
    sample_id: str
    host_ref: str
    source_ref: str
    observed_at: str
    metrics: tuple[HardwareMetric, ...]
    status: HardwareCollectionStatus
    errors: tuple[HardwareCollectionError, ...] = ()
    schema: str = HARDWARE_SAMPLE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != HARDWARE_SAMPLE_SCHEMA:
            raise HardwareContractError(f"unsupported hardware sample schema: {self.schema!r}")
        _require_ref("sample_id", self.sample_id, "hardware-sample:")
        _require_ref("host_ref", self.host_ref, "host:")
        _require_ref("source_ref", self.source_ref, "hardware-source:")
        _require_utc_timestamp("observed_at", self.observed_at)
        if not isinstance(self.status, HardwareCollectionStatus):
            raise HardwareContractError("status must be HardwareCollectionStatus")
        metrics = tuple(self.metrics)
        errors = tuple(self.errors)
        if any(not isinstance(item, HardwareMetric) for item in metrics):
            raise HardwareContractError("metrics must contain HardwareMetric values")
        if any(not isinstance(item, HardwareCollectionError) for item in errors):
            raise HardwareContractError("errors must contain HardwareCollectionError values")
        keys = [(item.metric, item.resource_ref) for item in metrics]
        if len(set(keys)) != len(keys):
            raise HardwareContractError("metrics contains duplicate metric/resource pairs")
        if self.status is HardwareCollectionStatus.COMPLETE and errors:
            raise HardwareContractError("complete samples cannot contain collection errors")
        if self.status is HardwareCollectionStatus.PARTIAL and (not metrics or not errors):
            raise HardwareContractError("partial samples require metrics and collection errors")
        if self.status in {HardwareCollectionStatus.UNAVAILABLE, HardwareCollectionStatus.ERROR} and metrics:
            raise HardwareContractError("unavailable/error samples cannot contain metrics")
        if self.status is HardwareCollectionStatus.ERROR and not errors:
            raise HardwareContractError("error samples require at least one collection error")
        object.__setattr__(self, "metrics", metrics)
        object.__setattr__(self, "errors", errors)

    def to_dict(self) -> dict[str, Any]:
        return {
            "errors": [item.to_dict() for item in self.errors],
            "host_ref": self.host_ref,
            "metrics": [item.to_dict() for item in self.metrics],
            "observed_at": self.observed_at,
            "sample_id": self.sample_id,
            "schema": self.schema,
            "source_ref": self.source_ref,
            "status": self.status.value,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> HardwareSample:
        if value.get("schema") != HARDWARE_SAMPLE_SCHEMA:
            raise HardwareContractError("unsupported hardware sample schema")
        return cls(
            sample_id=value["sample_id"],
            host_ref=value["host_ref"],
            source_ref=value["source_ref"],
            observed_at=value["observed_at"],
            metrics=tuple(HardwareMetric.from_mapping(item) for item in value.get("metrics", ())),
            status=HardwareCollectionStatus(value["status"]),
            errors=tuple(HardwareCollectionError.from_mapping(item) for item in value.get("errors", ())),
            schema=value["schema"],
        )


@dataclass(frozen=True, slots=True)
class HardwarePhysicalSnapshot:
    availability: HardwareAvailability
    metrics: tuple[HardwareMetric, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.availability, HardwareAvailability):
            raise HardwareContractError("physical availability must be HardwareAvailability")
        metrics = tuple(self.metrics)
        if any(not isinstance(item, HardwareMetric) for item in metrics):
            raise HardwareContractError("physical metrics must contain HardwareMetric values")
        object.__setattr__(self, "metrics", metrics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "availability": self.availability.value,
            "metrics": [item.to_dict() for item in self.metrics],
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> HardwarePhysicalSnapshot:
        return cls(
            availability=HardwareAvailability(value["availability"]),
            metrics=tuple(HardwareMetric.from_mapping(item) for item in value.get("metrics", ())),
        )


@dataclass(frozen=True, slots=True)
class HardwareSchedulerSnapshot:
    availability: HardwareAvailability
    capacity: int | None = None
    reserved: int | None = None
    available: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.availability, HardwareAvailability):
            raise HardwareContractError("scheduler availability must be HardwareAvailability")
        values = (self.capacity, self.reserved, self.available)
        if all(value is None for value in values):
            return
        if any(value is None for value in values):
            raise HardwareContractError("capacity, reserved and available must be all known or all unknown")
        for name, value in zip(("capacity", "reserved", "available"), values):
            _require_non_negative_int(name, value)
        if self.reserved > self.capacity:
            raise HardwareContractError("reserved cannot exceed capacity")
        if self.available != self.capacity - self.reserved:
            raise HardwareContractError("available must equal capacity minus reserved")

    def to_dict(self) -> dict[str, Any]:
        return {
            "availability": self.availability.value,
            "available": self.available,
            "capacity": self.capacity,
            "reserved": self.reserved,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> HardwareSchedulerSnapshot:
        return cls(
            availability=HardwareAvailability(value["availability"]),
            capacity=value.get("capacity"),
            reserved=value.get("reserved"),
            available=value.get("available"),
        )


@dataclass(frozen=True, slots=True)
class HardwareCell:
    cell_id: str
    host_ref: str
    resource_ref: str
    resource_kind: HardwareResourceKind
    observed_at: str
    freshness: HardwareFreshness
    physical: HardwarePhysicalSnapshot
    scheduler: HardwareSchedulerSnapshot
    source_refs: tuple[str, ...]
    schema: str = HARDWARE_CELL_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != HARDWARE_CELL_SCHEMA:
            raise HardwareContractError(f"unsupported hardware cell schema: {self.schema!r}")
        _require_ref("cell_id", self.cell_id, "hardware-cell:")
        _require_ref("host_ref", self.host_ref, "host:")
        _require_ref("resource_ref", self.resource_ref, "resource:")
        _require_utc_timestamp("observed_at", self.observed_at)
        if not isinstance(self.resource_kind, HardwareResourceKind):
            raise HardwareContractError("resource_kind must be HardwareResourceKind")
        if not isinstance(self.freshness, HardwareFreshness):
            raise HardwareContractError("freshness must be HardwareFreshness")
        if not isinstance(self.physical, HardwarePhysicalSnapshot):
            raise HardwareContractError("physical must be HardwarePhysicalSnapshot")
        if not isinstance(self.scheduler, HardwareSchedulerSnapshot):
            raise HardwareContractError("scheduler must be HardwareSchedulerSnapshot")
        if any(item.resource_ref != self.resource_ref for item in self.physical.metrics):
            raise HardwareContractError("physical metrics must belong to this resource_ref")
        refs = tuple(self.source_refs)
        if not refs:
            raise HardwareContractError("source_refs must not be empty")
        for ref in refs:
            _require_ref("source_refs item", ref)
        if len(set(refs)) != len(refs):
            raise HardwareContractError("source_refs must be unique")
        object.__setattr__(self, "source_refs", refs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "freshness": self.freshness.value,
            "host_ref": self.host_ref,
            "observed_at": self.observed_at,
            "physical": self.physical.to_dict(),
            "resource_kind": self.resource_kind.value,
            "resource_ref": self.resource_ref,
            "scheduler": self.scheduler.to_dict(),
            "schema": self.schema,
            "source_refs": list(self.source_refs),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> HardwareCell:
        if value.get("schema") != HARDWARE_CELL_SCHEMA:
            raise HardwareContractError("unsupported hardware cell schema")
        return cls(
            cell_id=value["cell_id"],
            host_ref=value["host_ref"],
            resource_ref=value["resource_ref"],
            resource_kind=HardwareResourceKind(value["resource_kind"]),
            observed_at=value["observed_at"],
            freshness=HardwareFreshness(value["freshness"]),
            physical=HardwarePhysicalSnapshot.from_mapping(value["physical"]),
            scheduler=HardwareSchedulerSnapshot.from_mapping(value["scheduler"]),
            source_refs=tuple(value["source_refs"]),
            schema=value["schema"],
        )


def _require_text(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise HardwareContractError(f"{name} must be a non-empty string")


def _require_ref(name: str, value: object, prefix: str = "") -> None:
    if not isinstance(value, str) or _REF_RE.fullmatch(value) is None:
        raise HardwareContractError(f"{name} must be a typed reference")
    if prefix and not value.startswith(prefix):
        raise HardwareContractError(f"{name} must start with {prefix}")


def _require_finite_number(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HardwareContractError(f"{name} must be a finite number")
    if not math.isfinite(float(value)):
        raise HardwareContractError(f"{name} must be finite")


def _require_non_negative_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise HardwareContractError(f"{name} must be a non-negative integer")


def _require_utc_timestamp(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise HardwareContractError(f"{name} must be a UTC ISO-8601 timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise HardwareContractError(f"{name} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise HardwareContractError(f"{name} must be UTC")
