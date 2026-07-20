"""Continuation relationnelle du graphe de recherche sur le port PostgreSQL partagé.

La connexion DB-API est injectée par ``LovePostgreSqlSharedAdapterPort``. Le
store conserve uniquement la topologie du graphe et relit les tâches depuis les
tables normalisées déjà partagées avec les transactions de lancement et de fin.
La révision durable est dérivée des transactions réellement commises : une
promotion de graphe, un lancement ou une clôture compte pour une révision.

Aucun driver, Scheduler, backend, document JSON ou journal JSONL n'est créé.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Protocol

from kernel.scheduler_canonical_continuation import SchedulerDurableGraphSnapshot
from kernel.scheduler_task_graph import (
    SchedulerTaskBarrier,
    SchedulerTaskBarrierKind,
    SchedulerTaskBranchCondition,
    SchedulerTaskBranchGate,
    SchedulerTaskBranchMode,
    SchedulerTaskBranchRule,
    SchedulerTaskGraph,
    SchedulerTaskGraphPromotion,
)
from kernel.scheduler_task_model import (
    SchedulerTask,
    SchedulerTaskDependency,
    SchedulerTaskDependencyKind,
    SchedulerTaskState,
)

POSTGRESQL_CONTINUATION_STORE_VERSION = "0287.r16.r65"
DEFAULT_CONTINUATION_AUTHORITY_REF = "sql-authority:scheduler-continuation"


class GitHubResearchLovePostgreSqlContinuationStoreError(RuntimeError):
    """Échec fermé de la continuation relationnelle partagée."""


class _Cursor(Protocol):
    rowcount: int

    def execute(
        self,
        sql: str,
        parameters: Sequence[object] = (),
    ) -> object: ...

    def fetchone(self) -> Sequence[object] | None: ...

    def fetchall(self) -> Sequence[Sequence[object]]: ...

    def close(self) -> object: ...


class _Connection(Protocol):
    def cursor(self) -> _Cursor: ...

    def commit(self) -> object: ...

    def rollback(self) -> object: ...


@dataclass(frozen=True, slots=True)
class SchedulerGraphRegistration:
    graph_ref: str
    command_ref: str
    scheduler_ref: str
    registered_at: str
    source_transaction_ref: str
    initial_graph_digest: str


class DbApiGitHubResearchLovePostgreSqlContinuationStore:
    """Implémentation DB-API du port de continuation canonique."""

    def __init__(
        self,
        connection: _Connection,
        *,
        scheduler_ref: str,
        paramstyle: str = "format",
        authority_ref: str = DEFAULT_CONTINUATION_AUTHORITY_REF,
        **_unused: object,
    ) -> None:
        if paramstyle not in {"format", "qmark"}:
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "paramstyle doit être format ou qmark"
            )
        _typed_ref("scheduler_ref", scheduler_ref, "scheduler:")
        _typed_ref("authority_ref", authority_ref, "sql-authority:")
        if getattr(connection, "autocommit", False) is True:
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "la continuation refuse une connexion autocommit"
            )
        self._connection = connection
        self._scheduler_ref = scheduler_ref
        self._paramstyle = paramstyle
        self._authority_ref = authority_ref

    @property
    def scheduler_ref(self) -> str:
        return self._scheduler_ref

    @property
    def authority_ref(self) -> str:
        return self._authority_ref

    @property
    def _p(self) -> str:
        return "%s" if self._paramstyle == "format" else "?"

    def initialize_schema(self) -> None:
        """Créer la topologie puis vérifier les tables d'autorité partagées."""

        statements = (
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_graph_registrations (
                command_ref TEXT PRIMARY KEY,
                graph_ref TEXT NOT NULL UNIQUE,
                scheduler_ref TEXT NOT NULL,
                registered_at TEXT NOT NULL,
                source_transaction_ref TEXT NOT NULL,
                initial_graph_digest TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_graph_members (
                command_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                task_ref TEXT NOT NULL UNIQUE,
                PRIMARY KEY (command_ref, ordinal)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_graph_barriers (
                barrier_ref TEXT PRIMARY KEY,
                command_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                target_task_ref TEXT NOT NULL,
                barrier_kind TEXT NOT NULL,
                UNIQUE (command_ref, ordinal)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_graph_barrier_members (
                barrier_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                member_task_ref TEXT NOT NULL,
                PRIMARY KEY (barrier_ref, ordinal),
                UNIQUE (barrier_ref, member_task_ref)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_graph_branch_gates (
                gate_ref TEXT PRIMARY KEY,
                command_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                target_task_ref TEXT NOT NULL,
                gate_mode TEXT NOT NULL,
                UNIQUE (command_ref, ordinal)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_graph_branch_rules (
                gate_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                source_task_ref TEXT NOT NULL,
                branch_condition TEXT NOT NULL,
                PRIMARY KEY (gate_ref, ordinal),
                UNIQUE (gate_ref, source_task_ref, branch_condition)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_graph_promotion_transactions (
                transaction_ref TEXT PRIMARY KEY,
                authority_ref TEXT NOT NULL,
                scheduler_ref TEXT NOT NULL,
                command_ref TEXT NOT NULL,
                graph_ref TEXT NOT NULL,
                previous_graph_digest TEXT NOT NULL,
                next_graph_digest TEXT NOT NULL,
                previous_revision INTEGER NOT NULL,
                next_revision INTEGER NOT NULL,
                promoted_task_count INTEGER NOT NULL,
                committed_at TEXT NOT NULL,
                actor_ref TEXT NOT NULL,
                cause_ref TEXT NOT NULL,
                commit_digest TEXT NOT NULL UNIQUE
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_scheduler_graph_members_command
            ON scheduler_task_graph_members(command_ref, ordinal)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_scheduler_graph_promotions_command
            ON scheduler_task_graph_promotion_transactions(command_ref, committed_at)
            """,
        )
        try:
            for statement in statements:
                self._execute(statement)
            self._verify_shared_authority_tables()
            self._connection.commit()
        except Exception as exc:
            self._rollback_quietly()
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "initialisation SQL de la continuation impossible "
                f"({type(exc).__name__})"
            ) from None

    def put_initial_graph(
        self,
        *,
        graph: SchedulerTaskGraph,
        scheduler_ref: str,
        source_transaction_ref: str,
    ) -> SchedulerDurableGraphSnapshot:
        """Enregistrer une fois la topologie et les tâches initiales typées."""

        self._require_scheduler(scheduler_ref)
        if graph.graph_version != 1:
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "le graphe initial doit avoir graph_version=1"
            )
        _typed_ref("source_transaction_ref", source_transaction_ref)
        existing = self._load_registration(graph.command_ref)
        if existing is not None:
            snapshot = self.load_snapshot(
                command_ref=graph.command_ref,
                scheduler_ref=scheduler_ref,
                loaded_at=graph.created_at,
            )
            if (
                snapshot.durable_revision != 1
                or snapshot.graph.graph_digest != graph.graph_digest
                or existing.source_transaction_ref != source_transaction_ref
            ):
                raise GitHubResearchLovePostgreSqlContinuationStoreError(
                    "collision immuable du graphe initial"
                )
            return snapshot

        try:
            self._insert(
                "scheduler_task_graph_registrations",
                (
                    "command_ref",
                    "graph_ref",
                    "scheduler_ref",
                    "registered_at",
                    "source_transaction_ref",
                    "initial_graph_digest",
                ),
                (
                    graph.command_ref,
                    graph.graph_ref,
                    scheduler_ref,
                    graph.created_at,
                    source_transaction_ref,
                    graph.graph_digest,
                ),
            )
            for ordinal, task in enumerate(graph.tasks):
                self._insert_task(task)
                self._insert(
                    "scheduler_task_graph_members",
                    ("command_ref", "ordinal", "task_ref"),
                    (graph.command_ref, ordinal, task.task_ref),
                )
            for ordinal, barrier in enumerate(graph.barriers):
                self._insert(
                    "scheduler_task_graph_barriers",
                    (
                        "barrier_ref",
                        "command_ref",
                        "ordinal",
                        "target_task_ref",
                        "barrier_kind",
                    ),
                    (
                        barrier.barrier_ref,
                        graph.command_ref,
                        ordinal,
                        barrier.target_task_ref,
                        barrier.kind.value,
                    ),
                )
                for member_ordinal, task_ref in enumerate(barrier.member_task_refs):
                    self._insert(
                        "scheduler_task_graph_barrier_members",
                        ("barrier_ref", "ordinal", "member_task_ref"),
                        (barrier.barrier_ref, member_ordinal, task_ref),
                    )
            for ordinal, gate in enumerate(graph.branch_gates):
                self._insert(
                    "scheduler_task_graph_branch_gates",
                    (
                        "gate_ref",
                        "command_ref",
                        "ordinal",
                        "target_task_ref",
                        "gate_mode",
                    ),
                    (
                        gate.gate_ref,
                        graph.command_ref,
                        ordinal,
                        gate.target_task_ref,
                        gate.mode.value,
                    ),
                )
                for rule_ordinal, rule in enumerate(gate.rules):
                    self._insert(
                        "scheduler_task_graph_branch_rules",
                        (
                            "gate_ref",
                            "ordinal",
                            "source_task_ref",
                            "branch_condition",
                        ),
                        (
                            gate.gate_ref,
                            rule_ordinal,
                            rule.source_task_ref,
                            rule.condition.value,
                        ),
                    )
            self._connection.commit()
        except Exception as exc:
            self._rollback_quietly()
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "enregistrement du graphe initial annulé "
                f"({type(exc).__name__})"
            ) from None
        return self.load_snapshot(
            command_ref=graph.command_ref,
            scheduler_ref=scheduler_ref,
            loaded_at=graph.created_at,
        )

    def load_snapshot(
        self,
        *,
        command_ref: str,
        scheduler_ref: str,
        loaded_at: str,
    ) -> SchedulerDurableGraphSnapshot:
        self._require_scheduler(scheduler_ref)
        _typed_ref("command_ref", command_ref, "scheduler-command:")
        _utc("loaded_at", loaded_at)
        registration = self._load_registration(command_ref)
        if registration is None:
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                f"graphe durable absent pour {command_ref}"
            )
        if registration.scheduler_ref != scheduler_ref:
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "le graphe appartient à un autre Scheduler"
            )

        tasks = self._load_tasks(command_ref)
        barriers = self._load_barriers(command_ref)
        branch_gates = self._load_branch_gates(command_ref)
        event_count, source_transaction_ref, latest_at = self._event_summary(
            command_ref,
            registration,
        )
        durable_revision = 1 + event_count
        updated_at = max(
            (registration.registered_at, latest_at, *(task.updated_at for task in tasks))
        )
        graph_digest = _graph_digest(
            graph_ref=registration.graph_ref,
            command_ref=command_ref,
            graph_version=durable_revision,
            created_at=registration.registered_at,
            updated_at=updated_at,
            tasks=tasks,
            barriers=barriers,
            branch_gates=branch_gates,
        )
        graph = SchedulerTaskGraph(
            graph_ref=registration.graph_ref,
            command_ref=command_ref,
            graph_version=durable_revision,
            created_at=registration.registered_at,
            updated_at=updated_at,
            tasks=tasks,
            barriers=barriers,
            branch_gates=branch_gates,
            graph_digest=graph_digest,
        )
        if (
            durable_revision == 1
            and graph.graph_digest != registration.initial_graph_digest
        ):
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "le graphe initial relu diverge de son digest enregistré"
            )
        return SchedulerDurableGraphSnapshot.create(
            command_ref=command_ref,
            scheduler_ref=scheduler_ref,
            durable_revision=durable_revision,
            loaded_at=loaded_at,
            graph=graph,
            source_transaction_ref=source_transaction_ref,
        )

    def commit_promotion(
        self,
        *,
        snapshot: SchedulerDurableGraphSnapshot,
        promotion: SchedulerTaskGraphPromotion,
        committed_at: str,
        actor_ref: str,
        cause_ref: str,
    ) -> SchedulerDurableGraphSnapshot:
        self._require_scheduler(snapshot.scheduler_ref)
        _utc("committed_at", committed_at)
        _typed_ref("actor_ref", actor_ref)
        _typed_ref("cause_ref", cause_ref)
        if not promotion.changed or not promotion.mutations:
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "commit_promotion exige une promotion modifiée"
            )
        if promotion.plan.graph_version != snapshot.graph.graph_version:
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "la promotion ne part pas de la version relue"
            )
        if promotion.graph.updated_at != committed_at:
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "committed_at doit correspondre à l'horodatage de promotion"
            )
        current = self.load_snapshot(
            command_ref=snapshot.command_ref,
            scheduler_ref=snapshot.scheduler_ref,
            loaded_at=committed_at,
        )
        if (
            current.durable_revision != snapshot.durable_revision
            or current.graph.graph_digest != snapshot.graph.graph_digest
            or current.source_transaction_ref != snapshot.source_transaction_ref
        ):
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "conflit de révision du graphe durable"
            )

        commit_digest = _promotion_commit_digest(
            scheduler_ref=snapshot.scheduler_ref,
            command_ref=snapshot.command_ref,
            graph_ref=snapshot.graph.graph_ref,
            previous_graph_digest=snapshot.graph.graph_digest,
            next_graph_digest=promotion.graph.graph_digest,
            previous_revision=snapshot.durable_revision,
            next_revision=snapshot.durable_revision + 1,
            promoted_task_count=len(promotion.mutations),
            committed_at=committed_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
        )
        transaction_ref = (
            "scheduler-graph-promotion:" + _bare_digest(commit_digest)[:24]
        )
        replay = self._fetchone(
            "SELECT commit_digest FROM scheduler_task_graph_promotion_transactions "
            f"WHERE transaction_ref = {self._p}",
            (transaction_ref,),
        )
        if replay is not None:
            if str(replay[0]) != commit_digest:
                raise GitHubResearchLovePostgreSqlContinuationStoreError(
                    "collision immuable du reçu de promotion"
                )
            return self.load_snapshot(
                command_ref=snapshot.command_ref,
                scheduler_ref=snapshot.scheduler_ref,
                loaded_at=committed_at,
            )

        before_by_ref = {task.task_ref: task for task in snapshot.graph.tasks}
        try:
            for mutation in promotion.mutations:
                before = before_by_ref[mutation.task.task_ref]
                after = mutation.task
                changed = self._execute_count(
                    "UPDATE scheduler_tasks SET state = "
                    f"{self._p}, state_version = {self._p}, "
                    f"effective_priority = {self._p}, updated_at = {self._p}, "
                    f"task_digest = {self._p} WHERE task_ref = {self._p} "
                    f"AND command_ref = {self._p} AND state = {self._p} "
                    f"AND state_version = {self._p} AND task_digest = {self._p}",
                    (
                        after.state.value,
                        after.state_version,
                        after.effective_priority,
                        after.updated_at,
                        after.task_digest,
                        before.task_ref,
                        before.command_ref,
                        before.state.value,
                        before.state_version,
                        before.task_digest,
                    ),
                )
                if changed != 1:
                    raise GitHubResearchLovePostgreSqlContinuationStoreError(
                        f"conflit de promotion pour {before.task_ref}"
                    )
                transition = mutation.transition
                self._insert(
                    "scheduler_task_transitions",
                    (
                        "transition_ref",
                        "task_ref",
                        "from_state",
                        "to_state",
                        "state_version",
                        "occurred_at",
                        "actor_ref",
                        "cause_ref",
                        "transition_digest",
                    ),
                    (
                        transition.transition_ref,
                        transition.task_ref,
                        transition.from_state.value,
                        transition.to_state.value,
                        transition.state_version,
                        transition.occurred_at,
                        transition.actor_ref,
                        transition.cause_ref,
                        transition.transition_digest,
                    ),
                )
            self._insert(
                "scheduler_task_graph_promotion_transactions",
                (
                    "transaction_ref",
                    "authority_ref",
                    "scheduler_ref",
                    "command_ref",
                    "graph_ref",
                    "previous_graph_digest",
                    "next_graph_digest",
                    "previous_revision",
                    "next_revision",
                    "promoted_task_count",
                    "committed_at",
                    "actor_ref",
                    "cause_ref",
                    "commit_digest",
                ),
                (
                    transaction_ref,
                    self._authority_ref,
                    snapshot.scheduler_ref,
                    snapshot.command_ref,
                    snapshot.graph.graph_ref,
                    snapshot.graph.graph_digest,
                    promotion.graph.graph_digest,
                    snapshot.durable_revision,
                    snapshot.durable_revision + 1,
                    len(promotion.mutations),
                    committed_at,
                    actor_ref,
                    cause_ref,
                    commit_digest,
                ),
            )
            self._connection.commit()
        except GitHubResearchLovePostgreSqlContinuationStoreError:
            self._rollback_quietly()
            raise
        except Exception as exc:
            self._rollback_quietly()
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "transaction de promotion annulée "
                f"({type(exc).__name__})"
            ) from None

        result = self.load_snapshot(
            command_ref=snapshot.command_ref,
            scheduler_ref=snapshot.scheduler_ref,
            loaded_at=committed_at,
        )
        if result.graph.graph_digest != promotion.graph.graph_digest:
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "le graphe relu diverge de la promotion commise"
            )
        return result

    def _verify_shared_authority_tables(self) -> None:
        checks = (
            "SELECT task_ref FROM scheduler_tasks WHERE 1 = 0",
            "SELECT transition_ref FROM scheduler_task_transitions WHERE 1 = 0",
            "SELECT transaction_ref FROM scheduler_task_launch_transactions WHERE 1 = 0",
            "SELECT transaction_ref FROM scheduler_handler_execution_transactions WHERE 1 = 0",
        )
        for statement in checks:
            self._fetchall(statement)

    def _require_scheduler(self, scheduler_ref: str) -> None:
        if scheduler_ref != self._scheduler_ref:
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "scheduler_ref diverge du Scheduler installé"
            )

    def _load_registration(self, command_ref: str) -> SchedulerGraphRegistration | None:
        row = self._fetchone(
            "SELECT graph_ref, command_ref, scheduler_ref, registered_at, "
            "source_transaction_ref, initial_graph_digest "
            "FROM scheduler_task_graph_registrations WHERE command_ref = "
            f"{self._p}",
            (command_ref,),
        )
        if row is None:
            return None
        return SchedulerGraphRegistration(*(str(value) for value in row))

    def _load_tasks(self, command_ref: str) -> tuple[SchedulerTask, ...]:
        rows = self._fetchall(
            "SELECT t.task_ref, t.command_ref, t.task_kind_ref, t.capability_ref, "
            "t.contract_version, t.state, t.state_version, t.initial_priority, "
            "t.effective_priority, t.max_attempts, t.attempt_count, t.created_at, "
            "t.updated_at, t.parent_task_ref, t.task_digest "
            "FROM scheduler_task_graph_members m JOIN scheduler_tasks t "
            "ON t.task_ref = m.task_ref WHERE m.command_ref = "
            f"{self._p} ORDER BY m.ordinal",
            (command_ref,),
        )
        if not rows:
            raise GitHubResearchLovePostgreSqlContinuationStoreError(
                "le graphe durable ne contient aucune tâche"
            )
        tasks: list[SchedulerTask] = []
        for row in rows:
            task_ref = str(row[0])
            dependencies = tuple(
                SchedulerTaskDependency(
                    task_ref=str(item[0]),
                    kind=SchedulerTaskDependencyKind(str(item[1])),
                )
                for item in self._fetchall(
                    "SELECT dependency_task_ref, dependency_kind "
                    "FROM scheduler_task_dependencies WHERE task_ref = "
                    f"{self._p} ORDER BY ordinal",
                    (task_ref,),
                )
            )
            context_refs = tuple(
                str(item[0])
                for item in self._fetchall(
                    "SELECT context_ref FROM scheduler_task_context_refs "
                    f"WHERE task_ref = {self._p} ORDER BY ordinal",
                    (task_ref,),
                )
            )
            evidence_refs = tuple(
                str(item[0])
                for item in self._fetchall(
                    "SELECT evidence_ref FROM scheduler_task_evidence_refs "
                    f"WHERE task_ref = {self._p} ORDER BY ordinal",
                    (task_ref,),
                )
            )
            tasks.append(
                SchedulerTask(
                    task_ref=task_ref,
                    command_ref=str(row[1]),
                    task_kind_ref=str(row[2]),
                    capability_ref=str(row[3]),
                    contract_version=int(row[4]),
                    state=SchedulerTaskState(str(row[5])),
                    state_version=int(row[6]),
                    initial_priority=int(row[7]),
                    effective_priority=int(row[8]),
                    max_attempts=int(row[9]),
                    attempt_count=int(row[10]),
                    created_at=str(row[11]),
                    updated_at=str(row[12]),
                    parent_task_ref=str(row[13]),
                    dependencies=dependencies,
                    context_refs=context_refs,
                    evidence_refs=evidence_refs,
                    task_digest=str(row[14]),
                )
            )
        return tuple(tasks)

    def _load_barriers(self, command_ref: str) -> tuple[SchedulerTaskBarrier, ...]:
        rows = self._fetchall(
            "SELECT barrier_ref, target_task_ref, barrier_kind "
            "FROM scheduler_task_graph_barriers WHERE command_ref = "
            f"{self._p} ORDER BY ordinal",
            (command_ref,),
        )
        return tuple(
            SchedulerTaskBarrier(
                barrier_ref=str(row[0]),
                target_task_ref=str(row[1]),
                member_task_refs=tuple(
                    str(member[0])
                    for member in self._fetchall(
                        "SELECT member_task_ref "
                        "FROM scheduler_task_graph_barrier_members "
                        f"WHERE barrier_ref = {self._p} ORDER BY ordinal",
                        (str(row[0]),),
                    )
                ),
                kind=SchedulerTaskBarrierKind(str(row[2])),
            )
            for row in rows
        )

    def _load_branch_gates(self, command_ref: str) -> tuple[SchedulerTaskBranchGate, ...]:
        rows = self._fetchall(
            "SELECT gate_ref, target_task_ref, gate_mode "
            "FROM scheduler_task_graph_branch_gates WHERE command_ref = "
            f"{self._p} ORDER BY ordinal",
            (command_ref,),
        )
        return tuple(
            SchedulerTaskBranchGate(
                gate_ref=str(row[0]),
                target_task_ref=str(row[1]),
                mode=SchedulerTaskBranchMode(str(row[2])),
                rules=tuple(
                    SchedulerTaskBranchRule(
                        source_task_ref=str(rule[0]),
                        condition=SchedulerTaskBranchCondition(str(rule[1])),
                    )
                    for rule in self._fetchall(
                        "SELECT source_task_ref, branch_condition "
                        "FROM scheduler_task_graph_branch_rules WHERE gate_ref = "
                        f"{self._p} ORDER BY ordinal",
                        (str(row[0]),),
                    )
                ),
            )
            for row in rows
        )

    def _event_summary(
        self,
        command_ref: str,
        registration: SchedulerGraphRegistration,
    ) -> tuple[int, str, str]:
        events: list[tuple[str, str]] = [
            (registration.registered_at, registration.source_transaction_ref)
        ]
        sources = (
            (
                "SELECT transaction_ref, committed_at "
                "FROM scheduler_task_graph_promotion_transactions "
                f"WHERE command_ref = {self._p}",
                (command_ref,),
            ),
            (
                "SELECT transaction_ref, committed_at "
                "FROM scheduler_task_launch_transactions "
                f"WHERE command_ref = {self._p}",
                (command_ref,),
            ),
            (
                "SELECT transaction_ref, released_at "
                "FROM scheduler_handler_execution_transactions "
                f"WHERE command_ref = {self._p}",
                (command_ref,),
            ),
        )
        event_count = 0
        for sql, parameters in sources:
            rows = self._fetchall(sql, parameters)
            event_count += len(rows)
            events.extend((str(row[1]), str(row[0])) for row in rows)
        latest_at, latest_ref = max(events, key=lambda item: (item[0], item[1]))
        return event_count, latest_ref, latest_at

    def _insert_task(self, task: SchedulerTask) -> None:
        existing = self._fetchone(
            "SELECT task_digest FROM scheduler_tasks WHERE task_ref = "
            f"{self._p}",
            (task.task_ref,),
        )
        if existing is not None:
            if str(existing[0]) != task.task_digest:
                raise GitHubResearchLovePostgreSqlContinuationStoreError(
                    "collision immuable d'une tâche initiale"
                )
            return
        self._insert(
            "scheduler_tasks",
            (
                "task_ref",
                "command_ref",
                "task_kind_ref",
                "capability_ref",
                "contract_version",
                "state",
                "state_version",
                "initial_priority",
                "effective_priority",
                "max_attempts",
                "attempt_count",
                "created_at",
                "updated_at",
                "parent_task_ref",
                "task_digest",
            ),
            (
                task.task_ref,
                task.command_ref,
                task.task_kind_ref,
                task.capability_ref,
                task.contract_version,
                task.state.value,
                task.state_version,
                task.initial_priority,
                task.effective_priority,
                task.max_attempts,
                task.attempt_count,
                task.created_at,
                task.updated_at,
                task.parent_task_ref,
                task.task_digest,
            ),
        )
        for ordinal, dependency in enumerate(task.dependencies):
            self._insert(
                "scheduler_task_dependencies",
                ("task_ref", "ordinal", "dependency_task_ref", "dependency_kind"),
                (task.task_ref, ordinal, dependency.task_ref, dependency.kind.value),
            )
        for ordinal, context_ref in enumerate(task.context_refs):
            self._insert(
                "scheduler_task_context_refs",
                ("task_ref", "ordinal", "context_ref"),
                (task.task_ref, ordinal, context_ref),
            )
        for ordinal, evidence_ref in enumerate(task.evidence_refs):
            self._insert(
                "scheduler_task_evidence_refs",
                ("task_ref", "ordinal", "evidence_ref"),
                (task.task_ref, ordinal, evidence_ref),
            )

    def _insert(self, table: str, columns: tuple[str, ...], values: tuple[object, ...]) -> None:
        self._execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES "
            f"({', '.join(self._p for _ in columns)})",
            values,
        )

    def _execute(self, sql: str, parameters: Sequence[object] = ()) -> None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
        finally:
            cursor.close()

    def _execute_count(self, sql: str, parameters: Sequence[object]) -> int:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
            return int(cursor.rowcount)
        finally:
            cursor.close()

    def _fetchone(
        self,
        sql: str,
        parameters: Sequence[object] = (),
    ) -> Sequence[object] | None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
            return cursor.fetchone()
        finally:
            cursor.close()

    def _fetchall(
        self,
        sql: str,
        parameters: Sequence[object] = (),
    ) -> Sequence[Sequence[object]]:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
            return cursor.fetchall()
        finally:
            cursor.close()

    def _rollback_quietly(self) -> None:
        try:
            self._connection.rollback()
        except Exception:
            pass


def build_github_research_love_postgresql_continuation_store(
    connection: _Connection,
    *,
    scheduler_ref: str,
    paramstyle: str = "format",
    **available: object,
) -> DbApiGitHubResearchLovePostgreSqlContinuationStore:
    """Fabrique configurée r16-r65, sans ouverture de connexion."""

    return DbApiGitHubResearchLovePostgreSqlContinuationStore(
        connection,
        scheduler_ref=scheduler_ref,
        paramstyle=paramstyle,
        **available,
    )


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


def _promotion_commit_digest(
    *,
    scheduler_ref: str,
    command_ref: str,
    graph_ref: str,
    previous_graph_digest: str,
    next_graph_digest: str,
    previous_revision: int,
    next_revision: int,
    promoted_task_count: int,
    committed_at: str,
    actor_ref: str,
    cause_ref: str,
) -> str:
    return "sha256:" + _length_prefixed_digest(
        (
            ("scheduler_ref", scheduler_ref),
            ("command_ref", command_ref),
            ("graph_ref", graph_ref),
            ("previous_graph_digest", previous_graph_digest),
            ("next_graph_digest", next_graph_digest),
            ("previous_revision", previous_revision),
            ("next_revision", next_revision),
            ("promoted_task_count", promoted_task_count),
            ("committed_at", committed_at),
            ("actor_ref", actor_ref),
            ("cause_ref", cause_ref),
        )
    )


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
    raise GitHubResearchLovePostgreSqlContinuationStoreError(
        f"type scalaire non pris en charge: {type(value).__name__}"
    )


def _bare_digest(value: str) -> str:
    return value.removeprefix("sha256:")


def _typed_ref(name: str, value: object, prefix: str = "") -> None:
    if (
        not isinstance(value, str)
        or ":" not in value
        or any(character.isspace() for character in value)
    ):
        raise GitHubResearchLovePostgreSqlContinuationStoreError(
            f"{name} doit être une référence typée"
        )
    if prefix and not value.startswith(prefix):
        raise GitHubResearchLovePostgreSqlContinuationStoreError(
            f"{name} doit commencer par {prefix}"
        )


def _utc(name: str, value: object) -> None:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        raise GitHubResearchLovePostgreSqlContinuationStoreError(
            f"{name} doit être un horodatage UTC finissant par Z"
        )


__all__ = (
    "DEFAULT_CONTINUATION_AUTHORITY_REF",
    "POSTGRESQL_CONTINUATION_STORE_VERSION",
    "DbApiGitHubResearchLovePostgreSqlContinuationStore",
    "GitHubResearchLovePostgreSqlContinuationStoreError",
    "SchedulerGraphRegistration",
    "build_github_research_love_postgresql_continuation_store",
)
