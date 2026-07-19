"""Persistance relationnelle atomique de la fin d'un handler Scheduler."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from kernel.scheduler_handler_execution import SchedulerHandlerExecutionOutcome
from kernel.scheduler_handler_execution_completion import SchedulerHandlerExecutionCommit


class SchedulerHandlerExecutionSqlAuthorityError(RuntimeError):
    pass


class _Cursor(Protocol):
    rowcount: int
    def execute(self, sql: str, parameters: Sequence[object] = ()) -> object: ...
    def fetchone(self) -> Sequence[object] | None: ...
    def fetchall(self) -> Sequence[Sequence[object]]: ...
    def close(self) -> object: ...


class _Connection(Protocol):
    def cursor(self) -> _Cursor: ...
    def commit(self) -> object: ...
    def rollback(self) -> object: ...


class DbApiSchedulerHandlerExecutionTransaction:
    def __init__(self, connection: _Connection, *, paramstyle: str = "format") -> None:
        if paramstyle not in {"format", "qmark"}:
            raise SchedulerHandlerExecutionSqlAuthorityError("paramstyle invalide")
        if getattr(connection, "autocommit", False) is True:
            raise SchedulerHandlerExecutionSqlAuthorityError("autocommit interdit")
        self._connection = connection
        self._paramstyle = paramstyle

    @property
    def _p(self) -> str:
        return "?" if self._paramstyle == "qmark" else "%s"

    def initialize_schema(self) -> None:
        statements = (
            "CREATE TABLE IF NOT EXISTS scheduler_task_results (result_ref TEXT PRIMARY KEY, task_ref TEXT NOT NULL, attempt_ref TEXT NOT NULL UNIQUE, result_type_ref TEXT NOT NULL, completed_at TEXT NOT NULL, result_digest TEXT NOT NULL UNIQUE)",
            "CREATE TABLE IF NOT EXISTS scheduler_task_result_evidence_refs (result_ref TEXT NOT NULL, ordinal INTEGER NOT NULL, evidence_ref TEXT NOT NULL, PRIMARY KEY(result_ref, ordinal), UNIQUE(result_ref, evidence_ref))",
            "CREATE TABLE IF NOT EXISTS scheduler_task_failures (failure_ref TEXT PRIMARY KEY, task_ref TEXT NOT NULL, attempt_ref TEXT NOT NULL UNIQUE, error_type TEXT NOT NULL, message TEXT NOT NULL, retryable BOOLEAN NOT NULL, failed_at TEXT NOT NULL, failure_digest TEXT NOT NULL UNIQUE)",
            "CREATE TABLE IF NOT EXISTS scheduler_task_failure_evidence_refs (failure_ref TEXT NOT NULL, ordinal INTEGER NOT NULL, evidence_ref TEXT NOT NULL, PRIMARY KEY(failure_ref, ordinal), UNIQUE(failure_ref, evidence_ref))",
            "CREATE TABLE IF NOT EXISTS scheduler_task_interruptions (transition_ref TEXT PRIMARY KEY, task_ref TEXT NOT NULL, attempt_ref TEXT NOT NULL UNIQUE, interruption_kind TEXT NOT NULL, occurred_at TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS scheduler_handler_execution_transactions (transaction_ref TEXT PRIMARY KEY, scheduler_ref TEXT NOT NULL, command_ref TEXT NOT NULL, task_ref TEXT NOT NULL, attempt_ref TEXT NOT NULL UNIQUE, reservation_ref TEXT NOT NULL UNIQUE, outcome_ref TEXT NOT NULL UNIQUE, outcome_digest TEXT NOT NULL UNIQUE, terminal_ref TEXT NOT NULL, task_state TEXT NOT NULL, task_state_version INTEGER NOT NULL, close_succeeded BOOLEAN NOT NULL, released_at TEXT NOT NULL, commit_digest TEXT NOT NULL UNIQUE)",
        )
        try:
            for sql in statements: self._execute(sql)
            self._connection.commit()
        except Exception as exc:
            self._rollback(); raise SchedulerHandlerExecutionSqlAuthorityError(f"initialisation impossible ({type(exc).__name__})") from None

    def commit_outcome(self, *, outcome: SchedulerHandlerExecutionOutcome[object], released_at: str) -> SchedulerHandlerExecutionCommit:
        ticket = outcome.lease.created.ticket
        expected = SchedulerHandlerExecutionCommit.create(
            scheduler_ref=ticket.scheduler_ref, command_ref=ticket.task_running.command_ref,
            task_ref=ticket.task_running.task_ref, attempt_ref=ticket.attempt.attempt_ref,
            reservation_ref=ticket.reservation.reservation_ref, outcome_ref=outcome.outcome_ref,
            task_state=outcome.task_state.value, task_state_version=self._terminal_task(outcome).state_version,
            released_at=released_at,
        )
        replay = self._load(expected.transaction_ref)
        if replay is not None:
            if replay != expected: raise SchedulerHandlerExecutionSqlAuthorityError("collision de reçu")
            return replay
        try:
            self._validate_launch(outcome)
            self._persist_terminal_payload(outcome)
            self._update_attempt(outcome)
            self._update_task(outcome)
            self._insert_transition(outcome)
            self._release_resources(outcome, released_at)
            self._touch_command(outcome, released_at)
            self._insert("scheduler_handler_execution_transactions",
                ("transaction_ref","scheduler_ref","command_ref","task_ref","attempt_ref","reservation_ref","outcome_ref","outcome_digest","terminal_ref","task_state","task_state_version","close_succeeded","released_at","commit_digest"),
                (expected.transaction_ref,expected.scheduler_ref,expected.command_ref,expected.task_ref,expected.attempt_ref,expected.reservation_ref,outcome.outcome_ref,outcome.outcome_digest,outcome.terminal_ref,expected.task_state,expected.task_state_version,outcome.close_receipt.closed,released_at,expected.commit_digest))
            self._connection.commit(); return expected
        except SchedulerHandlerExecutionSqlAuthorityError:
            self._rollback(); raise
        except Exception as exc:
            self._rollback(); raise SchedulerHandlerExecutionSqlAuthorityError(f"transaction de fin annulée ({type(exc).__name__})") from None

    def _terminal_bundle(self, outcome):
        return outcome.completion or outcome.failure_outcome or outcome.interruption
    def _terminal_task(self, outcome): return self._terminal_bundle(outcome).task
    def _terminal_attempt(self, outcome): return self._terminal_bundle(outcome).attempt
    def _terminal_transition(self, outcome): return self._terminal_bundle(outcome).transition

    def _validate_launch(self, outcome) -> None:
        ticket = outcome.lease.created.ticket
        row = self._fetchone("SELECT scheduler_ref, command_ref, task_ref, attempt_ref, reservation_ref FROM scheduler_task_launch_transactions WHERE transaction_ref = " + self._p, (ticket.launch_commit.transaction_ref,))
        expected = (ticket.scheduler_ref, ticket.task_running.command_ref, ticket.task_running.task_ref, ticket.attempt.attempt_ref, ticket.reservation.reservation_ref)
        if row is None or tuple(map(str,row)) != expected: raise SchedulerHandlerExecutionSqlAuthorityError("lancement SQL divergent")

    def _persist_terminal_payload(self, outcome) -> None:
        if outcome.completion is not None:
            r=outcome.completion.result
            self._insert("scheduler_task_results",("result_ref","task_ref","attempt_ref","result_type_ref","completed_at","result_digest"),(r.result_ref,r.task_ref,r.attempt_ref,r.result_type_ref,r.completed_at,r.result_digest))
            for i,ref in enumerate(r.evidence_refs): self._insert("scheduler_task_result_evidence_refs",("result_ref","ordinal","evidence_ref"),(r.result_ref,i,ref))
        elif outcome.failure_outcome is not None:
            f=outcome.failure_outcome.failure
            self._insert("scheduler_task_failures",("failure_ref","task_ref","attempt_ref","error_type","message","retryable","failed_at","failure_digest"),(f.failure_ref,f.task_ref,f.attempt_ref,f.error_type,f.message,f.retryable,f.failed_at,f.failure_digest))
            for i,ref in enumerate(f.evidence_refs): self._insert("scheduler_task_failure_evidence_refs",("failure_ref","ordinal","evidence_ref"),(f.failure_ref,i,ref))
        else:
            t=self._terminal_transition(outcome)
            self._insert("scheduler_task_interruptions",("transition_ref","task_ref","attempt_ref","interruption_kind","occurred_at"),(t.transition_ref,t.task_ref,self._terminal_attempt(outcome).attempt_ref,outcome.status.value,t.occurred_at))

    def _update_attempt(self, outcome) -> None:
        before=outcome.lease.created.ticket.attempt; after=self._terminal_attempt(outcome)
        changed=self._count("UPDATE scheduler_task_attempts SET state="+self._p+", finished_at="+self._p+", result_ref="+self._p+", failure_ref="+self._p+" WHERE attempt_ref="+self._p+" AND state="+self._p+" AND finished_at=''",(after.state.value,after.finished_at,after.result_ref,after.failure_ref,before.attempt_ref,"running"))
        if changed != 1: raise SchedulerHandlerExecutionSqlAuthorityError("conflit de tentative")

    def _update_task(self, outcome) -> None:
        before=outcome.lease.created.ticket.task_running; after=self._terminal_task(outcome)
        changed=self._count("UPDATE scheduler_tasks SET state="+self._p+", state_version="+self._p+", updated_at="+self._p+", task_digest="+self._p+" WHERE task_ref="+self._p+" AND state="+self._p+" AND state_version="+self._p+" AND task_digest="+self._p,(after.state.value,after.state_version,after.updated_at,after.task_digest,before.task_ref,before.state.value,before.state_version,before.task_digest))
        if changed != 1: raise SchedulerHandlerExecutionSqlAuthorityError("conflit de tâche")

    def _insert_transition(self, outcome) -> None:
        t=self._terminal_transition(outcome)
        self._insert("scheduler_task_transitions",("transition_ref","task_ref","from_state","to_state","state_version","occurred_at","actor_ref","cause_ref","transition_digest"),(t.transition_ref,t.task_ref,t.from_state.value,t.to_state.value,t.state_version,t.occurred_at,t.actor_ref,t.cause_ref,t.transition_digest))

    def _release_resources(self, outcome, released_at: str) -> None:
        ref=outcome.lease.created.ticket.reservation.reservation_ref
        row=self._fetchone("SELECT status FROM scheduler_resource_reservations WHERE reservation_ref="+self._p,(ref,))
        if row is None or str(row[0]) != "active": raise SchedulerHandlerExecutionSqlAuthorityError("réservation non active")
        reqs=self._fetchall("SELECT resource_ref, amount FROM scheduler_resource_reservation_requirements WHERE reservation_ref="+self._p+" ORDER BY ordinal",(ref,))
        for resource_ref, amount in reqs:
            current=self._fetchone("SELECT reserved, state_version FROM scheduler_resource_inventory WHERE resource_ref="+self._p,(resource_ref,))
            if current is None or int(current[0]) < int(amount): raise SchedulerHandlerExecutionSqlAuthorityError("inventaire incohérent")
            changed=self._count("UPDATE scheduler_resource_inventory SET reserved="+self._p+", state_version=state_version+1, updated_at="+self._p+" WHERE resource_ref="+self._p+" AND reserved="+self._p+" AND state_version="+self._p,(int(current[0])-int(amount),released_at,resource_ref,int(current[0]),int(current[1])))
            if changed != 1: raise SchedulerHandlerExecutionSqlAuthorityError("conflit de libération")
        if self._count("UPDATE scheduler_resource_reservations SET status='released' WHERE reservation_ref="+self._p+" AND status='active'",(ref,)) != 1: raise SchedulerHandlerExecutionSqlAuthorityError("conflit de réservation")

    def _touch_command(self, outcome, released_at: str) -> None:
        ticket=outcome.lease.created.ticket
        if self._count("UPDATE scheduler_command_states SET updated_at="+self._p+" WHERE command_ref="+self._p+" AND state='running' AND claimed_by="+self._p,(released_at,ticket.task_running.command_ref,ticket.scheduler_ref)) != 1: raise SchedulerHandlerExecutionSqlAuthorityError("commande non possédée")

    def _load(self, transaction_ref: str):
        row=self._fetchone("SELECT scheduler_ref,command_ref,task_ref,attempt_ref,reservation_ref,outcome_ref,task_state,task_state_version,released_at FROM scheduler_handler_execution_transactions WHERE transaction_ref="+self._p,(transaction_ref,))
        if row is None: return None
        return SchedulerHandlerExecutionCommit.create(scheduler_ref=str(row[0]),command_ref=str(row[1]),task_ref=str(row[2]),attempt_ref=str(row[3]),reservation_ref=str(row[4]),outcome_ref=str(row[5]),task_state=str(row[6]),task_state_version=int(row[7]),released_at=str(row[8]))

    def _insert(self, table, columns, values): self._execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(self._p for _ in columns)})",values)
    def _execute(self, sql, params=()):
        c=self._connection.cursor()
        try: c.execute(sql,params)
        finally: c.close()
    def _count(self, sql, params):
        c=self._connection.cursor()
        try: c.execute(sql,params); return int(c.rowcount)
        finally: c.close()
    def _fetchone(self, sql, params):
        c=self._connection.cursor()
        try: c.execute(sql,params); return c.fetchone()
        finally: c.close()
    def _fetchall(self, sql, params):
        c=self._connection.cursor()
        try: c.execute(sql,params); return c.fetchall()
        finally: c.close()
    def _rollback(self):
        try: self._connection.rollback()
        except Exception: pass


__all__=["DbApiSchedulerHandlerExecutionTransaction","SchedulerHandlerExecutionSqlAuthorityError"]
