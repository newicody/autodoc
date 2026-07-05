"""Scheduler deliberation route contracts.

0125-r2 locks the deliberation loop around the real kernel authority:
Scheduler is the deliberation orchestrator.  There is no parallel local
orchestrator.  GitHub exchanges artifacts only.  /dev/shm route frames are a
multitask data-plane interface for local workers and a future grid; they are
not context authority.  EventBus observes facts, statistics, and paths, not
payload commands.  E5/OpenVINO is embedding only behind adapter, not decision
maker.  SQLContextStore is durable context authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re

from context.server_oriented_deliberation_cycle import ServerOrientation, SpecialistPreliminaryOpinion

_CYCLE_COMMAND_SCHEMA = "missipy.scheduler.deliberation_cycle_command.v1"
_ROUND_COMMAND_SCHEMA = "missipy.scheduler.deliberation_round_command.v1"
_DISPATCH_COMMAND_SCHEMA = "missipy.scheduler.specialist_dispatch_command.v1"
_ROUTE_REF_SCHEMA = "missipy.route.deliberation_route_ref.v1"
_DEMAND_FRAME_SCHEMA = "missipy.route.specialist_demand_frame.v1"
_OPINION_FRAME_SCHEMA = "missipy.route.specialist_opinion_frame.v1"
_ROUTE_EXCHANGE_SCHEMA = "missipy.route.deliberation_exchange.v1"
_OBSERVATION_FACT_SCHEMA = "missipy.bus.deliberation_observation_fact.v1"
_SCHEDULER_BRIDGE_SCHEMA = "missipy.scheduler.deliberation_bridge.v1"

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_ALLOWED_ARTIFACT_PREFIXES = ("artifact:", "github:")
_ALLOWED_SQL_PREFIXES = ("sql:",)
_ALLOWED_CONTEXT_PREFIXES = ("sql:", "ctx:", "ctx-result:", "ctx-fragment:", "qdrant:", "artifact:")
_ALLOWED_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_ALLOWED_ROUTE_PREFIXES = ("route:",)
_ALLOWED_BUS_PREFIXES = ("bus:", "specialist-path:", "scheduler-trace:")
_ALLOWED_EMBEDDING_PREFIXES = ("openvino:", "e5:", "embedding-model:")
_ALLOWED_COLLECTION_PREFIXES = ("qdrant:", "collection:")
_ALLOWED_COMMAND_PREFIXES = ("command:", "scheduler-command:")
_ALLOWED_STATE_PREFIXES = ("sql:", "ctx:", "cycle-state:")
_ALLOWED_ROUND_STATUS = ("planned", "dispatched", "collecting", "recompiling", "completed", "blocked")
_ALLOWED_FACT_KINDS = (
    "scheduler.dispatched_round",
    "scheduler.dispatched_specialist",
    "route.frame_written",
    "route.frame_consumed",
    "specialist.started",
    "specialist.explored_axis",
    "specialist.requested_context",
    "specialist.proposed_alternative",
    "specialist.requested_peer_review",
    "server.recompiled_opinions",
    "server.refined_demand",
    "cycle.round_completed",
)
_ALLOWED_FRAME_KINDS = ("specialist_demand", "specialist_opinion")
_ALLOWED_DEPTHS = ("shallow", "standard", "deep", "audit")


@dataclass(frozen=True, slots=True)
class DeliberationCycleCommand:
    """Command that asks the Scheduler to orchestrate a deliberation cycle."""

    command_ref: str
    artifact_ref: str
    orientation_ref: str
    sql_cycle_state_ref: str
    route_cycle_root_ref: str
    priority: int = 100
    context_refs: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("command_ref", self.command_ref, required_prefixes=_ALLOWED_COMMAND_PREFIXES)
        _require_typed_ref("artifact_ref", self.artifact_ref, required_prefixes=_ALLOWED_ARTIFACT_PREFIXES)
        _require_typed_ref("orientation_ref", self.orientation_ref, required_prefixes=("orientation:",))
        _require_typed_ref("sql_cycle_state_ref", self.sql_cycle_state_ref, required_prefixes=_ALLOWED_STATE_PREFIXES)
        _require_typed_ref("route_cycle_root_ref", self.route_cycle_root_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        if not 0 <= self.priority <= 10_000:
            raise ValueError("priority must be between 0 and 10000")
        object.__setattr__(self, "context_refs", _normalize_refs("context_refs", self.context_refs, allow_empty=True, required_prefixes=_ALLOWED_CONTEXT_PREFIXES))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @classmethod
    def from_orientation(
        cls,
        orientation: ServerOrientation,
        *,
        command_ref: str | None = None,
        route_cycle_root_ref: str | None = None,
        priority: int = 100,
    ) -> "DeliberationCycleCommand":
        seed = f"{orientation.orientation_ref}|{orientation.artifact_ref}|{orientation.sql_context_ref}"
        stable = _stable_suffix(seed)
        return cls(
            command_ref=command_ref or f"scheduler-command:deliberation-cycle-{stable}",
            artifact_ref=orientation.artifact_ref,
            orientation_ref=orientation.orientation_ref,
            sql_cycle_state_ref=f"cycle-state:{stable}",
            route_cycle_root_ref=route_cycle_root_ref or f"route:deliberation/{stable}",
            priority=priority,
            context_refs=(orientation.sql_context_ref, *orientation.context_refs),
            metadata=(("scheduler_role", "orchestrator"), ("github_role", "artifact_exchange_only")),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _CYCLE_COMMAND_SCHEMA,
            "command_ref": self.command_ref,
            "artifact_ref": self.artifact_ref,
            "orientation_ref": self.orientation_ref,
            "sql_cycle_state_ref": self.sql_cycle_state_ref,
            "route_cycle_root_ref": self.route_cycle_root_ref,
            "priority": self.priority,
            "context_refs": list(self.context_refs),
            "metadata": dict(self.metadata),
            "scheduler_orchestrates": True,
            "parallel_local_orchestrator": False,
            "github_exchange_role": "artifact exchange only",
        }


@dataclass(frozen=True, slots=True)
class DeliberationRouteRef:
    """Typed reference to a /dev/shm route frame or route directory."""

    route_ref: str
    dev_shm_path: str
    frame_kind: str
    cycle_id: str
    round_id: str | None = None
    specialist_ref: str | None = None

    def __post_init__(self) -> None:
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        if not self.dev_shm_path.startswith("/dev/shm/autodoc/routes/"):
            raise ValueError("dev_shm_path must start with /dev/shm/autodoc/routes/")
        if ".." in self.dev_shm_path:
            raise ValueError("dev_shm_path must not contain '..'")
        if self.frame_kind not in _ALLOWED_FRAME_KINDS and self.frame_kind != "cycle_root":
            raise ValueError("frame_kind must be specialist_demand, specialist_opinion, or cycle_root")
        _require_slug("cycle_id", self.cycle_id)
        if self.round_id is not None:
            _require_slug("round_id", self.round_id)
        if self.specialist_ref is not None:
            _require_typed_ref("specialist_ref", self.specialist_ref, required_prefixes=_ALLOWED_SPECIALIST_PREFIXES)

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _ROUTE_REF_SCHEMA,
            "route_ref": self.route_ref,
            "dev_shm_path": self.dev_shm_path,
            "frame_kind": self.frame_kind,
            "cycle_id": self.cycle_id,
            "round_id": self.round_id,
            "specialist_ref": self.specialist_ref,
            "data_plane": "dev_shm_multitask_interface",
            "durable_authority": False,
        }


@dataclass(frozen=True, slots=True)
class DeliberationRoundCommand:
    """Scheduler command for one deliberation round."""

    command_ref: str
    cycle_command_ref: str
    orientation_ref: str
    round_id: str
    route_round_ref: str
    sql_cycle_state_ref: str
    expected_specialist_refs: tuple[str, ...]
    status: str = "planned"

    def __post_init__(self) -> None:
        _require_typed_ref("command_ref", self.command_ref, required_prefixes=_ALLOWED_COMMAND_PREFIXES)
        _require_typed_ref("cycle_command_ref", self.cycle_command_ref, required_prefixes=_ALLOWED_COMMAND_PREFIXES)
        _require_typed_ref("orientation_ref", self.orientation_ref, required_prefixes=("orientation:",))
        _require_slug("round_id", self.round_id)
        _require_typed_ref("route_round_ref", self.route_round_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_typed_ref("sql_cycle_state_ref", self.sql_cycle_state_ref, required_prefixes=_ALLOWED_STATE_PREFIXES)
        object.__setattr__(
            self,
            "expected_specialist_refs",
            _normalize_refs("expected_specialist_refs", self.expected_specialist_refs, required_prefixes=_ALLOWED_SPECIALIST_PREFIXES),
        )
        if self.status not in _ALLOWED_ROUND_STATUS:
            raise ValueError("status must be one of: " + ", ".join(_ALLOWED_ROUND_STATUS))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _ROUND_COMMAND_SCHEMA,
            "command_ref": self.command_ref,
            "cycle_command_ref": self.cycle_command_ref,
            "orientation_ref": self.orientation_ref,
            "round_id": self.round_id,
            "route_round_ref": self.route_round_ref,
            "sql_cycle_state_ref": self.sql_cycle_state_ref,
            "expected_specialist_refs": list(self.expected_specialist_refs),
            "status": self.status,
            "handled_by_scheduler_chain": True,
        }


@dataclass(frozen=True, slots=True)
class SpecialistDispatchCommand:
    """Scheduler command that dispatches one specialist to one route demand frame."""

    command_ref: str
    round_command_ref: str
    specialist_ref: str
    demand_route_ref: str
    expected_opinion_route_ref: str
    bus_topic_ref: str

    def __post_init__(self) -> None:
        _require_typed_ref("command_ref", self.command_ref, required_prefixes=_ALLOWED_COMMAND_PREFIXES)
        _require_typed_ref("round_command_ref", self.round_command_ref, required_prefixes=_ALLOWED_COMMAND_PREFIXES)
        _require_typed_ref("specialist_ref", self.specialist_ref, required_prefixes=_ALLOWED_SPECIALIST_PREFIXES)
        _require_typed_ref("demand_route_ref", self.demand_route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_typed_ref("expected_opinion_route_ref", self.expected_opinion_route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_typed_ref("bus_topic_ref", self.bus_topic_ref, required_prefixes=_ALLOWED_BUS_PREFIXES)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _DISPATCH_COMMAND_SCHEMA,
            "command_ref": self.command_ref,
            "round_command_ref": self.round_command_ref,
            "specialist_ref": self.specialist_ref,
            "demand_route_ref": self.demand_route_ref,
            "expected_opinion_route_ref": self.expected_opinion_route_ref,
            "bus_topic_ref": self.bus_topic_ref,
            "scheduler_orchestrates_dispatch": True,
            "payload_in_event_bus": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistDemandFrame:
    """Frame written to /dev/shm for a specialist worker."""

    frame_ref: str
    route_ref: str
    cycle_command_ref: str
    round_command_ref: str
    specialist_ref: str
    request_text: str
    context_refs: tuple[str, ...]
    embedding_model_ref: str = "openvino:e5-small"
    qdrant_collection_ref: str = "qdrant:autodoc-context"
    expected_output: str = "preliminary_opinion"
    depth: str = "standard"

    def __post_init__(self) -> None:
        _require_typed_ref("frame_ref", self.frame_ref, required_prefixes=("route-frame:",))
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_typed_ref("cycle_command_ref", self.cycle_command_ref, required_prefixes=_ALLOWED_COMMAND_PREFIXES)
        _require_typed_ref("round_command_ref", self.round_command_ref, required_prefixes=_ALLOWED_COMMAND_PREFIXES)
        _require_typed_ref("specialist_ref", self.specialist_ref, required_prefixes=_ALLOWED_SPECIALIST_PREFIXES)
        _require_non_empty("request_text", self.request_text)
        object.__setattr__(self, "context_refs", _normalize_refs("context_refs", self.context_refs, required_prefixes=_ALLOWED_CONTEXT_PREFIXES))
        _require_typed_ref("embedding_model_ref", self.embedding_model_ref, required_prefixes=_ALLOWED_EMBEDDING_PREFIXES)
        _require_typed_ref("qdrant_collection_ref", self.qdrant_collection_ref, required_prefixes=_ALLOWED_COLLECTION_PREFIXES)
        _require_non_empty("expected_output", self.expected_output)
        if self.depth not in _ALLOWED_DEPTHS:
            raise ValueError("depth must be shallow, standard, deep, or audit")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _DEMAND_FRAME_SCHEMA,
            "frame_type": "specialist_demand",
            "frame_ref": self.frame_ref,
            "route_ref": self.route_ref,
            "cycle_command_ref": self.cycle_command_ref,
            "round_command_ref": self.round_command_ref,
            "specialist_ref": self.specialist_ref,
            "request_text": self.request_text,
            "context_refs": list(self.context_refs),
            "embedding_model_ref": self.embedding_model_ref,
            "qdrant_collection_ref": self.qdrant_collection_ref,
            "expected_output": self.expected_output,
            "depth": self.depth,
            "e5_role": "embedding only",
            "decision_maker": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistOpinionFrame:
    """Frame written by a specialist worker after reading a demand frame."""

    frame_ref: str
    route_ref: str
    demand_frame_ref: str
    specialist_ref: str
    opinion_ref: str
    stance: str
    summary: str
    context_delta_refs: tuple[str, ...] = ()
    observation_fact_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("frame_ref", self.frame_ref, required_prefixes=("route-frame:",))
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_typed_ref("demand_frame_ref", self.demand_frame_ref, required_prefixes=("route-frame:",))
        _require_typed_ref("specialist_ref", self.specialist_ref, required_prefixes=_ALLOWED_SPECIALIST_PREFIXES)
        _require_typed_ref("opinion_ref", self.opinion_ref, required_prefixes=("specialist-opinion:",))
        _require_non_empty("stance", self.stance)
        _require_non_empty("summary", self.summary)
        object.__setattr__(self, "context_delta_refs", _normalize_refs("context_delta_refs", self.context_delta_refs, allow_empty=True, required_prefixes=("ctx:", "ctx-result:", "sql:")))
        object.__setattr__(self, "observation_fact_refs", _normalize_refs("observation_fact_refs", self.observation_fact_refs, allow_empty=True, required_prefixes=_ALLOWED_BUS_PREFIXES))

    @classmethod
    def from_preliminary_opinion(
        cls,
        opinion: SpecialistPreliminaryOpinion,
        *,
        demand_frame_ref: str,
        route_ref: str,
        frame_ref: str | None = None,
    ) -> "SpecialistOpinionFrame":
        suffix = _stable_suffix(f"{opinion.opinion_ref}|{route_ref}|{demand_frame_ref}")
        return cls(
            frame_ref=frame_ref or f"route-frame:opinion-{suffix}",
            route_ref=route_ref,
            demand_frame_ref=demand_frame_ref,
            specialist_ref=opinion.specialist_ref,
            opinion_ref=opinion.opinion_ref,
            stance=opinion.stance,
            summary=opinion.summary,
            context_delta_refs=opinion.context_delta_refs,
            observation_fact_refs=opinion.bus_observation_refs,
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _OPINION_FRAME_SCHEMA,
            "frame_type": "specialist_opinion",
            "frame_ref": self.frame_ref,
            "route_ref": self.route_ref,
            "demand_frame_ref": self.demand_frame_ref,
            "specialist_ref": self.specialist_ref,
            "opinion_ref": self.opinion_ref,
            "stance": self.stance,
            "summary": self.summary,
            "context_delta_refs": list(self.context_delta_refs),
            "observation_fact_refs": list(self.observation_fact_refs),
            "validated_as_final_solution": False,
        }


@dataclass(frozen=True, slots=True)
class DeliberationRouteExchange:
    """Set of route refs that connect one round to specialists."""

    exchange_ref: str
    round_command_ref: str
    demand_routes: tuple[DeliberationRouteRef, ...]
    opinion_routes: tuple[DeliberationRouteRef, ...]

    def __post_init__(self) -> None:
        _require_typed_ref("exchange_ref", self.exchange_ref, required_prefixes=("route-exchange:",))
        _require_typed_ref("round_command_ref", self.round_command_ref, required_prefixes=_ALLOWED_COMMAND_PREFIXES)
        if not self.demand_routes:
            raise ValueError("demand_routes must not be empty")
        if not self.opinion_routes:
            raise ValueError("opinion_routes must not be empty")
        object.__setattr__(self, "demand_routes", tuple(self.demand_routes))
        object.__setattr__(self, "opinion_routes", tuple(self.opinion_routes))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _ROUTE_EXCHANGE_SCHEMA,
            "exchange_ref": self.exchange_ref,
            "round_command_ref": self.round_command_ref,
            "demand_routes": [route.to_mapping() for route in self.demand_routes],
            "opinion_routes": [route.to_mapping() for route in self.opinion_routes],
            "dev_shm_role": "multitask data-plane interface",
            "future_grid_extension": True,
            "durable_authority": "SQLContextStore",
        }


@dataclass(frozen=True, slots=True)
class DeliberationObservationFact:
    """Bus-ready observation fact derived from scheduler/route/specialist activity."""

    fact_ref: str
    kind: str
    cycle_ref: str
    route_ref: str | None = None
    specialist_ref: str | None = None
    count: int = 1
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("fact_ref", self.fact_ref, required_prefixes=_ALLOWED_BUS_PREFIXES)
        if self.kind not in _ALLOWED_FACT_KINDS:
            raise ValueError("kind must be one of: " + ", ".join(_ALLOWED_FACT_KINDS))
        _require_typed_ref("cycle_ref", self.cycle_ref, required_prefixes=_ALLOWED_COMMAND_PREFIXES + _ALLOWED_STATE_PREFIXES)
        if self.route_ref is not None:
            _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        if self.specialist_ref is not None:
            _require_typed_ref("specialist_ref", self.specialist_ref, required_prefixes=_ALLOWED_SPECIALIST_PREFIXES)
        if self.count < 0:
            raise ValueError("count must be >= 0")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _OBSERVATION_FACT_SCHEMA,
            "fact_ref": self.fact_ref,
            "kind": self.kind,
            "cycle_ref": self.cycle_ref,
            "route_ref": self.route_ref,
            "specialist_ref": self.specialist_ref,
            "count": self.count,
            "metadata": dict(self.metadata),
            "event_bus_role": "observation_only",
            "command": False,
            "payload_ref_only": True,
        }


@dataclass(frozen=True, slots=True)
class SchedulerDeliberationRouteBridge:
    """Immutable bridge packet used by handlers to connect Scheduler and routes."""

    bridge_ref: str
    cycle_command: DeliberationCycleCommand
    round_command: DeliberationRoundCommand
    dispatch_commands: tuple[SpecialistDispatchCommand, ...]
    route_exchange: DeliberationRouteExchange
    observation_facts: tuple[DeliberationObservationFact, ...]

    def __post_init__(self) -> None:
        _require_typed_ref("bridge_ref", self.bridge_ref, required_prefixes=("scheduler-bridge:",))
        if not self.dispatch_commands:
            raise ValueError("dispatch_commands must not be empty")
        object.__setattr__(self, "dispatch_commands", tuple(self.dispatch_commands))
        object.__setattr__(self, "observation_facts", tuple(self.observation_facts))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _SCHEDULER_BRIDGE_SCHEMA,
            "bridge_ref": self.bridge_ref,
            "cycle_command": self.cycle_command.to_mapping(),
            "round_command": self.round_command.to_mapping(),
            "dispatch_commands": [command.to_mapping() for command in self.dispatch_commands],
            "route_exchange": self.route_exchange.to_mapping(),
            "observation_facts": [fact.to_mapping() for fact in self.observation_facts],
            "scheduler_is_orchestrator": True,
            "dev_shm_is_multitask_interface": True,
            "event_bus_observation_only": True,
            "github_artifact_exchange_only": True,
            "e5_embedding_only": True,
        }


def build_scheduler_deliberation_route_bridge(
    orientation: ServerOrientation,
    *,
    round_id: str = "round-0001",
    request_template: str = "Produce a preliminary opinion for the server deliberation round.",
) -> SchedulerDeliberationRouteBridge:
    """Build a deterministic bridge packet without touching the live Scheduler."""

    cycle_command = DeliberationCycleCommand.from_orientation(orientation)
    stable = _stable_suffix(f"{cycle_command.command_ref}|{round_id}")
    route_round_ref = f"route:deliberation/{stable}/{round_id}"
    round_command = DeliberationRoundCommand(
        command_ref=f"scheduler-command:deliberation-round-{stable}",
        cycle_command_ref=cycle_command.command_ref,
        orientation_ref=orientation.orientation_ref,
        round_id=round_id,
        route_round_ref=route_round_ref,
        sql_cycle_state_ref=cycle_command.sql_cycle_state_ref,
        expected_specialist_refs=orientation.requested_specialist_refs,
    )
    demand_routes: list[DeliberationRouteRef] = []
    opinion_routes: list[DeliberationRouteRef] = []
    dispatch_commands: list[SpecialistDispatchCommand] = []
    facts: list[DeliberationObservationFact] = [
        DeliberationObservationFact(
            fact_ref=f"scheduler-trace:round-dispatched-{stable}",
            kind="scheduler.dispatched_round",
            cycle_ref=cycle_command.command_ref,
            route_ref=route_round_ref,
        )
    ]
    for index, specialist_ref in enumerate(orientation.requested_specialist_refs, start=1):
        specialist_slug = _ref_slug(specialist_ref)
        demand_route_ref = f"route:deliberation/{stable}/{round_id}/demand-{specialist_slug}"
        opinion_route_ref = f"route:deliberation/{stable}/{round_id}/opinion-{specialist_slug}"
        demand_routes.append(
            DeliberationRouteRef(
                route_ref=demand_route_ref,
                dev_shm_path=f"/dev/shm/autodoc/routes/deliberation/{stable}/{round_id}/demand-{specialist_slug}.frame",
                frame_kind="specialist_demand",
                cycle_id=stable,
                round_id=round_id,
                specialist_ref=specialist_ref,
            )
        )
        opinion_routes.append(
            DeliberationRouteRef(
                route_ref=opinion_route_ref,
                dev_shm_path=f"/dev/shm/autodoc/routes/deliberation/{stable}/{round_id}/opinion-{specialist_slug}.frame",
                frame_kind="specialist_opinion",
                cycle_id=stable,
                round_id=round_id,
                specialist_ref=specialist_ref,
            )
        )
        dispatch_commands.append(
            SpecialistDispatchCommand(
                command_ref=f"scheduler-command:specialist-dispatch-{stable}-{index:02d}",
                round_command_ref=round_command.command_ref,
                specialist_ref=specialist_ref,
                demand_route_ref=demand_route_ref,
                expected_opinion_route_ref=opinion_route_ref,
                bus_topic_ref=f"bus:deliberation/{stable}/{round_id}/{specialist_slug}",
            )
        )
        facts.append(
            DeliberationObservationFact(
                fact_ref=f"scheduler-trace:specialist-dispatched-{stable}-{index:02d}",
                kind="scheduler.dispatched_specialist",
                cycle_ref=cycle_command.command_ref,
                route_ref=demand_route_ref,
                specialist_ref=specialist_ref,
                metadata=(("request_template", request_template),),
            )
        )
    exchange = DeliberationRouteExchange(
        exchange_ref=f"route-exchange:deliberation-{stable}-{round_id}",
        round_command_ref=round_command.command_ref,
        demand_routes=tuple(demand_routes),
        opinion_routes=tuple(opinion_routes),
    )
    return SchedulerDeliberationRouteBridge(
        bridge_ref=f"scheduler-bridge:deliberation-{stable}-{round_id}",
        cycle_command=cycle_command,
        round_command=round_command,
        dispatch_commands=tuple(dispatch_commands),
        route_exchange=exchange,
        observation_facts=tuple(facts),
    )


def build_specialist_demand_frames(
    bridge: SchedulerDeliberationRouteBridge,
    *,
    request_text_by_specialist: dict[str, str] | None = None,
) -> tuple[SpecialistDemandFrame, ...]:
    """Create /dev/shm demand frame payloads from a bridge packet."""

    texts = request_text_by_specialist or {}
    frames: list[SpecialistDemandFrame] = []
    for command in bridge.dispatch_commands:
        text = texts.get(command.specialist_ref, "Produce a preliminary opinion for this deliberation round.")
        frames.append(
            SpecialistDemandFrame(
                frame_ref=f"route-frame:demand-{_stable_suffix(command.demand_route_ref)}",
                route_ref=command.demand_route_ref,
                cycle_command_ref=bridge.cycle_command.command_ref,
                round_command_ref=bridge.round_command.command_ref,
                specialist_ref=command.specialist_ref,
                request_text=text,
                context_refs=bridge.cycle_command.context_refs,
            )
        )
    return tuple(frames)


def _require_typed_ref(name: str, value: str, *, required_prefixes: tuple[str, ...] | None = None) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed ref")
    if required_prefixes is not None and not value.startswith(required_prefixes):
        raise ValueError(f"{name} must start with one of: {', '.join(required_prefixes)}")


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _require_slug(name: str, value: str) -> None:
    if not isinstance(value, str) or not re.match(r"^[a-z0-9][a-z0-9_.-]*$", value):
        raise ValueError(f"{name} must be a stable slug")


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


def _ref_slug(ref: str) -> str:
    return re.sub(r"[^a-z0-9_.-]+", "-", ref.split(":", 1)[1].lower()).strip("-") or "specialist"
