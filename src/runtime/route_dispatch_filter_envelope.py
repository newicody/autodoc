from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


_FIELD_NAMES: tuple[str, ...] = ("route_id", "zone", "policy_decision_id", "authorized")


@dataclass(frozen=True, slots=True)
class RouteDispatchFilterEnvelope:
    """Scheduler-issued route envelope used for policy/zone dispatch filtering.

    The envelope is deliberately not a security authority. Scheduler/policy/zone
    remain the authority. ControlProxy uses this immutable envelope to filter and
    route already-decided work toward the correct handler/materialization path.
    """

    route_id: str
    zone: str
    policy_decision_id: str
    authorized: bool
    source: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.route_id:
            raise ValueError("route_id is required")
        if not self.zone:
            raise ValueError("zone is required")
        if not self.policy_decision_id:
            raise ValueError("policy_decision_id is required")
        if self.authorized is not True:
            raise ValueError("authorized=True is required")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_mapping(self) -> dict[str, Any]:
        """Return a stable JSON-ready projection for logs, docs, and tests."""

        return {
            "route_id": self.route_id,
            "zone": self.zone,
            "policy_decision_id": self.policy_decision_id,
            "authorized": self.authorized,
            "source": self.source,
            "metadata": dict(self.metadata),
            "purpose": "policy/zone dispatch filtering, not a security objective",
        }


@dataclass(frozen=True, slots=True)
class RouteDispatchFilterDecision:
    """Result of reading an already-authorized route request envelope."""

    accepted: bool
    reason: str
    envelope: RouteDispatchFilterEnvelope | None = None
    missing_fields: tuple[str, ...] = ()

    def to_mapping(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "missing_fields": list(self.missing_fields),
            "envelope": None if self.envelope is None else self.envelope.to_mapping(),
        }


def _read_field(payload: object, field_name: str) -> Any:
    if isinstance(payload, Mapping):
        return payload.get(field_name)
    return getattr(payload, field_name, None)


def _read_metadata(payload: object) -> Mapping[str, Any]:
    metadata = _read_field(payload, "metadata")
    if isinstance(metadata, Mapping):
        return metadata
    return {}


def _read_source(payload: object) -> str | None:
    source = _read_field(payload, "source")
    if isinstance(source, str) and source:
        return source
    return None


def evaluate_route_dispatch_filter(payload: object) -> RouteDispatchFilterDecision:
    """Evaluate a Scheduler-facing route payload for dispatch filtering.

    This function checks the presence of the Scheduler/policy/zone envelope. It
    does not decide policy and it does not grant authority. A rejected decision
    only means that ControlProxy cannot route this payload coherently.
    """

    missing = tuple(name for name in _FIELD_NAMES if _read_field(payload, name) in (None, ""))
    if missing:
        return RouteDispatchFilterDecision(
            accepted=False,
            reason="missing dispatch filter envelope fields",
            missing_fields=missing,
        )

    authorized = _read_field(payload, "authorized")
    if authorized is not True:
        return RouteDispatchFilterDecision(
            accepted=False,
            reason="authorized flag is not true",
            missing_fields=(),
        )

    envelope = RouteDispatchFilterEnvelope(
        route_id=str(_read_field(payload, "route_id")),
        zone=str(_read_field(payload, "zone")),
        policy_decision_id=str(_read_field(payload, "policy_decision_id")),
        authorized=True,
        source=_read_source(payload),
        metadata=_read_metadata(payload),
    )
    return RouteDispatchFilterDecision(
        accepted=True,
        reason="accepted for policy/zone dispatch filtering",
        envelope=envelope,
    )


def require_route_dispatch_filter_envelope(payload: object) -> RouteDispatchFilterEnvelope:
    """Return the dispatch-filter envelope or raise a deterministic error."""

    decision = evaluate_route_dispatch_filter(payload)
    if decision.envelope is not None:
        return decision.envelope
    missing = ", ".join(decision.missing_fields)
    suffix = f": {missing}" if missing else ""
    raise ValueError(f"route dispatch filter rejected payload: {decision.reason}{suffix}")


__all__ = (
    "RouteDispatchFilterDecision",
    "RouteDispatchFilterEnvelope",
    "evaluate_route_dispatch_filter",
    "require_route_dispatch_filter_envelope",
)
