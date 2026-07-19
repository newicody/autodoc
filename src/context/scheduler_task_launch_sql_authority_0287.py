"""Transactional relational authority for admitted Scheduler task launches.

The adapter implements :class:`SchedulerTaskLaunchTransaction` on one injected
DB-API connection.  It stores the task, attempt, transition, bounded command
budget mutation and resource reservation in normalized tables, then moves the
already-claimed command to ``running`` in the same transaction.

It opens no driver, creates no Scheduler, executes no handler and stores no document or line-file authority.  A caller must initialize the schema and provide the same
connection already owned by the local PostgreSQL authority binding.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from kernel.scheduler_handler_catalog import SchedulerHandlerBinding
from kernel.scheduler_task_admission import (
    SchedulerResourceReservation,
    SchedulerTaskAdmissionDecision,
    SchedulerTaskAdmissionPlan,
)
from kernel.scheduler_task_launch_preparation import (
    SchedulerCommandBudgetMutation,
    SchedulerTaskLaunchCommit,
    SchedulerTaskLaunchTransaction,
)
from kernel.scheduler_task_model import (
    SchedulerTask,
    SchedulerTaskAttemptStart,
    SchedulerTaskState,
)


SCHEDULER_TASK_LAUNCH_SQL_AUTHORITY_VERSION = "0287.r16.r31.r1"
DEFAULT_SCHEDULER_TASK_LAUNCH_AUTHORITY_REF = (
    "sql-authority:scheduler-task-launches"
)


class SchedulerTaskLaunchSqlAuthorityError(RuntimeError):
    """Raised when a launch transaction cannot fail closed atomically."""


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


class DbApiSchedulerTaskLaunchTransaction(SchedulerTaskLaunchTransaction):
    """Atomic DB-API implementation of one admitted task launch.

    ``paramstyle`` is ``format`` for psycopg/PostgreSQL and ``qmark`` for the
    bounded SQLite test path.  The connection must not be configured for
    autocommit because every mutation belongs to one indivisible transaction.
    """

    def __init__(
        self,
        connection: _Connection,
        *,
        paramstyle: str = "format",
        authority_ref: str = DEFAULT_SCHEDULER_TASK_LAUNCH_AUTHORITY_REF,
    ) -> None:
        if paramstyle not in {"format", "qmark"}:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "paramstyle doit être format ou qmark"
            )
        if not authority_ref.startswith("sql-authority:"):
            raise SchedulerTaskLaunchSqlAuthorityError(
                "authority_ref doit commencer par sql-authority:"
            )
        if getattr(connection, "autocommit", False) is True:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "la transaction de lancement refuse une connexion autocommit"
            )
        self._connection = connection
        self._paramstyle = paramstyle
        self._authority_ref = authority_ref

    @property
    def authority_ref(self) -> str:
        return self._authority_ref

    def initialize_schema(self) -> None:
        """Create the normalized launch authority schema idempotently."""

        statements = (
            """
            CREATE TABLE IF NOT EXISTS scheduler_command_budget_states (
                command_ref TEXT PRIMARY KEY,
                budget_ref TEXT NOT NULL UNIQUE,
                consumed_scheduler_steps INTEGER NOT NULL,
                consumed_specialist_visits INTEGER NOT NULL,
                state_version INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_tasks (
                task_ref TEXT PRIMARY KEY,
                command_ref TEXT NOT NULL,
                task_kind_ref TEXT NOT NULL,
                capability_ref TEXT NOT NULL,
                contract_version INTEGER NOT NULL,
                state TEXT NOT NULL,
                state_version INTEGER NOT NULL,
                initial_priority INTEGER NOT NULL,
                effective_priority INTEGER NOT NULL,
                max_attempts INTEGER NOT NULL,
                attempt_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                parent_task_ref TEXT NOT NULL,
                task_digest TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_dependencies (
                task_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                dependency_task_ref TEXT NOT NULL,
                dependency_kind TEXT NOT NULL,
                PRIMARY KEY (task_ref, ordinal),
                UNIQUE (task_ref, dependency_task_ref)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_context_refs (
                task_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                context_ref TEXT NOT NULL,
                PRIMARY KEY (task_ref, ordinal),
                UNIQUE (task_ref, context_ref)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_evidence_refs (
                task_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                evidence_ref TEXT NOT NULL,
                PRIMARY KEY (task_ref, ordinal),
                UNIQUE (task_ref, evidence_ref)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_attempts (
                attempt_ref TEXT PRIMARY KEY,
                task_ref TEXT NOT NULL,
                attempt_number INTEGER NOT NULL,
                state TEXT NOT NULL,
                handler_ref TEXT NOT NULL,
                capability_ref TEXT NOT NULL,
                contract_version INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                deadline_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                result_ref TEXT NOT NULL,
                failure_ref TEXT NOT NULL,
                UNIQUE (task_ref, attempt_number)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_transitions (
                transition_ref TEXT PRIMARY KEY,
                task_ref TEXT NOT NULL,
                from_state TEXT NOT NULL,
                to_state TEXT NOT NULL,
                state_version INTEGER NOT NULL,
                occurred_at TEXT NOT NULL,
                actor_ref TEXT NOT NULL,
                cause_ref TEXT NOT NULL,
                transition_digest TEXT NOT NULL UNIQUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_resource_inventory (
                resource_ref TEXT PRIMARY KEY,
                capacity INTEGER NOT NULL,
                reserved INTEGER NOT NULL,
                state_version INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_resource_reservations (
                reservation_ref TEXT PRIMARY KEY,
                task_ref TEXT NOT NULL UNIQUE,
                profile_ref TEXT NOT NULL,
                reserved_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                reservation_digest TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_resource_reservation_requirements (
                reservation_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                resource_ref TEXT NOT NULL,
                amount INTEGER NOT NULL,
                exclusive BOOLEAN NOT NULL,
                PRIMARY KEY (reservation_ref, ordinal),
                UNIQUE (reservation_ref, resource_ref)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_task_launch_transactions (
                transaction_ref TEXT PRIMARY KEY,
                authority_ref TEXT NOT NULL,
                scheduler_ref TEXT NOT NULL,
                command_ref TEXT NOT NULL,
                task_ref TEXT NOT NULL UNIQUE,
                attempt_ref TEXT NOT NULL UNIQUE,
                reservation_ref TEXT NOT NULL UNIQUE,
                admission_plan_digest TEXT NOT NULL,
                task_state_version INTEGER NOT NULL,
                scheduler_steps_before INTEGER NOT NULL,
                scheduler_steps_after INTEGER NOT NULL,
                specialist_visits_before INTEGER NOT NULL,
                specialist_visits_after INTEGER NOT NULL,
                budget_mutation_digest TEXT NOT NULL UNIQUE,
                committed_at TEXT NOT NULL,
                commit_digest TEXT NOT NULL UNIQUE
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_scheduler_tasks_command_state
            ON scheduler_tasks(command_ref, state, effective_priority, task_ref)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_scheduler_resource_reservation_status
            ON scheduler_resource_reservations(status, expires_at, reservation_ref)
            """,
        )
        try:
            for statement in statements:
                self._execute(statement)
            self._connection.commit()
        except Exception as exc:
            self._rollback_quietly()
            raise SchedulerTaskLaunchSqlAuthorityError(
                "initialisation SQL des lancements Scheduler impossible "
                f"({type(exc).__name__})"
            ) from None

    def put_resource_inventory_item(
        self,
        *,
        resource_ref: str,
        capacity: int,
        reserved: int,
        state_version: int,
        updated_at: str,
    ) -> None:
        """Seed or replace one explicit resource inventory item.

        This narrow helper is for bootstrap/tests.  It performs no scheduling
        decision and is not a resource manager.
        """

        if not resource_ref.startswith("resource:"):
            raise SchedulerTaskLaunchSqlAuthorityError(
                "resource_ref doit commencer par resource:"
            )
        for name, value in (
            ("capacity", capacity),
            ("reserved", reserved),
            ("state_version", state_version),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise SchedulerTaskLaunchSqlAuthorityError(
                    f"{name} doit être un entier positif ou nul"
                )
        if state_version < 1 or reserved > capacity:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "inventaire de ressource incohérent"
            )
        current = self._fetchone(
            "SELECT capacity, reserved, state_version, updated_at "
            "FROM scheduler_resource_inventory WHERE resource_ref = "
            f"{self._placeholder}",
            (resource_ref,),
        )
        try:
            if current is None:
                self._insert(
                    "scheduler_resource_inventory",
                    (
                        "resource_ref",
                        "capacity",
                        "reserved",
                        "state_version",
                        "updated_at",
                    ),
                    (resource_ref, capacity, reserved, state_version, updated_at),
                )
            else:
                self._execute(
                    "UPDATE scheduler_resource_inventory SET capacity = "
                    f"{self._placeholder}, reserved = {self._placeholder}, "
                    f"state_version = {self._placeholder}, updated_at = {self._placeholder} "
                    f"WHERE resource_ref = {self._placeholder}",
                    (capacity, reserved, state_version, updated_at, resource_ref),
                )
            self._connection.commit()
        except Exception as exc:
            self._rollback_quietly()
            raise SchedulerTaskLaunchSqlAuthorityError(
                "écriture de l’inventaire Scheduler impossible "
                f"({type(exc).__name__})"
            ) from None

    def commit_launch(
        self,
        *,
        scheduler_ref: str,
        plan: SchedulerTaskAdmissionPlan,
        decision: SchedulerTaskAdmissionDecision,
        task_before: SchedulerTask,
        attempt_start: SchedulerTaskAttemptStart,
        budget_mutation: SchedulerCommandBudgetMutation,
        reservation: SchedulerResourceReservation,
        handler_binding: SchedulerHandlerBinding,
        committed_at: str,
    ) -> SchedulerTaskLaunchCommit:
        """Commit one admitted launch atomically or roll back every mutation."""

        expected = self._validate_and_build_commit(
            scheduler_ref=scheduler_ref,
            plan=plan,
            decision=decision,
            task_before=task_before,
            attempt_start=attempt_start,
            budget_mutation=budget_mutation,
            reservation=reservation,
            handler_binding=handler_binding,
            committed_at=committed_at,
        )
        replay = self._load_launch_commit(expected.transaction_ref)
        if replay is not None:
            if replay != expected:
                raise SchedulerTaskLaunchSqlAuthorityError(
                    "collision immuable du reçu de lancement"
                )
            return replay

        try:
            self._lock_command_for_launch(
                scheduler_ref=scheduler_ref,
                command_ref=task_before.command_ref,
                committed_at=committed_at,
            )
            self._charge_command_budget(
                mutation=budget_mutation,
                committed_at=committed_at,
            )
            self._reserve_resources(
                reservation=reservation,
                committed_at=committed_at,
            )
            self._persist_ready_task(task_before)
            self._move_task_to_running(
                task_before=task_before,
                task_running=attempt_start.task,
            )
            self._persist_attempt(attempt_start)
            self._persist_transition(attempt_start)
            self._persist_launch_commit(expected, budget_mutation)
            self._connection.commit()
            return expected
        except SchedulerTaskLaunchSqlAuthorityError:
            self._rollback_quietly()
            raise
        except Exception as exc:
            self._rollback_quietly()
            raise SchedulerTaskLaunchSqlAuthorityError(
                "transaction SQL de lancement Scheduler annulée "
                f"({type(exc).__name__})"
            ) from None

    def _validate_and_build_commit(
        self,
        *,
        scheduler_ref: str,
        plan: SchedulerTaskAdmissionPlan,
        decision: SchedulerTaskAdmissionDecision,
        task_before: SchedulerTask,
        attempt_start: SchedulerTaskAttemptStart,
        budget_mutation: SchedulerCommandBudgetMutation,
        reservation: SchedulerResourceReservation,
        handler_binding: SchedulerHandlerBinding,
        committed_at: str,
    ) -> SchedulerTaskLaunchCommit:
        task_running = attempt_start.task
        attempt = attempt_start.attempt
        transition = attempt_start.transition
        if task_before.state is not SchedulerTaskState.READY:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "task_before doit être ready"
            )
        if task_running.state is not SchedulerTaskState.RUNNING:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "task_running doit être running"
            )
        if decision.task_ref != task_before.task_ref:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "la décision et la tâche divergent"
            )
        if decision.reservation != reservation:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "la réservation diverge de la décision d’admission"
            )
        if task_running.task_ref != task_before.task_ref:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "les versions de tâche divergent"
            )
        if task_running.command_ref != budget_mutation.command_ref:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "la tâche et la mutation de budget divergent"
            )
        if attempt.task_ref != task_running.task_ref:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "la tentative et la tâche divergent"
            )
        if transition.task_ref != task_running.task_ref:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "la transition et la tâche divergent"
            )
        if reservation.task_ref != task_running.task_ref:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "la réservation et la tâche divergent"
            )
        if handler_binding.handler_ref != attempt.handler_ref:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "le handler résolu diverge de la tentative"
            )
        if plan.plan_digest == "" or committed_at != attempt.started_at:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "horodatage ou digest du lancement incohérent"
            )
        if transition.occurred_at != committed_at:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "la transition doit partager l’horodatage du commit"
            )
        return SchedulerTaskLaunchCommit.create(
            scheduler_ref=scheduler_ref,
            command_ref=task_running.command_ref,
            task_ref=task_running.task_ref,
            attempt_ref=attempt.attempt_ref,
            reservation_ref=reservation.reservation_ref,
            admission_plan_digest=plan.plan_digest,
            task_state_version=task_running.state_version,
            scheduler_steps_after=budget_mutation.scheduler_steps_after,
            specialist_visits_after=budget_mutation.specialist_visits_after,
            committed_at=committed_at,
        )

    def _lock_command_for_launch(
        self,
        *,
        scheduler_ref: str,
        command_ref: str,
        committed_at: str,
    ) -> None:
        row = self._fetchone(
            "SELECT state, state_version, claimed_by, started_at "
            "FROM scheduler_command_states WHERE command_ref = "
            f"{self._placeholder}",
            (command_ref,),
        )
        if row is None:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "commande Scheduler absente de l’autorité SQL"
            )
        state, version, claimed_by, started_at = (
            str(row[0]), int(row[1]), str(row[2]), str(row[3])
        )
        if state not in {"claimed", "running"} or claimed_by != scheduler_ref:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "la commande n’est pas réclamée par ce Scheduler"
            )
        next_started_at = started_at or committed_at
        changed = self._execute_count(
            "UPDATE scheduler_command_states SET state = "
            f"{self._placeholder}, state_version = state_version + 1, "
            f"updated_at = {self._placeholder}, started_at = {self._placeholder} "
            f"WHERE command_ref = {self._placeholder} AND state = {self._placeholder} "
            f"AND state_version = {self._placeholder} AND claimed_by = {self._placeholder}",
            (
                "running",
                committed_at,
                next_started_at,
                command_ref,
                state,
                version,
                scheduler_ref,
            ),
        )
        if changed != 1:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "conflit de version de l’état de commande"
            )

    def _charge_command_budget(
        self,
        *,
        mutation: SchedulerCommandBudgetMutation,
        committed_at: str,
    ) -> None:
        limits = self._fetchone(
            "SELECT max_scheduler_steps, max_specialist_visits "
            "FROM scheduler_command_execution_budgets WHERE command_ref = "
            f"{self._placeholder}",
            (mutation.command_ref,),
        )
        if limits is None:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "budget maximal de commande absent"
            )
        if (
            mutation.scheduler_steps_after > int(limits[0])
            or mutation.specialist_visits_after > int(limits[1])
        ):
            raise SchedulerTaskLaunchSqlAuthorityError(
                "la mutation dépasse le budget maximal"
            )
        row = self._fetchone(
            "SELECT budget_ref, consumed_scheduler_steps, "
            "consumed_specialist_visits, state_version "
            "FROM scheduler_command_budget_states WHERE command_ref = "
            f"{self._placeholder}",
            (mutation.command_ref,),
        )
        if row is None:
            if (
                mutation.scheduler_steps_before != 0
                or mutation.specialist_visits_before != 0
            ):
                raise SchedulerTaskLaunchSqlAuthorityError(
                    "état de budget absent pour une consommation non nulle"
                )
            self._insert(
                "scheduler_command_budget_states",
                (
                    "command_ref",
                    "budget_ref",
                    "consumed_scheduler_steps",
                    "consumed_specialist_visits",
                    "state_version",
                    "updated_at",
                ),
                (
                    mutation.command_ref,
                    mutation.budget_ref,
                    0,
                    0,
                    1,
                    committed_at,
                ),
            )
            row = (mutation.budget_ref, 0, 0, 1)
        budget_ref, steps_before, visits_before, state_version = (
            str(row[0]), int(row[1]), int(row[2]), int(row[3])
        )
        if budget_ref != mutation.budget_ref:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "budget_ref SQL divergent"
            )
        if (
            steps_before != mutation.scheduler_steps_before
            or visits_before != mutation.specialist_visits_before
        ):
            raise SchedulerTaskLaunchSqlAuthorityError(
                "conflit de consommation du budget de commande"
            )
        changed = self._execute_count(
            "UPDATE scheduler_command_budget_states SET "
            f"consumed_scheduler_steps = {self._placeholder}, "
            f"consumed_specialist_visits = {self._placeholder}, "
            f"state_version = state_version + 1, updated_at = {self._placeholder} "
            f"WHERE command_ref = {self._placeholder} "
            f"AND consumed_scheduler_steps = {self._placeholder} "
            f"AND consumed_specialist_visits = {self._placeholder} "
            f"AND state_version = {self._placeholder}",
            (
                mutation.scheduler_steps_after,
                mutation.specialist_visits_after,
                committed_at,
                mutation.command_ref,
                steps_before,
                visits_before,
                state_version,
            ),
        )
        if changed != 1:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "conflit de version du budget de commande"
            )

    def _reserve_resources(
        self,
        *,
        reservation: SchedulerResourceReservation,
        committed_at: str,
    ) -> None:
        for requirement in reservation.requirements:
            row = self._fetchone(
                "SELECT capacity, reserved, state_version "
                "FROM scheduler_resource_inventory WHERE resource_ref = "
                f"{self._placeholder}",
                (requirement.resource_ref,),
            )
            if row is None:
                raise SchedulerTaskLaunchSqlAuthorityError(
                    f"ressource absente: {requirement.resource_ref}"
                )
            capacity, reserved, state_version = int(row[0]), int(row[1]), int(row[2])
            if requirement.exclusive and reserved != 0:
                raise SchedulerTaskLaunchSqlAuthorityError(
                    f"ressource exclusive déjà réservée: {requirement.resource_ref}"
                )
            if capacity - reserved < requirement.amount:
                raise SchedulerTaskLaunchSqlAuthorityError(
                    f"capacité insuffisante: {requirement.resource_ref}"
                )
            changed = self._execute_count(
                "UPDATE scheduler_resource_inventory SET reserved = "
                f"{self._placeholder}, state_version = state_version + 1, "
                f"updated_at = {self._placeholder} WHERE resource_ref = "
                f"{self._placeholder} AND capacity = {self._placeholder} "
                f"AND reserved = {self._placeholder} AND state_version = {self._placeholder}",
                (
                    reserved + requirement.amount,
                    committed_at,
                    requirement.resource_ref,
                    capacity,
                    reserved,
                    state_version,
                ),
            )
            if changed != 1:
                raise SchedulerTaskLaunchSqlAuthorityError(
                    f"conflit de réservation: {requirement.resource_ref}"
                )
        self._insert(
            "scheduler_resource_reservations",
            (
                "reservation_ref",
                "task_ref",
                "profile_ref",
                "reserved_at",
                "expires_at",
                "reservation_digest",
                "status",
            ),
            (
                reservation.reservation_ref,
                reservation.task_ref,
                reservation.profile_ref,
                reservation.reserved_at,
                reservation.expires_at,
                reservation.reservation_digest,
                "active",
            ),
        )
        for ordinal, requirement in enumerate(reservation.requirements):
            self._insert(
                "scheduler_resource_reservation_requirements",
                (
                    "reservation_ref",
                    "ordinal",
                    "resource_ref",
                    "amount",
                    "exclusive",
                ),
                (
                    reservation.reservation_ref,
                    ordinal,
                    requirement.resource_ref,
                    requirement.amount,
                    requirement.exclusive,
                ),
            )

    def _persist_ready_task(self, task: SchedulerTask) -> None:
        row = self._fetchone(
            "SELECT task_digest, state, state_version FROM scheduler_tasks "
            f"WHERE task_ref = {self._placeholder}",
            (task.task_ref,),
        )
        if row is not None:
            if (
                str(row[0]) != task.task_digest
                or str(row[1]) != task.state.value
                or int(row[2]) != task.state_version
            ):
                raise SchedulerTaskLaunchSqlAuthorityError(
                    "collision immuable de la tâche Scheduler"
                )
            return
        self._insert_task(task)
        for ordinal, dependency in enumerate(task.dependencies):
            self._insert(
                "scheduler_task_dependencies",
                (
                    "task_ref",
                    "ordinal",
                    "dependency_task_ref",
                    "dependency_kind",
                ),
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

    def _insert_task(self, task: SchedulerTask) -> None:
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

    def _move_task_to_running(
        self,
        *,
        task_before: SchedulerTask,
        task_running: SchedulerTask,
    ) -> None:
        changed = self._execute_count(
            "UPDATE scheduler_tasks SET state = "
            f"{self._placeholder}, state_version = {self._placeholder}, "
            f"effective_priority = {self._placeholder}, "
            f"attempt_count = {self._placeholder}, updated_at = {self._placeholder}, "
            f"task_digest = {self._placeholder} WHERE task_ref = {self._placeholder} "
            f"AND state = {self._placeholder} AND state_version = {self._placeholder} "
            f"AND task_digest = {self._placeholder}",
            (
                task_running.state.value,
                task_running.state_version,
                task_running.effective_priority,
                task_running.attempt_count,
                task_running.updated_at,
                task_running.task_digest,
                task_before.task_ref,
                task_before.state.value,
                task_before.state_version,
                task_before.task_digest,
            ),
        )
        if changed != 1:
            raise SchedulerTaskLaunchSqlAuthorityError(
                "conflit de version de la tâche Scheduler"
            )

    def _persist_attempt(self, attempt_start: SchedulerTaskAttemptStart) -> None:
        attempt = attempt_start.attempt
        self._insert(
            "scheduler_task_attempts",
            (
                "attempt_ref",
                "task_ref",
                "attempt_number",
                "state",
                "handler_ref",
                "capability_ref",
                "contract_version",
                "started_at",
                "deadline_at",
                "finished_at",
                "result_ref",
                "failure_ref",
            ),
            (
                attempt.attempt_ref,
                attempt.task_ref,
                attempt.number,
                attempt.state.value,
                attempt.handler_ref,
                attempt.capability_ref,
                attempt.contract_version,
                attempt.started_at,
                attempt.deadline_at,
                attempt.finished_at,
                attempt.result_ref,
                attempt.failure_ref,
            ),
        )

    def _persist_transition(self, attempt_start: SchedulerTaskAttemptStart) -> None:
        transition = attempt_start.transition
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

    def _persist_launch_commit(
        self,
        commit: SchedulerTaskLaunchCommit,
        mutation: SchedulerCommandBudgetMutation,
    ) -> None:
        self._insert(
            "scheduler_task_launch_transactions",
            (
                "transaction_ref",
                "authority_ref",
                "scheduler_ref",
                "command_ref",
                "task_ref",
                "attempt_ref",
                "reservation_ref",
                "admission_plan_digest",
                "task_state_version",
                "scheduler_steps_before",
                "scheduler_steps_after",
                "specialist_visits_before",
                "specialist_visits_after",
                "budget_mutation_digest",
                "committed_at",
                "commit_digest",
            ),
            (
                commit.transaction_ref,
                self._authority_ref,
                commit.scheduler_ref,
                commit.command_ref,
                commit.task_ref,
                commit.attempt_ref,
                commit.reservation_ref,
                commit.admission_plan_digest,
                commit.task_state_version,
                mutation.scheduler_steps_before,
                commit.scheduler_steps_after,
                mutation.specialist_visits_before,
                commit.specialist_visits_after,
                mutation.mutation_digest,
                commit.committed_at,
                commit.commit_digest,
            ),
        )

    def _load_launch_commit(
        self,
        transaction_ref: str,
    ) -> SchedulerTaskLaunchCommit | None:
        row = self._fetchone(
            "SELECT scheduler_ref, command_ref, task_ref, attempt_ref, "
            "reservation_ref, admission_plan_digest, task_state_version, "
            "scheduler_steps_after, specialist_visits_after, committed_at "
            "FROM scheduler_task_launch_transactions WHERE transaction_ref = "
            f"{self._placeholder}",
            (transaction_ref,),
        )
        if row is None:
            return None
        return SchedulerTaskLaunchCommit.create(
            scheduler_ref=str(row[0]),
            command_ref=str(row[1]),
            task_ref=str(row[2]),
            attempt_ref=str(row[3]),
            reservation_ref=str(row[4]),
            admission_plan_digest=str(row[5]),
            task_state_version=int(row[6]),
            scheduler_steps_after=int(row[7]),
            specialist_visits_after=int(row[8]),
            committed_at=str(row[9]),
        )

    @property
    def _placeholder(self) -> str:
        return "?" if self._paramstyle == "qmark" else "%s"

    def _insert(
        self,
        table: str,
        columns: tuple[str, ...],
        values: tuple[object, ...],
    ) -> None:
        placeholders = ", ".join(self._placeholder for _ in columns)
        names = ", ".join(columns)
        self._execute(
            f"INSERT INTO {table} ({names}) VALUES ({placeholders})",
            values,
        )

    def _execute(
        self,
        sql: str,
        parameters: Sequence[object] = (),
    ) -> None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
        finally:
            cursor.close()

    def _execute_count(
        self,
        sql: str,
        parameters: Sequence[object],
    ) -> int:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
            return int(cursor.rowcount)
        finally:
            cursor.close()

    def _fetchone(
        self,
        sql: str,
        parameters: Sequence[object],
    ) -> Sequence[object] | None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
            return cursor.fetchone()
        finally:
            cursor.close()

    def _rollback_quietly(self) -> None:
        try:
            self._connection.rollback()
        except Exception:  # noqa: BLE001 - preserve sanitized primary failure
            pass


__all__ = (
    "DEFAULT_SCHEDULER_TASK_LAUNCH_AUTHORITY_REF",
    "SCHEDULER_TASK_LAUNCH_SQL_AUTHORITY_VERSION",
    "DbApiSchedulerTaskLaunchTransaction",
    "SchedulerTaskLaunchSqlAuthorityError",
)
