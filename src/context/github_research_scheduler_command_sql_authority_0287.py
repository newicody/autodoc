"""Relational SQL authority for typed GitHub research Scheduler commands.

The command object graph remains the in-process authority.  This adapter stores
that graph in normalized SQL tables and reconstructs the same classes on read.
It accepts an injected DB-API connection, opens no driver, creates no Scheduler,
uses no filesystem queue, and stores no JSON document or JSON column.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from context.github_research_scheduler_command_0287 import (
    COMMAND_WRITE_RESULT_SCHEMA,
    GitHubResearchCorrelation,
    GitHubResearchPayload,
    GitHubResearchSchedulerCommand,
    GitHubResearchSchedulerCommandStore,
    ResearchExecutionBudget,
    SchedulerAuthorization,
    SchedulerCommandSqlWriteResult,
)
from context.sql_context_store import SqlContextStorePolicy
from runtime.scheduler_route_adapter import SchedulerRouteRequest

SCHEDULER_COMMAND_SQL_AUTHORITY_VERSION = "0287.r16.r25"
SCHEDULER_COMMAND_STATE_SCHEMA = "missipy.scheduler.command_sql_state.v1"
DEFAULT_SCHEDULER_COMMAND_AUTHORITY_REF = (
    "sql-authority:github-research-scheduler-commands"
)

_ALLOWED_STATES = frozenset(
    {"pending", "claimed", "running", "completed", "failed", "cancelled"}
)


class GitHubResearchSchedulerCommandSqlAuthorityError(RuntimeError):
    """Raised when relational command persistence cannot fail closed."""


class _Cursor(Protocol):
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
class SchedulerCommandSqlState:
    """Durable lifecycle state for one Scheduler command."""

    schema: str
    command_ref: str
    state: str
    state_version: int
    updated_at: str
    claimed_by: str
    claimed_at: str
    started_at: str
    completed_at: str
    failed_at: str
    last_error_code: str

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_COMMAND_STATE_SCHEMA:
            raise GitHubResearchSchedulerCommandSqlAuthorityError(
                "unsupported Scheduler command state schema"
            )
        if self.state not in _ALLOWED_STATES:
            raise GitHubResearchSchedulerCommandSqlAuthorityError(
                "unsupported Scheduler command state"
            )
        if self.state_version < 1:
            raise GitHubResearchSchedulerCommandSqlAuthorityError(
                "state_version must be positive"
            )


class DbApiGitHubResearchSchedulerCommandStore(
    GitHubResearchSchedulerCommandStore
):
    """Normalized DB-API store for immutable typed research commands."""

    def __init__(
        self,
        connection: _Connection,
        policy: SqlContextStorePolicy | None = None,
        *,
        authority_ref: str = DEFAULT_SCHEDULER_COMMAND_AUTHORITY_REF,
    ) -> None:
        if not authority_ref.startswith("sql-authority:"):
            raise GitHubResearchSchedulerCommandSqlAuthorityError(
                "authority_ref must start with sql-authority:"
            )
        self._connection = connection
        self._policy = policy or SqlContextStorePolicy()
        self._authority_ref = authority_ref

    @property
    def authority_ref(self) -> str:
        return self._authority_ref

    def initialize_schema(self) -> None:
        """Create the normalized command authority schema idempotently."""

        statements = (
            """
            CREATE TABLE IF NOT EXISTS scheduler_commands (
                command_ref TEXT PRIMARY KEY,
                command_schema TEXT NOT NULL,
                command_kind TEXT NOT NULL,
                command_digest TEXT NOT NULL UNIQUE,
                issued_at TEXT NOT NULL,
                priority INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_command_authorizations (
                command_ref TEXT PRIMARY KEY,
                authorization_schema TEXT NOT NULL,
                policy_decision_id TEXT NOT NULL UNIQUE,
                policy_ref TEXT NOT NULL,
                decision_digest TEXT NOT NULL,
                decision TEXT NOT NULL,
                automatic BOOLEAN NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_command_github_correlations (
                command_ref TEXT PRIMARY KEY,
                repository TEXT NOT NULL,
                issue_number INTEGER NOT NULL,
                run_id TEXT NOT NULL,
                conversation_ref TEXT NOT NULL,
                return_route_ref TEXT NOT NULL,
                UNIQUE (repository, issue_number, run_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_command_research_payloads (
                command_ref TEXT PRIMARY KEY,
                work_package_ref TEXT NOT NULL,
                route_candidate_ref TEXT NOT NULL,
                requested_status TEXT NOT NULL,
                request_mode TEXT NOT NULL,
                parent_event_ref TEXT NOT NULL,
                context_generation INTEGER NOT NULL,
                admissibility_digest TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_command_context_refs (
                command_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                context_ref TEXT NOT NULL,
                PRIMARY KEY (command_ref, ordinal),
                UNIQUE (command_ref, context_ref)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_command_evidence_refs (
                command_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                evidence_ref TEXT NOT NULL,
                PRIMARY KEY (command_ref, ordinal),
                UNIQUE (command_ref, evidence_ref)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_command_execution_budgets (
                command_ref TEXT PRIMARY KEY,
                max_scheduler_steps INTEGER NOT NULL,
                max_specialist_visits INTEGER NOT NULL,
                max_wall_time_s DOUBLE PRECISION NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_command_route_requests (
                command_ref TEXT PRIMARY KEY,
                route_request_schema TEXT NOT NULL,
                request_id TEXT NOT NULL UNIQUE,
                route_id TEXT NOT NULL,
                task_id TEXT NOT NULL UNIQUE,
                holder TEXT NOT NULL,
                scope TEXT NOT NULL,
                authorized BOOLEAN NOT NULL,
                policy_decision_id TEXT NOT NULL,
                ttl_seconds INTEGER NOT NULL,
                activate BOOLEAN NOT NULL,
                requested_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheduler_command_states (
                command_ref TEXT PRIMARY KEY,
                state_schema TEXT NOT NULL,
                state TEXT NOT NULL,
                state_version INTEGER NOT NULL,
                updated_at TEXT NOT NULL,
                claimed_by TEXT NOT NULL,
                claimed_at TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                failed_at TEXT NOT NULL,
                last_error_code TEXT NOT NULL
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_scheduler_commands_priority
            ON scheduler_commands(priority, issued_at, command_ref)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_scheduler_command_states_pending
            ON scheduler_command_states(state, updated_at, command_ref)
            """,
        )
        for statement in statements:
            self._execute(statement)
        self._commit_if_needed()

    def put_command(
        self,
        command: GitHubResearchSchedulerCommand,
    ) -> SchedulerCommandSqlWriteResult:
        """Insert one immutable command or acknowledge an exact replay."""

        if not isinstance(command, GitHubResearchSchedulerCommand):
            raise GitHubResearchSchedulerCommandSqlAuthorityError(
                "command must be a GitHubResearchSchedulerCommand"
            )
        existing = self.get_command(command.command_ref)
        if existing is not None:
            return self._replay_or_collision(existing, command)

        try:
            self._insert_command_graph(command)
            self._commit_if_needed()
        except Exception as exc:
            self._rollback_if_possible()
            try:
                concurrent = self.get_command(command.command_ref)
            except Exception:  # noqa: BLE001 - preserve sanitized failure
                concurrent = None
            if concurrent is not None:
                return self._replay_or_collision(concurrent, command)
            raise GitHubResearchSchedulerCommandSqlAuthorityError(
                "Scheduler command SQL insertion failed "
                f"({type(exc).__name__})"
            ) from None

        return SchedulerCommandSqlWriteResult(
            schema=COMMAND_WRITE_RESULT_SCHEMA,
            command_ref=command.command_ref,
            command_digest=command.command_digest,
            authority_ref=self._authority_ref,
            inserted=True,
            idempotent_replay=False,
        )

    def get_command(
        self,
        command_ref: str,
    ) -> GitHubResearchSchedulerCommand | None:
        """Reconstruct the immutable typed command from normalized rows."""

        p = self._placeholder
        root = self._fetchone(
            "SELECT command_schema, command_ref, command_digest, issued_at, "
            "priority FROM scheduler_commands "
            f"WHERE command_ref = {p}",
            (command_ref,),
        )
        if root is None:
            return None

        authorization = self._required_row(
            "SELECT authorization_schema, policy_decision_id, policy_ref, "
            "decision_digest, decision, automatic "
            "FROM scheduler_command_authorizations "
            f"WHERE command_ref = {p}",
            (command_ref,),
            "authorization",
        )
        correlation = self._required_row(
            "SELECT repository, issue_number, run_id, conversation_ref, "
            "return_route_ref FROM scheduler_command_github_correlations "
            f"WHERE command_ref = {p}",
            (command_ref,),
            "GitHub correlation",
        )
        research = self._required_row(
            "SELECT work_package_ref, route_candidate_ref, requested_status, "
            "request_mode, parent_event_ref, context_generation, "
            "admissibility_digest FROM scheduler_command_research_payloads "
            f"WHERE command_ref = {p}",
            (command_ref,),
            "research payload",
        )
        budget = self._required_row(
            "SELECT max_scheduler_steps, max_specialist_visits, "
            "max_wall_time_s FROM scheduler_command_execution_budgets "
            f"WHERE command_ref = {p}",
            (command_ref,),
            "execution budget",
        )
        route = self._required_row(
            "SELECT route_request_schema, request_id, route_id, task_id, "
            "holder, scope, authorized, policy_decision_id, ttl_seconds, "
            "activate, requested_at FROM scheduler_command_route_requests "
            f"WHERE command_ref = {p}",
            (command_ref,),
            "route request",
        )
        context_refs = tuple(
            str(row[0])
            for row in self._fetchall(
                "SELECT context_ref FROM scheduler_command_context_refs "
                f"WHERE command_ref = {p} ORDER BY ordinal",
                (command_ref,),
            )
        )
        evidence_refs = tuple(
            str(row[0])
            for row in self._fetchall(
                "SELECT evidence_ref FROM scheduler_command_evidence_refs "
                f"WHERE command_ref = {p} ORDER BY ordinal",
                (command_ref,),
            )
        )

        return GitHubResearchSchedulerCommand(
            schema=str(root[0]),
            command_ref=str(root[1]),
            command_digest=str(root[2]),
            issued_at=str(root[3]),
            priority=int(root[4]),
            authorization=SchedulerAuthorization(
                schema=str(authorization[0]),
                policy_decision_id=str(authorization[1]),
                policy_ref=str(authorization[2]),
                decision_digest=str(authorization[3]),
                decision=str(authorization[4]),
                automatic=bool(authorization[5]),
            ),
            correlation=GitHubResearchCorrelation(
                repository=str(correlation[0]),
                issue_number=int(correlation[1]),
                run_id=str(correlation[2]),
                conversation_ref=str(correlation[3]),
                return_route_ref=str(correlation[4]),
            ),
            research=GitHubResearchPayload(
                work_package_ref=str(research[0]),
                route_candidate_ref=str(research[1]),
                requested_status=str(research[2]),
                request_mode=str(research[3]),
                parent_event_ref=str(research[4]),
                context_generation=int(research[5]),
                context_refs=context_refs,
                evidence_refs=evidence_refs,
                admissibility_digest=str(research[6]),
            ),
            execution_budget=ResearchExecutionBudget(
                max_scheduler_steps=int(budget[0]),
                max_specialist_visits=int(budget[1]),
                max_wall_time_s=float(budget[2]),
            ),
            route_request=SchedulerRouteRequest(
                schema=str(route[0]),
                request_id=str(route[1]),
                route_id=str(route[2]),
                task_id=str(route[3]),
                holder=str(route[4]),
                scope=str(route[5]),
                authorized=bool(route[6]),
                policy_decision_id=str(route[7]),
                ttl_seconds=int(route[8]),
                activate=bool(route[9]),
                requested_at=str(route[10]),
            ),
        )

    def get_state(self, command_ref: str) -> SchedulerCommandSqlState | None:
        p = self._placeholder
        row = self._fetchone(
            "SELECT state_schema, command_ref, state, state_version, "
            "updated_at, claimed_by, claimed_at, started_at, completed_at, "
            "failed_at, last_error_code FROM scheduler_command_states "
            f"WHERE command_ref = {p}",
            (command_ref,),
        )
        if row is None:
            return None
        return SchedulerCommandSqlState(
            schema=str(row[0]),
            command_ref=str(row[1]),
            state=str(row[2]),
            state_version=int(row[3]),
            updated_at=str(row[4]),
            claimed_by=str(row[5]),
            claimed_at=str(row[6]),
            started_at=str(row[7]),
            completed_at=str(row[8]),
            failed_at=str(row[9]),
            last_error_code=str(row[10]),
        )

    def list_pending_command_refs(self, *, limit: int = 100) -> tuple[str, ...]:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise GitHubResearchSchedulerCommandSqlAuthorityError(
                "limit must be a positive integer"
            )
        p = self._placeholder
        rows = self._fetchall(
            "SELECT c.command_ref FROM scheduler_commands c "
            "JOIN scheduler_command_states s "
            "ON s.command_ref = c.command_ref "
            f"WHERE s.state = {p} "
            "ORDER BY c.priority DESC, c.issued_at, c.command_ref "
            f"LIMIT {p}",
            ("pending", limit),
        )
        return tuple(str(row[0]) for row in rows)

    def _insert_command_graph(
        self,
        command: GitHubResearchSchedulerCommand,
    ) -> None:
        self._insert(
            "scheduler_commands",
            (
                "command_ref",
                "command_schema",
                "command_kind",
                "command_digest",
                "issued_at",
                "priority",
            ),
            (
                command.command_ref,
                command.schema,
                "github-research",
                command.command_digest,
                command.issued_at,
                command.priority,
            ),
        )
        authorization = command.authorization
        self._insert(
            "scheduler_command_authorizations",
            (
                "command_ref",
                "authorization_schema",
                "policy_decision_id",
                "policy_ref",
                "decision_digest",
                "decision",
                "automatic",
            ),
            (
                command.command_ref,
                authorization.schema,
                authorization.policy_decision_id,
                authorization.policy_ref,
                authorization.decision_digest,
                authorization.decision,
                authorization.automatic,
            ),
        )
        correlation = command.correlation
        self._insert(
            "scheduler_command_github_correlations",
            (
                "command_ref",
                "repository",
                "issue_number",
                "run_id",
                "conversation_ref",
                "return_route_ref",
            ),
            (
                command.command_ref,
                correlation.repository,
                correlation.issue_number,
                correlation.run_id,
                correlation.conversation_ref,
                correlation.return_route_ref,
            ),
        )
        research = command.research
        self._insert(
            "scheduler_command_research_payloads",
            (
                "command_ref",
                "work_package_ref",
                "route_candidate_ref",
                "requested_status",
                "request_mode",
                "parent_event_ref",
                "context_generation",
                "admissibility_digest",
            ),
            (
                command.command_ref,
                research.work_package_ref,
                research.route_candidate_ref,
                research.requested_status,
                research.request_mode,
                research.parent_event_ref,
                research.context_generation,
                research.admissibility_digest,
            ),
        )
        for ordinal, context_ref in enumerate(research.context_refs):
            self._insert(
                "scheduler_command_context_refs",
                ("command_ref", "ordinal", "context_ref"),
                (command.command_ref, ordinal, context_ref),
            )
        for ordinal, evidence_ref in enumerate(research.evidence_refs):
            self._insert(
                "scheduler_command_evidence_refs",
                ("command_ref", "ordinal", "evidence_ref"),
                (command.command_ref, ordinal, evidence_ref),
            )
        budget = command.execution_budget
        self._insert(
            "scheduler_command_execution_budgets",
            (
                "command_ref",
                "max_scheduler_steps",
                "max_specialist_visits",
                "max_wall_time_s",
            ),
            (
                command.command_ref,
                budget.max_scheduler_steps,
                budget.max_specialist_visits,
                float(budget.max_wall_time_s),
            ),
        )
        route = command.route_request
        self._insert(
            "scheduler_command_route_requests",
            (
                "command_ref",
                "route_request_schema",
                "request_id",
                "route_id",
                "task_id",
                "holder",
                "scope",
                "authorized",
                "policy_decision_id",
                "ttl_seconds",
                "activate",
                "requested_at",
            ),
            (
                command.command_ref,
                route.schema,
                route.request_id,
                route.route_id,
                route.task_id,
                route.holder,
                route.scope,
                route.authorized,
                route.policy_decision_id,
                route.ttl_seconds,
                route.activate,
                route.requested_at,
            ),
        )
        self._insert(
            "scheduler_command_states",
            (
                "command_ref",
                "state_schema",
                "state",
                "state_version",
                "updated_at",
                "claimed_by",
                "claimed_at",
                "started_at",
                "completed_at",
                "failed_at",
                "last_error_code",
            ),
            (
                command.command_ref,
                SCHEDULER_COMMAND_STATE_SCHEMA,
                "pending",
                1,
                command.issued_at,
                "",
                "",
                "",
                "",
                "",
                "",
            ),
        )

    def _replay_or_collision(
        self,
        existing: GitHubResearchSchedulerCommand,
        command: GitHubResearchSchedulerCommand,
    ) -> SchedulerCommandSqlWriteResult:
        if existing != command:
            raise GitHubResearchSchedulerCommandSqlAuthorityError(
                "immutable Scheduler command collision"
            )
        return SchedulerCommandSqlWriteResult(
            schema=COMMAND_WRITE_RESULT_SCHEMA,
            command_ref=command.command_ref,
            command_digest=command.command_digest,
            authority_ref=self._authority_ref,
            inserted=False,
            idempotent_replay=True,
        )

    @property
    def _placeholder(self) -> str:
        return "?" if self._policy.paramstyle == "qmark" else "%s"

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

    def _fetchall(
        self,
        sql: str,
        parameters: Sequence[object],
    ) -> Sequence[Sequence[object]]:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
            return cursor.fetchall()
        finally:
            cursor.close()

    def _required_row(
        self,
        sql: str,
        parameters: Sequence[object],
        label: str,
    ) -> Sequence[object]:
        row = self._fetchone(sql, parameters)
        if row is None:
            raise GitHubResearchSchedulerCommandSqlAuthorityError(
                f"incomplete Scheduler command authority: missing {label}"
            )
        return row

    def _commit_if_needed(self) -> None:
        if self._policy.auto_commit:
            self._connection.commit()

    def _rollback_if_possible(self) -> None:
        rollback = getattr(self._connection, "rollback", None)
        if callable(rollback):
            rollback()


__all__ = (
    "DEFAULT_SCHEDULER_COMMAND_AUTHORITY_REF",
    "SCHEDULER_COMMAND_SQL_AUTHORITY_VERSION",
    "SCHEDULER_COMMAND_STATE_SCHEMA",
    "DbApiGitHubResearchSchedulerCommandStore",
    "GitHubResearchSchedulerCommandSqlAuthorityError",
    "SchedulerCommandSqlState",
)
