from dataclasses import dataclass

import pytest

from context.github_research_scheduler_command_claim_0287 import (
    CanonicalSchedulerCommandClaimError,
    claim_next_for_running_canonical_scheduler,
)
from context.github_research_scheduler_command_sql_authority_0287 import (
    DbApiGitHubResearchSchedulerCommandStore,
)
from context.sql_context_store import SqlContextStorePolicy


@dataclass
class _Scheduler:
    running: bool


class _EmptyStore:
    def claim_next_pending(self, *, scheduler_ref: str, claimed_at: str):
        assert scheduler_ref.startswith("scheduler:")
        assert claimed_at.endswith("Z")
        return None


def test_running_scheduler_can_use_restored_claim_port() -> None:
    result = claim_next_for_running_canonical_scheduler(
        scheduler=_Scheduler(running=True),
        command_store=_EmptyStore(),
        scheduler_ref="scheduler:autodoc-local-canonical",
        claimed_at="2026-07-20T18:00:00Z",
    )
    assert result.status == "no-pending-command"
    assert result.claim is None


def test_stopped_scheduler_is_rejected_before_store_call() -> None:
    with pytest.raises(CanonicalSchedulerCommandClaimError):
        claim_next_for_running_canonical_scheduler(
            scheduler=_Scheduler(running=False),
            command_store=_EmptyStore(),
            scheduler_ref="scheduler:autodoc-local-canonical",
            claimed_at="2026-07-20T18:00:00Z",
        )


class _Cursor:
    def __init__(self, statements: list[str]) -> None:
        self.statements = statements
        self.rowcount = 0

    def execute(self, sql: str, parameters=()):
        self.statements.append(sql)

    def fetchone(self):
        return None

    def fetchall(self):
        return ()

    def close(self):
        return None


class _Connection:
    def __init__(self) -> None:
        self.statements: list[str] = []
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return _Cursor(self.statements)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_postgresql_claim_keeps_skip_locked_boundary() -> None:
    connection = _Connection()
    store = DbApiGitHubResearchSchedulerCommandStore(
        connection,
        SqlContextStorePolicy(paramstyle="format", auto_commit=True),
    )
    assert store.claim_next_pending(
        scheduler_ref="scheduler:autodoc-local-canonical",
        claimed_at="2026-07-20T18:00:00Z",
    ) is None
    sql = "\n".join(connection.statements)
    assert "FOR UPDATE OF s SKIP LOCKED" in sql
    assert "RETURNING s.command_ref" in sql
    assert connection.commits == 1
