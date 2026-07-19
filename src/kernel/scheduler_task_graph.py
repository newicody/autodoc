from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import hashlib
import re

from kernel.scheduler_task_model import (
    SchedulerTask,
    SchedulerTaskMutation,
    SchedulerTaskState,
)


_SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_READY_SOURCE_STATES = frozenset(
    {
        SchedulerTaskState.PLANNED,
        SchedulerTaskState.PAUSED,
        SchedulerTaskState.RETRY_WAIT,
    }
)


class SchedulerTaskGraphError(ValueError):
    """Erreur de contrat du graphe de tâches Scheduler."""


class SchedulerTaskBarrierKind(str, Enum):
    """Condition collective imposée avant une tâche cible."""

    ALL_SUCCEEDED = "all-succeeded"
    ALL_TERMINAL = "all-terminal"


class SchedulerTaskBranchCondition(str, Enum):
    """Condition d'une branche sur l'état durable d'une tâche source."""

    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed-out"
    TERMINAL = "terminal"

    def satisfied_by(self, state: SchedulerTaskState) -> bool:
        if self is SchedulerTaskBranchCondition.TERMINAL:
            return state.terminal
        expected = {
            SchedulerTaskBranchCondition.COMPLETED: SchedulerTaskState.COMPLETED,
            SchedulerTaskBranchCondition.FAILED: SchedulerTaskState.FAILED,
            SchedulerTaskBranchCondition.CANCELLED: SchedulerTaskState.CANCELLED,
            SchedulerTaskBranchCondition.TIMED_OUT: SchedulerTaskState.TIMED_OUT,
        }[self]
        return state is expected


class SchedulerTaskBranchMode(str, Enum):
    """Agrégation des règles d'une porte de branche."""

    ANY = "any"
    ALL = "all"


@dataclass(frozen=True, slots=True)
class SchedulerTaskBarrier:
    """Barrière nommée entre plusieurs prédécesseurs et une tâche cible."""

    barrier_ref: str
    target_task_ref: str
    member_task_refs: tuple[str, ...]
    kind: SchedulerTaskBarrierKind

    def __post_init__(self) -> None:
        _require_typed_ref("barrier_ref", self.barrier_ref, "scheduler-barrier:")
        _require_typed_ref("target_task_ref", self.target_task_ref, "scheduler-task:")
        members = _validated_task_refs("member_task_refs", self.member_task_refs)
        if self.target_task_ref in members:
            raise SchedulerTaskGraphError("une barrière ne peut cibler l'un de ses membres")
        object.__setattr__(self, "member_task_refs", members)

    def satisfied_by(self, states: Mapping[str, SchedulerTaskState]) -> bool:
        if any(task_ref not in states for task_ref in self.member_task_refs):
            return False
        if self.kind is SchedulerTaskBarrierKind.ALL_SUCCEEDED:
            return all(
                states[task_ref] is SchedulerTaskState.COMPLETED
                for task_ref in self.member_task_refs
            )
        return all(states[task_ref].terminal for task_ref in self.member_task_refs)


@dataclass(frozen=True, slots=True)
class SchedulerTaskBranchRule:
    """Règle élémentaire d'activation d'une branche."""

    source_task_ref: str
    condition: SchedulerTaskBranchCondition

    def __post_init__(self) -> None:
        _require_typed_ref("source_task_ref", self.source_task_ref, "scheduler-task:")

    def satisfied_by(self, states: Mapping[str, SchedulerTaskState]) -> bool:
        state = states.get(self.source_task_ref)
        return state is not None and self.condition.satisfied_by(state)


