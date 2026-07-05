"""Route proxy flow-control contracts.

0129 introduces RouteProxy flow control as a fast data-plane guard around
/dev/shm route zones.  Scheduler remains the orchestrator; RouteProxy applies
leases, writer permits, context generation fences, route pressure hints, and
runtime registry mirrors on /dev/shm.  EventBus observes RouteProxy facts and
statistics; it does not carry payload commands.  SQLContextStore remains durable
authority.  E5/OpenVINO remains embedding only behind adapter, and Qdrant remains
projection and recall only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re

_LEASE_SCHEMA = "missipy.route_proxy.lease.v1"
_PERMIT_SCHEMA = "missipy.route_proxy.writer_permit.v1"
_ZONE_STATE_SCHEMA = "missipy.route_proxy.zone_state.v1"
_GENERATION_FENCE_SCHEMA = "missipy.route_proxy.context_generation_fence.v1"
_PRIORITY_HINT_SCHEMA = "missipy.route_proxy.priority_hint.v1"
_REGISTRY_SNAPSHOT_SCHEMA = "missipy.route_proxy.registry_snapshot.v1"
_PRESSURE_SIGNAL_SCHEMA = "missipy.route_proxy.pressure_signal.v1"
_OBSERVATION_FACT_SCHEMA = "missipy.bus.route_proxy_observation_fact.v1"
_FLOW_PACKET_SCHEMA = "missipy.route_proxy.flow_control_packet.v1"

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_ALLOWED_ROUTE_PREFIXES = ("route:", "route-frame:", "route-zone:")
_ALLOWED_OWNER_PREFIXES = ("specialist:", "worker:", "scheduler-command:", "proxy:")
_ALLOWED_LEASE_PREFIXES = ("route-lease:",)
_ALLOWED_PERMIT_PREFIXES = ("route-permit:",)
_ALLOWED_FENCE_PREFIXES = ("route-fence:",)
_ALLOWED_PRIORITY_PREFIXES = ("route-priority:",)
_ALLOWED_SNAPSHOT_PREFIXES = ("route-registry:",)
_ALLOWED_PRESSURE_PREFIXES = ("route-pressure:",)
_ALLOWED_FACT_PREFIXES = ("bus:", "scheduler-trace:", "route-proxy-fact:")
_ALLOWED_REGISTRY_REF_PREFIXES = ("vector-registry:", "collection:", "qdrant:", "sql:", "ctx:")
_ALLOWED_CONTEXT_PREFIXES = ("sql:", "ctx:", "ctx-result:", "cycle-state:")
_ALLOWED_STATES = ("idle", "requested", "granted", "blocked", "stale", "released", "expired")
_ALLOWED_ZONE_STATES = ("open", "reserved", "blocked", "stale", "draining", "closed")
_ALLOWED_PRESSURE_LEVELS = ("low", "medium", "high", "critical")
_ALLOWED_PRIORITY_REASONS = (
    "scheduler_priority_changed",
    "context_generation_changed",
    "route_pressure_high",
    "specialist_refresh_required",
    "manual_operator_hint",
)
_ALLOWED_FACT_KINDS = (
    "route.lease_requested",
    "route.lease_granted",
    "route.lease_blocked",
    "route.writer_permit_granted",
    "route.writer_permit_denied",
    "route.context_generation_changed",
    "route.priority_changed",
    "route.registry_snapshot_published",
    "route.zone_pressure_high",
    "route.writer_blocked",
    "route.frame_marked_stale",
)


@dataclass(frozen=True, slots=True)
class RouteProxyLease:
    """A fast lease that reserves a /dev/shm route zone for one writer."""

    lease_ref: str
    route_ref: str
    owner_ref: str
    context_ref: str
    context_generation: int
    priority: int
    state: str = "requested"
    expires_after_ticks: int = 1
    reason: str = "scheduler_priority_changed"

    def __post_init__(self) -> None:
        _require_typed_ref("lease_ref", self.lease_ref, required_prefixes=_ALLOWED_LEASE_PREFIXES)
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_typed_ref("owner_ref", self.owner_ref, required_prefixes=_ALLOWED_OWNER_PREFIXES)
        _require_typed_ref("context_ref", self.context_ref, required_prefixes=_ALLOWED_CONTEXT_PREFIXES)
        _require_positive_int("context_generation", self.context_generation, allow_zero=False)
        _require_priority(self.priority)
        if self.state not in _ALLOWED_STATES:
            raise ValueError("state must be one of: " + ", ".join(_ALLOWED_STATES))
        _require_positive_int("expires_after_ticks", self.expires_after_ticks, allow_zero=False)
        if self.reason not in _ALLOWED_PRIORITY_REASONS:
            raise ValueError("reason must be one of: " + ", ".join(_ALLOWED_PRIORITY_REASONS))

    def grant(self) -> "RouteProxyLease":
        return RouteProxyLease(
            lease_ref=self.lease_ref,
            route_ref=self.route_ref,
            owner_ref=self.owner_ref,
            context_ref=self.context_ref,
            context_generation=self.context_generation,
            priority=self.priority,
            state="granted",
            expires_after_ticks=self.expires_after_ticks,
            reason=self.reason,
        )

    def mark_stale(self, *, new_context_generation: int) -> "RouteProxyLease":
        _require_positive_int("new_context_generation", new_context_generation, allow_zero=False)
        if new_context_generation <= self.context_generation:
            raise ValueError("new_context_generation must be greater than current context_generation")
        return RouteProxyLease(
            lease_ref=self.lease_ref,
            route_ref=self.route_ref,
            owner_ref=self.owner_ref,
            context_ref=self.context_ref,
            context_generation=new_context_generation,
            priority=self.priority,
            state="stale",
            expires_after_ticks=self.expires_after_ticks,
            reason="context_generation_changed",
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _LEASE_SCHEMA,
            "lease_ref": self.lease_ref,
            "route_ref": self.route_ref,
            "owner_ref": self.owner_ref,
            "context_ref": self.context_ref,
            "context_generation": self.context_generation,
            "priority": self.priority,
            "state": self.state,
            "expires_after_ticks": self.expires_after_ticks,
            "reason": self.reason,
            "route_proxy_role": "fast_dev_shm_flow_control",
            "scheduler_remains_orchestrator": True,
            "durable_authority": False,
        }


@dataclass(frozen=True, slots=True)
class RouteWriterPermit:
    """Permit returned by RouteProxy before a writer touches a route frame."""

    permit_ref: str
    lease_ref: str
    route_ref: str
    writer_ref: str
    context_generation: int
    priority: int
    write_allowed: bool
    denial_reason: str | None = None

    def __post_init__(self) -> None:
        _require_typed_ref("permit_ref", self.permit_ref, required_prefixes=_ALLOWED_PERMIT_PREFIXES)
        _require_typed_ref("lease_ref", self.lease_ref, required_prefixes=_ALLOWED_LEASE_PREFIXES)
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_typed_ref("writer_ref", self.writer_ref, required_prefixes=_ALLOWED_OWNER_PREFIXES)
        _require_positive_int("context_generation", self.context_generation, allow_zero=False)
        _require_priority(self.priority)
        if self.write_allowed and self.denial_reason is not None:
            raise ValueError("denial_reason must be None when write_allowed is true")
        if not self.write_allowed:
            _require_non_empty("denial_reason", self.denial_reason or "")

    @classmethod
    def from_lease(cls, lease: RouteProxyLease, *, write_allowed: bool, denial_reason: str | None = None) -> "RouteWriterPermit":
        seed = f"{lease.lease_ref}|{lease.route_ref}|{lease.owner_ref}|{lease.context_generation}|{write_allowed}|{denial_reason or ''}"
        return cls(
            permit_ref=f"route-permit:{_stable_suffix(seed)}",
            lease_ref=lease.lease_ref,
            route_ref=lease.route_ref,
            writer_ref=lease.owner_ref,
            context_generation=lease.context_generation,
            priority=lease.priority,
            write_allowed=write_allowed,
            denial_reason=denial_reason,
        )

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _PERMIT_SCHEMA,
            "permit_ref": self.permit_ref,
            "lease_ref": self.lease_ref,
            "route_ref": self.route_ref,
            "writer_ref": self.writer_ref,
            "context_generation": self.context_generation,
            "priority": self.priority,
            "write_allowed": self.write_allowed,
            "denial_reason": self.denial_reason,
            "payload_carried_on_event_bus": False,
        }


@dataclass(frozen=True, slots=True)
class RouteZoneState:
    """Runtime mirror for one /dev/shm zone; not durable authority."""

    zone_ref: str
    dev_shm_path: str
    state: str
    context_generation: int
    active_lease_refs: tuple[str, ...] = ()
    owner_ref: str | None = None
    pressure_level: str = "low"

    def __post_init__(self) -> None:
        _require_typed_ref("zone_ref", self.zone_ref, required_prefixes=("route-zone:",))
        if not self.dev_shm_path.startswith("/dev/shm/autodoc/routes/"):
            raise ValueError("dev_shm_path must start with /dev/shm/autodoc/routes/")
        if ".." in self.dev_shm_path:
            raise ValueError("dev_shm_path must not contain '..'")
        if self.state not in _ALLOWED_ZONE_STATES:
            raise ValueError("state must be one of: " + ", ".join(_ALLOWED_ZONE_STATES))
        _require_positive_int("context_generation", self.context_generation, allow_zero=False)
        object.__setattr__(self, "active_lease_refs", _normalize_refs("active_lease_refs", self.active_lease_refs, allow_empty=True, required_prefixes=_ALLOWED_LEASE_PREFIXES))
        if self.owner_ref is not None:
            _require_typed_ref("owner_ref", self.owner_ref, required_prefixes=_ALLOWED_OWNER_PREFIXES)
        if self.pressure_level not in _ALLOWED_PRESSURE_LEVELS:
            raise ValueError("pressure_level must be one of: " + ", ".join(_ALLOWED_PRESSURE_LEVELS))

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _ZONE_STATE_SCHEMA,
            "zone_ref": self.zone_ref,
            "dev_shm_path": self.dev_shm_path,
            "state": self.state,
            "context_generation": self.context_generation,
            "active_lease_refs": list(self.active_lease_refs),
            "owner_ref": self.owner_ref,
            "pressure_level": self.pressure_level,
            "runtime_mirror_only": True,
            "future_grid_seam": True,
        }


@dataclass(frozen=True, slots=True)
class RouteContextGenerationFence:
    """Fence that invalidates writes from an older context generation."""

    fence_ref: str
    route_root_ref: str
    old_generation: int
    new_generation: int
    stale_route_refs: tuple[str, ...]
    reason: str = "context_generation_changed"

    def __post_init__(self) -> None:
        _require_typed_ref("fence_ref", self.fence_ref, required_prefixes=_ALLOWED_FENCE_PREFIXES)
        _require_typed_ref("route_root_ref", self.route_root_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_positive_int("old_generation", self.old_generation, allow_zero=False)
        _require_positive_int("new_generation", self.new_generation, allow_zero=False)
        if self.new_generation <= self.old_generation:
            raise ValueError("new_generation must be greater than old_generation")
        object.__setattr__(self, "stale_route_refs", _normalize_refs("stale_route_refs", self.stale_route_refs, required_prefixes=_ALLOWED_ROUTE_PREFIXES))
        if self.reason not in _ALLOWED_PRIORITY_REASONS:
            raise ValueError("reason must be one of: " + ", ".join(_ALLOWED_PRIORITY_REASONS))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _GENERATION_FENCE_SCHEMA,
            "fence_ref": self.fence_ref,
            "route_root_ref": self.route_root_ref,
            "old_generation": self.old_generation,
            "new_generation": self.new_generation,
            "stale_route_refs": list(self.stale_route_refs),
            "reason": self.reason,
            "blocks_old_writers_fast": True,
        }


@dataclass(frozen=True, slots=True)
class RoutePriorityHint:
    """Priority hint produced from Scheduler decisions and applied by RouteProxy."""

    hint_ref: str
    route_ref: str
    owner_ref: str
    priority: int
    reason: str

    def __post_init__(self) -> None:
        _require_typed_ref("hint_ref", self.hint_ref, required_prefixes=_ALLOWED_PRIORITY_PREFIXES)
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_typed_ref("owner_ref", self.owner_ref, required_prefixes=_ALLOWED_OWNER_PREFIXES)
        _require_priority(self.priority)
        if self.reason not in _ALLOWED_PRIORITY_REASONS:
            raise ValueError("reason must be one of: " + ", ".join(_ALLOWED_PRIORITY_REASONS))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _PRIORITY_HINT_SCHEMA,
            "hint_ref": self.hint_ref,
            "route_ref": self.route_ref,
            "owner_ref": self.owner_ref,
            "priority": self.priority,
            "reason": self.reason,
            "scheduler_decides_priority": True,
            "route_proxy_applies_fast": True,
        }


@dataclass(frozen=True, slots=True)
class RouteRegistrySnapshot:
    """Runtime mirror snapshot that RouteProxy may publish as observable facts."""

    snapshot_ref: str
    proxy_ref: str
    route_zones: tuple[RouteZoneState, ...]
    leases: tuple[RouteProxyLease, ...] = ()
    mirrored_registry_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("snapshot_ref", self.snapshot_ref, required_prefixes=_ALLOWED_SNAPSHOT_PREFIXES)
        _require_typed_ref("proxy_ref", self.proxy_ref, required_prefixes=("proxy:",))
        if not self.route_zones:
            raise ValueError("route_zones must not be empty")
        object.__setattr__(self, "route_zones", tuple(self.route_zones))
        object.__setattr__(self, "leases", tuple(self.leases))
        object.__setattr__(self, "mirrored_registry_refs", _normalize_refs("mirrored_registry_refs", self.mirrored_registry_refs, allow_empty=True, required_prefixes=_ALLOWED_REGISTRY_REF_PREFIXES))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _REGISTRY_SNAPSHOT_SCHEMA,
            "snapshot_ref": self.snapshot_ref,
            "proxy_ref": self.proxy_ref,
            "route_zones": [zone.to_mapping() for zone in self.route_zones],
            "leases": [lease.to_mapping() for lease in self.leases],
            "mirrored_registry_refs": list(self.mirrored_registry_refs),
            "runtime_mirror_only": True,
            "source_of_truth": "SQLContextStore and declared registries",
            "event_bus_publication_is_observation": True,
        }


@dataclass(frozen=True, slots=True)
class RoutePressureSignal:
    """Signal that a route zone is under pressure and should be throttled or reprioritized."""

    signal_ref: str
    route_ref: str
    pressure_level: str
    pending_writers: int
    estimated_bytes: int
    recommended_action: str

    def __post_init__(self) -> None:
        _require_typed_ref("signal_ref", self.signal_ref, required_prefixes=_ALLOWED_PRESSURE_PREFIXES)
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        if self.pressure_level not in _ALLOWED_PRESSURE_LEVELS:
            raise ValueError("pressure_level must be one of: " + ", ".join(_ALLOWED_PRESSURE_LEVELS))
        _require_positive_int("pending_writers", self.pending_writers, allow_zero=True)
        _require_positive_int("estimated_bytes", self.estimated_bytes, allow_zero=True)
        _require_non_empty("recommended_action", self.recommended_action)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _PRESSURE_SIGNAL_SCHEMA,
            "signal_ref": self.signal_ref,
            "route_ref": self.route_ref,
            "pressure_level": self.pressure_level,
            "pending_writers": self.pending_writers,
            "estimated_bytes": self.estimated_bytes,
            "recommended_action": self.recommended_action,
            "scheduler_may_reprioritize": True,
            "route_proxy_does_not_decide_business_logic": True,
        }


@dataclass(frozen=True, slots=True)
class RouteProxyObservationFact:
    """Bus-ready observation fact emitted by RouteProxy flow control."""

    fact_ref: str
    kind: str
    route_ref: str
    owner_ref: str | None = None
    lease_ref: str | None = None
    context_generation: int | None = None
    count: int = 1
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("fact_ref", self.fact_ref, required_prefixes=_ALLOWED_FACT_PREFIXES)
        if self.kind not in _ALLOWED_FACT_KINDS:
            raise ValueError("kind must be one of: " + ", ".join(_ALLOWED_FACT_KINDS))
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        if self.owner_ref is not None:
            _require_typed_ref("owner_ref", self.owner_ref, required_prefixes=_ALLOWED_OWNER_PREFIXES)
        if self.lease_ref is not None:
            _require_typed_ref("lease_ref", self.lease_ref, required_prefixes=_ALLOWED_LEASE_PREFIXES)
        if self.context_generation is not None:
            _require_positive_int("context_generation", self.context_generation, allow_zero=False)
        _require_positive_int("count", self.count, allow_zero=True)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _OBSERVATION_FACT_SCHEMA,
            "fact_ref": self.fact_ref,
            "kind": self.kind,
            "route_ref": self.route_ref,
            "owner_ref": self.owner_ref,
            "lease_ref": self.lease_ref,
            "context_generation": self.context_generation,
            "count": self.count,
            "metadata": dict(self.metadata),
            "event_bus_role": "observation_only",
            "payload_command": False,
        }


@dataclass(frozen=True, slots=True)
class RouteProxyFlowControlPacket:
    """One immutable packet describing fast RouteProxy control around /dev/shm."""

    packet_ref: str
    lease: RouteProxyLease
    writer_permit: RouteWriterPermit
    zone_state: RouteZoneState
    registry_snapshot: RouteRegistrySnapshot
    observation_facts: tuple[RouteProxyObservationFact, ...]
    priority_hint: RoutePriorityHint | None = None
    generation_fence: RouteContextGenerationFence | None = None
    pressure_signal: RoutePressureSignal | None = None

    def __post_init__(self) -> None:
        _require_typed_ref("packet_ref", self.packet_ref, required_prefixes=("route-proxy:",))
        if self.writer_permit.lease_ref != self.lease.lease_ref:
            raise ValueError("writer_permit must reference packet lease")
        if self.writer_permit.route_ref != self.lease.route_ref:
            raise ValueError("writer_permit route_ref must match lease route_ref")
        if self.zone_state.context_generation != self.lease.context_generation:
            raise ValueError("zone_state context_generation must match lease context_generation")
        if self.zone_state.zone_ref not in self.lease.route_ref and self.lease.route_ref not in self.zone_state.zone_ref:
            # Prefix families differ in normal use; require only same typed route family through path below.
            if not self.zone_state.dev_shm_path.startswith("/dev/shm/autodoc/routes/"):
                raise ValueError("zone_state must describe a /dev/shm route zone")
        object.__setattr__(self, "observation_facts", tuple(self.observation_facts))

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _FLOW_PACKET_SCHEMA,
            "packet_ref": self.packet_ref,
            "lease": self.lease.to_mapping(),
            "writer_permit": self.writer_permit.to_mapping(),
            "zone_state": self.zone_state.to_mapping(),
            "registry_snapshot": self.registry_snapshot.to_mapping(),
            "observation_facts": [fact.to_mapping() for fact in self.observation_facts],
            "priority_hint": None if self.priority_hint is None else self.priority_hint.to_mapping(),
            "generation_fence": None if self.generation_fence is None else self.generation_fence.to_mapping(),
            "pressure_signal": None if self.pressure_signal is None else self.pressure_signal.to_mapping(),
            "scheduler_is_orchestrator": True,
            "route_proxy_is_fast_data_plane_control": True,
            "event_bus_observation_only": True,
            "sql_is_durable_authority": True,
            "dev_shm_future_grid_seam": True,
        }


def build_route_proxy_flow_control_packet(
    *,
    route_ref: str,
    owner_ref: str,
    context_ref: str,
    context_generation: int,
    priority: int,
    dev_shm_path: str,
    write_allowed: bool = True,
    pressure_level: str = "low",
    mirrored_registry_refs: tuple[str, ...] = (),
) -> RouteProxyFlowControlPacket:
    """Build a deterministic RouteProxy flow-control packet without touching /dev/shm."""

    seed = f"{route_ref}|{owner_ref}|{context_ref}|{context_generation}|{priority}|{dev_shm_path}"
    suffix = _stable_suffix(seed)
    lease = RouteProxyLease(
        lease_ref=f"route-lease:{suffix}",
        route_ref=route_ref,
        owner_ref=owner_ref,
        context_ref=context_ref,
        context_generation=context_generation,
        priority=priority,
        state="granted" if write_allowed else "blocked",
        reason="scheduler_priority_changed",
    )
    permit = RouteWriterPermit.from_lease(
        lease,
        write_allowed=write_allowed,
        denial_reason=None if write_allowed else "route_proxy_blocked_writer",
    )
    zone = RouteZoneState(
        zone_ref=f"route-zone:{suffix}",
        dev_shm_path=dev_shm_path,
        state="reserved" if write_allowed else "blocked",
        context_generation=context_generation,
        active_lease_refs=(lease.lease_ref,),
        owner_ref=owner_ref,
        pressure_level=pressure_level,
    )
    snapshot = RouteRegistrySnapshot(
        snapshot_ref=f"route-registry:{suffix}",
        proxy_ref="proxy:route-proxy",
        route_zones=(zone,),
        leases=(lease,),
        mirrored_registry_refs=mirrored_registry_refs,
    )
    priority_hint = RoutePriorityHint(
        hint_ref=f"route-priority:{suffix}",
        route_ref=route_ref,
        owner_ref=owner_ref,
        priority=priority,
        reason="scheduler_priority_changed",
    )
    pressure_signal = RoutePressureSignal(
        signal_ref=f"route-pressure:{suffix}",
        route_ref=route_ref,
        pressure_level=pressure_level,
        pending_writers=0 if write_allowed else 1,
        estimated_bytes=0,
        recommended_action="continue" if write_allowed else "refresh_context_or_wait",
    )
    facts = (
        RouteProxyObservationFact(
            fact_ref=f"route-proxy-fact:lease-{suffix}",
            kind="route.lease_granted" if write_allowed else "route.lease_blocked",
            route_ref=route_ref,
            owner_ref=owner_ref,
            lease_ref=lease.lease_ref,
            context_generation=context_generation,
            metadata=(("route_proxy_role", "fast_dev_shm_flow_control"),),
        ),
        RouteProxyObservationFact(
            fact_ref=f"route-proxy-fact:permit-{suffix}",
            kind="route.writer_permit_granted" if write_allowed else "route.writer_permit_denied",
            route_ref=route_ref,
            owner_ref=owner_ref,
            lease_ref=lease.lease_ref,
            context_generation=context_generation,
        ),
        RouteProxyObservationFact(
            fact_ref=f"route-proxy-fact:snapshot-{suffix}",
            kind="route.registry_snapshot_published",
            route_ref=route_ref,
            owner_ref="proxy:route-proxy",
            context_generation=context_generation,
        ),
    )
    return RouteProxyFlowControlPacket(
        packet_ref=f"route-proxy:{suffix}",
        lease=lease,
        writer_permit=permit,
        zone_state=zone,
        registry_snapshot=snapshot,
        observation_facts=facts,
        priority_hint=priority_hint,
        pressure_signal=pressure_signal,
    )


def build_context_generation_fence(
    *,
    route_root_ref: str,
    old_generation: int,
    new_generation: int,
    stale_route_refs: tuple[str, ...],
) -> RouteContextGenerationFence:
    """Build a deterministic fence that marks old route refs stale."""

    seed = f"{route_root_ref}|{old_generation}|{new_generation}|{'|'.join(stale_route_refs)}"
    return RouteContextGenerationFence(
        fence_ref=f"route-fence:{_stable_suffix(seed)}",
        route_root_ref=route_root_ref,
        old_generation=old_generation,
        new_generation=new_generation,
        stale_route_refs=stale_route_refs,
        reason="context_generation_changed",
    )


def _require_typed_ref(name: str, value: str, *, required_prefixes: tuple[str, ...] | None = None) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed ref")
    if required_prefixes is not None and not value.startswith(required_prefixes):
        raise ValueError(f"{name} must start with one of: {', '.join(required_prefixes)}")


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_positive_int(name: str, value: int, *, allow_zero: bool) -> None:
    if not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if allow_zero:
        if value < 0:
            raise ValueError(f"{name} must be >= 0")
    elif value <= 0:
        raise ValueError(f"{name} must be > 0")


def _require_priority(value: int) -> None:
    _require_positive_int("priority", value, allow_zero=True)
    if value > 10_000:
        raise ValueError("priority must be between 0 and 10000")


def _normalize_refs(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool = False,
    required_prefixes: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    refs = tuple(dict.fromkeys(values))
    if not refs and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    for ref in refs:
        _require_typed_ref(name, ref, required_prefixes=required_prefixes)
    return refs


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized.append((key.strip(), value.strip()))
    return tuple(normalized)


def _stable_suffix(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
