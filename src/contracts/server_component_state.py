"""Immutable component-owned state snapshots for server scientific framing.

Snapshots describe only facts returned by their owning components. Unknown and
stale values remain explicit; this contract never derives Scheduler capacity
from physical utilization and never authorizes execution.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
import math
from types import MappingProxyType
from typing import Any

COMPONENT_STATE_SCHEMA = "missipy.server.component_state_snapshot.v1"

_STATUSES = {"complete", "partial", "unavailable", "error"}
_AVAILABILITY = {"available", "constrained", "unavailable", "unknown"}
_FRESHNESS = {"fresh", "stale", "unknown"}
_COMMUNICATION = {"connected", "degraded", "unavailable", "unknown"}
_COHERENCE = {"coherent", "partially_coherent", "incoherent"}


class ComponentStateContractError(ValueError):
    """Invalid component-owned state snapshot."""


@dataclass(frozen=True, slots=True)
class ServerComponentStateSnapshot:
    component_ref: str
    source_ref: str
    observed_at: str
    status: str
    availability: str
    freshness: str
    communication_status: str
    capabilities: tuple[str, ...] = ()
    reservations: tuple[str, ...] = ()
    interfaces: tuple[str, ...] = ()
    usage_statistics: Mapping[str, int | float] = field(default_factory=dict)
    supported_representations: tuple[str, ...] = ()
    unsupported_representations: tuple[str, ...] = ()
    available_data: tuple[str, ...] = ()
    missing_data: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    report_outline: tuple[str, ...] = ()
    assessment: str = ""
    coherence_status: str = "partially_coherent"
    errors: tuple[str, ...] = ()
    schema: str = COMPONENT_STATE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != COMPONENT_STATE_SCHEMA:
            raise ComponentStateContractError("unsupported component state schema")
        _typed_ref("component_ref", self.component_ref, "component:")
        _typed_ref("source_ref", self.source_ref, "component-state-source:")
        _timestamp(self.observed_at)
        for name, value, allowed in (
            ("status", self.status, _STATUSES),
            ("availability", self.availability, _AVAILABILITY),
            ("freshness", self.freshness, _FRESHNESS),
            ("communication_status", self.communication_status, _COMMUNICATION),
            ("coherence_status", self.coherence_status, _COHERENCE),
        ):
            if value not in allowed:
                raise ComponentStateContractError(f"{name} is unsupported")
        for name in (
            "capabilities", "reservations", "interfaces",
            "supported_representations", "unsupported_representations",
            "available_data", "missing_data", "constraints", "report_outline", "errors",
        ):
            values = tuple(getattr(self, name))
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise ComponentStateContractError(f"{name} must contain non-empty strings")
            object.__setattr__(self, name, values)
        if self.status == "complete" and self.errors:
            raise ComponentStateContractError("complete snapshot cannot contain errors")
        if self.status == "error" and not self.errors:
            raise ComponentStateContractError("error snapshot requires an error")
        if not isinstance(self.assessment, str):
            raise ComponentStateContractError("assessment must be text")
        statistics = dict(self.usage_statistics)
        for key, value in statistics.items():
            if not isinstance(key, str) or not key.strip():
                raise ComponentStateContractError("usage statistic names must be non-empty")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ComponentStateContractError("usage statistics must be numeric")
            if not math.isfinite(value) or value < 0:
                raise ComponentStateContractError("usage statistics must be finite and non-negative")
        object.__setattr__(self, "usage_statistics", MappingProxyType(statistics))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "component_ref": self.component_ref,
            "source_ref": self.source_ref,
            "observed_at": self.observed_at,
            "status": self.status,
            "availability": self.availability,
            "freshness": self.freshness,
            "communication_status": self.communication_status,
            "capabilities": list(self.capabilities),
            "reservations": list(self.reservations),
            "interfaces": list(self.interfaces),
            "usage_statistics": dict(self.usage_statistics),
            "supported_representations": list(self.supported_representations),
            "unsupported_representations": list(self.unsupported_representations),
            "available_data": list(self.available_data),
            "missing_data": list(self.missing_data),
            "constraints": list(self.constraints),
            "report_outline": list(self.report_outline),
            "assessment": self.assessment,
            "coherence_status": self.coherence_status,
            "errors": list(self.errors),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ServerComponentStateSnapshot":
        return cls(
            component_ref=value["component_ref"],
            source_ref=value["source_ref"],
            observed_at=value["observed_at"],
            status=value["status"],
            availability=value["availability"],
            freshness=value["freshness"],
            communication_status=value["communication_status"],
            capabilities=tuple(value.get("capabilities", ())),
            reservations=tuple(value.get("reservations", ())),
            interfaces=tuple(value.get("interfaces", ())),
            usage_statistics=value.get("usage_statistics", {}),
            supported_representations=tuple(value.get("supported_representations", ())),
            unsupported_representations=tuple(value.get("unsupported_representations", ())),
            available_data=tuple(value.get("available_data", ())),
            missing_data=tuple(value.get("missing_data", ())),
            constraints=tuple(value.get("constraints", ())),
            report_outline=tuple(value.get("report_outline", ())),
            assessment=value.get("assessment", ""),
            coherence_status=value.get("coherence_status", "partially_coherent"),
            errors=tuple(value.get("errors", ())),
            schema=value.get("schema", COMPONENT_STATE_SCHEMA),
        )


def _typed_ref(name: str, value: object, prefix: str) -> None:
    if not isinstance(value, str) or not value.startswith(prefix) or any(ch.isspace() for ch in value):
        raise ComponentStateContractError(f"{name} must use {prefix} typed reference")


def _timestamp(value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ComponentStateContractError("observed_at must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ComponentStateContractError("observed_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ComponentStateContractError("observed_at must include a timezone")