@dataclass(frozen=True, slots=True)
class SchedulerTaskBranchGate:
    """Porte conditionnelle explicite appliquée à une tâche cible."""

    gate_ref: str
    target_task_ref: str
    mode: SchedulerTaskBranchMode
    rules: tuple[SchedulerTaskBranchRule, ...]

    def __post_init__(self) -> None:
        _require_typed_ref("gate_ref", self.gate_ref, "scheduler-branch-gate:")
        _require_typed_ref("target_task_ref", self.target_task_ref, "scheduler-task:")
        rules = tuple(self.rules)
        if not rules:
            raise SchedulerTaskGraphError("une porte de branche exige au moins une règle")
        identities = {(rule.source_task_ref, rule.condition.value) for rule in rules}
        if len(identities) != len(rules):
            raise SchedulerTaskGraphError("une porte de branche contient une règle dupliquée")
        if any(rule.source_task_ref == self.target_task_ref for rule in rules):
            raise SchedulerTaskGraphError("une porte de branche ne peut dépendre de sa cible")
        object.__setattr__(self, "rules", rules)

    def satisfied_by(self, states: Mapping[str, SchedulerTaskState]) -> bool:
        outcomes = tuple(rule.satisfied_by(states) for rule in self.rules)
        if self.mode is SchedulerTaskBranchMode.ALL:
            return all(outcomes)
        return any(outcomes)


@dataclass(frozen=True, slots=True)
class SchedulerTaskReadiness:
    """Évaluation déterministe d'une tâche sans transition d'état."""

    task_ref: str
    ready: bool
    dependency_blocked: bool
    barrier_refs_blocking: tuple[str, ...]
    branch_gate_refs_blocking: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")
        if not isinstance(self.ready, bool) or not isinstance(self.dependency_blocked, bool):
            raise SchedulerTaskGraphError("les indicateurs de readiness doivent être booléens")
        _validated_refs("barrier_refs_blocking", self.barrier_refs_blocking)
        _validated_refs("branch_gate_refs_blocking", self.branch_gate_refs_blocking)
        expected_ready = not (
            self.dependency_blocked
            or self.barrier_refs_blocking
            or self.branch_gate_refs_blocking
        )
        if self.ready is not expected_ready:
            raise SchedulerTaskGraphError("l'indicateur ready est incohérent")


@dataclass(frozen=True, slots=True)
class SchedulerTaskReadinessPlan:
    """Plan pur et ordonné des tâches pouvant devenir ready."""

    graph_ref: str
    graph_version: int
    evaluations: tuple[SchedulerTaskReadiness, ...]
    ready_task_refs: tuple[str, ...]
    plan_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref("graph_ref", self.graph_ref, "scheduler-task-graph:")
        _require_positive_int("graph_version", self.graph_version)
        refs = tuple(item.task_ref for item in self.evaluations if item.ready)
        if refs != self.ready_task_refs:
            raise SchedulerTaskGraphError("ready_task_refs diverge des évaluations")
        _require_sha256("plan_digest", self.plan_digest)
        expected = _readiness_plan_digest(
            graph_ref=self.graph_ref,
            graph_version=self.graph_version,
            evaluations=self.evaluations,
        )
        if self.plan_digest != expected:
            raise SchedulerTaskGraphError("plan_digest incohérent")


