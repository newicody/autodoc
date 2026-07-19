from __future__ import annotations

from types import SimpleNamespace

import context.love_postgresql_authority_binding_0287 as module


class _Connection:
    autocommit = False


class _AuthorityStore:
    def __init__(self, connection: object, policy: object) -> None:
        self.connection = connection
        self.policy = policy
        self.initialized = False
        self.close_count = 0

    def initialize_schema(self) -> None:
        self.initialized = True

    def close(self) -> None:
        self.close_count += 1


class _CommandStore:
    def __init__(self, connection: object, policy: object) -> None:
        self.connection = connection
        self.policy = policy
        self.initialized = False

    def initialize_schema(self) -> None:
        self.initialized = True


class _Transaction:
    def __init__(
        self,
        connection: object,
        *,
        paramstyle: str,
    ) -> None:
        self.connection = connection
        self.paramstyle = paramstyle
        self.initialized = False

    def initialize_schema(self) -> None:
        self.initialized = True


def _settings() -> SimpleNamespace:
    postgresql = SimpleNamespace(
        host="127.0.0.1",
        port=5432,
        database="autodoc",
        user="autodoc",
        password_env="AUTODOC_TEST_PASSWORD",
        sslmode="disable",
        connect_timeout_seconds=5,
        schema_name="autodoc",
    )
    return SimpleNamespace(
        runtime_ref="runtime:love-installed",
        sql_authority_ref="sql-authority:love-postgresql",
        base_revision_ref="context-revision:love-root",
        postgresql=postgresql,
    )


def test_binding_reuses_owned_connection_for_execution_completion(monkeypatch) -> None:
    connection = _Connection()
    prepared: list[tuple[object, object]] = []

    monkeypatch.setattr(module, "DbApiContextRevisionAuthorityStore", _AuthorityStore)
    monkeypatch.setattr(module, "DbApiGitHubResearchSchedulerCommandStore", _CommandStore)
    monkeypatch.setattr(module, "DbApiSchedulerTaskLaunchTransaction", _Transaction)
    monkeypatch.setattr(module, "DbApiSchedulerHandlerExecutionTransaction", _Transaction)
    monkeypatch.setattr(
        module,
        "_prepare_postgresql_schema",
        lambda value, settings: prepared.append((value, settings)),
    )
    monkeypatch.setattr(
        module,
        "ensure_love_base_revision",
        lambda authority_store, settings: module.LovePostgreSqlBaseRevisionSeedReceipt(
            schema=module.LOVE_POSTGRESQL_BASE_REVISION_SEED_SCHEMA,
            revision_ref="context-revision:love-root",
            context_ref="context:love-root",
            inserted=True,
            idempotent_replay=False,
        ),
    )

    binding = module.open_love_postgresql_authority(
        _settings(),
        connector=lambda **kwargs: connection,
        environment={"AUTODOC_TEST_PASSWORD": "secret"},
    )

    assert prepared and prepared[0][0] is connection
    assert binding.authority_store.connection is connection
    assert binding.scheduler_command_store is not None
    assert binding.scheduler_command_store.connection is connection
    launch = binding.scheduler_task_launch_transaction
    assert launch is not None
    assert launch.connection is connection
    completion = binding.scheduler_handler_execution_transaction
    assert completion is not None
    assert completion.connection is connection
    assert completion.paramstyle == "format"
    assert completion.initialized is True
    boundaries = binding.receipt.boundaries
    assert boundaries["scheduler_handler_execution_transaction_bound"] is True
    assert boundaries["scheduler_handler_execution_schema_initialized"] is True
    assert boundaries["scheduler_handler_execution_uses_owned_connection"] is True
    assert boundaries["scheduler_handler_execution_replayed"] is False

    binding.close()
    binding.close()
    assert binding.authority_store.close_count == 1