@dataclass(frozen=True, slots=True)
class SchedulerTaskGraph:
    """Graphe immuable de tâches appartenant à une commande Scheduler."""

    graph_ref: str
    command_ref: str
    graph_version: int
    created_at: str
    updated_at: str
    tasks: tuple[SchedulerTask, ...]
    barriers: tuple[SchedulerTaskBarrier, ...]
    branch_gates: tuple[SchedulerTaskBranchGate, ...]
    graph_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref("graph_ref", self.graph_ref, "scheduler-task-graph:")
        _require_typed_ref("command_ref", self.command_ref, "scheduler-command:")
        _require_positive_int("graph_version", self.graph_version)
        _require_utc("created_at", self.created_at)
        _require_utc("updated_at", self.updated_at)
        tasks = tuple(self.tasks)
        if not tasks:
            raise SchedulerTaskGraphError("un graphe exige au moins une tâche")
        task_refs = tuple(task.task_ref for task in tasks)
        if len(set(task_refs)) != len(task_refs):
            raise SchedulerTaskGraphError("le graphe contient une task_ref dupliquée")
        if any(task.command_ref != self.command_ref for task in tasks):
            raise SchedulerTaskGraphError("toutes les tâches doivent partager command_ref")
        known = frozenset(task_refs)
        for task in tasks:
            if task.parent_task_ref and task.parent_task_ref not in known:
                raise SchedulerTaskGraphError("parent_task_ref absent du graphe")
            if any(dependency.task_ref not in known for dependency in task.dependencies):
                raise SchedulerTaskGraphError("une dépendance référence une tâche absente")
        barriers = tuple(self.barriers)
        branch_gates = tuple(self.branch_gates)
        _require_unique_refs("barrier_ref", tuple(item.barrier_ref for item in barriers))
        _require_unique_refs("gate_ref", tuple(item.gate_ref for item in branch_gates))
        for barrier in barriers:
            if barrier.target_task_ref not in known:
                raise SchedulerTaskGraphError("une barrière cible une tâche absente")
            if any(member not in known for member in barrier.member_task_refs):
                raise SchedulerTaskGraphError("une barrière référence une tâche absente")
        for gate in branch_gates:
            if gate.target_task_ref not in known:
                raise SchedulerTaskGraphError("une porte de branche cible une tâche absente")
            if any(rule.source_task_ref not in known for rule in gate.rules):
                raise SchedulerTaskGraphError("une branche référence une tâche absente")
        object.__setattr__(self, "tasks", tasks)
        object.__setattr__(self, "barriers", barriers)
        object.__setattr__(self, "branch_gates", branch_gates)
        _assert_acyclic(tasks=tasks, barriers=barriers, branch_gates=branch_gates)
        _require_sha256("graph_digest", self.graph_digest)
        expected = _graph_digest(
            graph_ref=self.graph_ref,
            command_ref=self.command_ref,
            graph_version=self.graph_version,
            created_at=self.created_at,
            updated_at=self.updated_at,
            tasks=self.tasks,
            barriers=self.barriers,
            branch_gates=self.branch_gates,
        )
        if self.graph_digest != expected:
            raise SchedulerTaskGraphError("graph_digest incohérent")

    @classmethod
    def create(
        cls,
        *,
        graph_ref: str,
        command_ref: str,
        created_at: str,
        tasks: Sequence[SchedulerTask],
        barriers: Sequence[SchedulerTaskBarrier] = (),
        branch_gates: Sequence[SchedulerTaskBranchGate] = (),
    ) -> SchedulerTaskGraph:
        values = dict(
            graph_ref=graph_ref,
            command_ref=command_ref,
            graph_version=1,
            created_at=created_at,
            updated_at=created_at,
            tasks=tuple(tasks),
            barriers=tuple(barriers),
            branch_gates=tuple(branch_gates),
        )
        return cls(graph_digest=_graph_digest(**values), **values)

    def task(self, task_ref: str) -> SchedulerTask:
        for task in self.tasks:
            if task.task_ref == task_ref:
                return task
        raise SchedulerTaskGraphError(f"tâche absente: {task_ref}")

    def readiness_plan(self) -> SchedulerTaskReadinessPlan:
        states = {task.task_ref: task.state for task in self.tasks}
        candidates = tuple(task for task in self.tasks if task.state in _READY_SOURCE_STATES)
        ordered = tuple(
            sorted(
                candidates,
                key=lambda task: (
                    -task.effective_priority,
                    task.created_at,
                    task.task_ref,
                ),
            )
        )
        evaluations: list[SchedulerTaskReadiness] = []
        for task in ordered:
            dependency_blocked = not task.dependencies_satisfied(states)
            barrier_refs_blocking = tuple(
                barrier.barrier_ref
                for barrier in self.barriers
                if barrier.target_task_ref == task.task_ref
                and not barrier.satisfied_by(states)
            )
            branch_gate_refs_blocking = tuple(
                gate.gate_ref
                for gate in self.branch_gates
                if gate.target_task_ref == task.task_ref
                and not gate.satisfied_by(states)
            )
            evaluations.append(
                SchedulerTaskReadiness(
                    task_ref=task.task_ref,
                    ready=not (
                        dependency_blocked
                        or barrier_refs_blocking
                        or branch_gate_refs_blocking
                    ),
                    dependency_blocked=dependency_blocked,
                    barrier_refs_blocking=barrier_refs_blocking,
                    branch_gate_refs_blocking=branch_gate_refs_blocking,
                )
            )
        values = tuple(evaluations)
        return SchedulerTaskReadinessPlan(
            graph_ref=self.graph_ref,
            graph_version=self.graph_version,
            evaluations=values,
            ready_task_refs=tuple(item.task_ref for item in values if item.ready),
            plan_digest=_readiness_plan_digest(
                graph_ref=self.graph_ref,
                graph_version=self.graph_version,
                evaluations=values,
            ),
        )

    def promote_ready(
        self,
        *,
        occurred_at: str,
        actor_ref: str,
        cause_ref: str,
    ) -> SchedulerTaskGraphPromotion:
        plan = self.readiness_plan()
        if not plan.ready_task_refs:
            return SchedulerTaskGraphPromotion(
                graph=self,
                plan=plan,
                mutations=(),
                changed=False,
            )
        states = {task.task_ref: task.state for task in self.tasks}
        by_ref = {task.task_ref: task for task in self.tasks}
        mutations: list[SchedulerTaskMutation] = []
        for task_ref in plan.ready_task_refs:
            mutation = by_ref[task_ref].mark_ready(
                dependency_states=states,
                occurred_at=occurred_at,
                actor_ref=actor_ref,
                cause_ref=cause_ref,
            )
            by_ref[task_ref] = mutation.task
            mutations.append(mutation)
        updated_tasks = tuple(by_ref[task.task_ref] for task in self.tasks)
        values = dict(
            graph_ref=self.graph_ref,
            command_ref=self.command_ref,
            graph_version=self.graph_version + 1,
            created_at=self.created_at,
            updated_at=occurred_at,
            tasks=updated_tasks,
            barriers=self.barriers,
            branch_gates=self.branch_gates,
        )
        graph = SchedulerTaskGraph(graph_digest=_graph_digest(**values), **values)
        return SchedulerTaskGraphPromotion(
            graph=graph,
            plan=plan,
            mutations=tuple(mutations),
            changed=True,
        )


@dataclass(frozen=True, slots=True)
class SchedulerTaskGraphPromotion:
    """Résultat pur de la promotion des tâches vers ready."""

    graph: SchedulerTaskGraph
    plan: SchedulerTaskReadinessPlan
    mutations: tuple[SchedulerTaskMutation, ...]
    changed: bool

    def __post_init__(self) -> None:
        if not isinstance(self.changed, bool):
            raise SchedulerTaskGraphError("changed doit être booléen")
        mutation_refs = tuple(item.task.task_ref for item in self.mutations)
        if mutation_refs != self.plan.ready_task_refs:
            raise SchedulerTaskGraphError("les mutations divergent du plan de readiness")
        if self.changed is not bool(self.mutations):
            raise SchedulerTaskGraphError("changed diverge des mutations")
        if self.changed:
            if self.graph.graph_version != self.plan.graph_version + 1:
                raise SchedulerTaskGraphError("la promotion doit incrémenter graph_version")
        elif self.graph.graph_version != self.plan.graph_version:
            raise SchedulerTaskGraphError("un graphe inchangé conserve graph_version")


def _assert_acyclic(
    *,
    tasks: Sequence[SchedulerTask],
    barriers: Sequence[SchedulerTaskBarrier],
    branch_gates: Sequence[SchedulerTaskBranchGate],
) -> None:
    adjacency: dict[str, set[str]] = {task.task_ref: set() for task in tasks}
    for task in tasks:
        for dependency in task.dependencies:
            adjacency[dependency.task_ref].add(task.task_ref)
    for barrier in barriers:
        for member in barrier.member_task_refs:
            adjacency[member].add(barrier.target_task_ref)
    for gate in branch_gates:
        for rule in gate.rules:
            adjacency[rule.source_task_ref].add(gate.target_task_ref)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_ref: str) -> None:
        if task_ref in visiting:
            raise SchedulerTaskGraphError("le graphe de tâches contient un cycle")
        if task_ref in visited:
            return
        visiting.add(task_ref)
        for successor in sorted(adjacency[task_ref]):
            visit(successor)
        visiting.remove(task_ref)
        visited.add(task_ref)

    for task_ref in sorted(adjacency):
        visit(task_ref)


def _graph_digest(
    *,
    graph_ref: str,
    command_ref: str,
    graph_version: int,
    created_at: str,
    updated_at: str,
    tasks: Sequence[SchedulerTask],
    barriers: Sequence[SchedulerTaskBarrier],
    branch_gates: Sequence[SchedulerTaskBranchGate],
) -> str:
    parts: list[tuple[str, object]] = [
        ("graph_ref", graph_ref),
        ("command_ref", command_ref),
        ("graph_version", graph_version),
        ("created_at", created_at),
        ("updated_at", updated_at),
    ]
    for task in tasks:
        parts.extend((("task_ref", task.task_ref), ("task_digest", task.task_digest)))
    for barrier in barriers:
        parts.extend(
            (
                ("barrier_ref", barrier.barrier_ref),
                ("barrier_target", barrier.target_task_ref),
                ("barrier_kind", barrier.kind.value),
            )
        )
        parts.extend(("barrier_member", value) for value in barrier.member_task_refs)
    for gate in branch_gates:
        parts.extend(
            (
                ("gate_ref", gate.gate_ref),
                ("gate_target", gate.target_task_ref),
                ("gate_mode", gate.mode.value),
            )
        )
        for rule in gate.rules:
            parts.extend(
                (
                    ("branch_source", rule.source_task_ref),
                    ("branch_condition", rule.condition.value),
                )
            )
    return "sha256:" + _length_prefixed_digest(parts)


def _readiness_plan_digest(
    *,
    graph_ref: str,
    graph_version: int,
    evaluations: Sequence[SchedulerTaskReadiness],
) -> str:
    parts: list[tuple[str, object]] = [
        ("graph_ref", graph_ref),
        ("graph_version", graph_version),
    ]
    for item in evaluations:
        parts.extend(
            (
                ("task_ref", item.task_ref),
                ("ready", item.ready),
                ("dependency_blocked", item.dependency_blocked),
            )
        )
        parts.extend(("barrier_blocking", value) for value in item.barrier_refs_blocking)
        parts.extend(("branch_gate_blocking", value) for value in item.branch_gate_refs_blocking)
    return "sha256:" + _length_prefixed_digest(parts)


def _length_prefixed_digest(parts: Sequence[tuple[str, object]]) -> str:
    digest = hashlib.sha256()
    for name, value in parts:
        key = name.encode("utf-8")
        encoded = _scalar_text(value).encode("utf-8")
        digest.update(len(key).to_bytes(4, "big"))
        digest.update(key)
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _scalar_text(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, (str, int)):
        return str(value)
    raise SchedulerTaskGraphError(
        f"type scalaire non pris en charge: {type(value).__name__}"
    )


def _validated_task_refs(name: str, values: Sequence[str]) -> tuple[str, ...]:
    result = tuple(values)
    if not result:
        raise SchedulerTaskGraphError(f"{name} ne doit pas être vide")
    _require_unique_refs(name, result)
    for value in result:
        _require_typed_ref(name, value, "scheduler-task:")
    return result


def _validated_refs(name: str, values: Sequence[str]) -> tuple[str, ...]:
    result = tuple(values)
    _require_unique_refs(name, result)
    for value in result:
        _require_typed_ref(name, value)
    return result


def _require_unique_refs(name: str, values: Sequence[str]) -> None:
    if len(set(values)) != len(values):
        raise SchedulerTaskGraphError(f"{name} contient un doublon")


def _require_typed_ref(name: str, value: object, prefix: str = "") -> None:
    if not isinstance(value, str) or _TYPED_REF_RE.fullmatch(value) is None:
        raise SchedulerTaskGraphError(f"{name} doit être une référence typée")
    if prefix and not value.startswith(prefix):
        raise SchedulerTaskGraphError(f"{name} doit commencer par {prefix}")


def _require_utc(name: str, value: object) -> None:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        raise SchedulerTaskGraphError(f"{name} doit être un horodatage UTC finissant par Z")


def _require_positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SchedulerTaskGraphError(f"{name} doit être un entier strictement positif")


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise SchedulerTaskGraphError(f"{name} doit être un SHA-256 minuscule")


__all__ = (
    "SchedulerTaskBarrier",
    "SchedulerTaskBarrierKind",
    "SchedulerTaskBranchCondition",
    "SchedulerTaskBranchGate",
    "SchedulerTaskBranchMode",
    "SchedulerTaskBranchRule",
    "SchedulerTaskGraph",
    "SchedulerTaskGraphError",
    "SchedulerTaskGraphPromotion",
    "SchedulerTaskReadiness",
    "SchedulerTaskReadinessPlan",
)
