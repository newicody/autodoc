from __future__ import annotations

import pytest

from context import (
    github_research_love_externally_managed_postgresql_execution_core_0287 as module,
)
from context.love_externally_managed_installed_backend_foundation_0287 import (
    LoveExternallyManagedInstalledBackendFoundation,
)
from context.love_postgresql_shared_adapter_port_0287 import (
    LOVE_POSTGRESQL_SHARED_ADAPTER_PORT_SCHEMA,
    LovePostgreSqlSharedAdapterPort,
)


class _Connection:
    def cursor(self):
        return object()

    def commit(self):
        return None

    def rollback(self):
        return None


class _LaunchTransaction:
    def commit_launch(self, **kwargs):
        return kwargs


class _FinishTransaction:
    def commit_outcome(self, **kwargs):
        return kwargs


class _ContinuationStore:
    def __init__(
        self,
        connection,
        *,
        paramstyle,
        scheduler_ref,
        task_launch_transaction,
        handler_execution_transaction,
        **unused,
    ) -> None:
        self.connection = connection
        self.paramstyle = paramstyle
        self.scheduler_ref = scheduler_ref
        self.task_launch_transaction = task_launch_transaction
        self.handler_execution_transaction = handler_execution_transaction
        self.schema_initialized = False

    def initialize_schema(self) -> None:
        self.schema_initialized = True

    def load_snapshot(self, **kwargs):
        return kwargs

    def commit_promotion(self, **kwargs):
        return kwargs


class _Runner:
    def __init__(self, **values) -> None:
        self.values = values

    async def run_ready_task(self, **kwargs):
        return kwargs


def _foundation(
    *,
    port: LovePostgreSqlSharedAdapterPort,
    launch: object,
    finish: object,
) -> LoveExternallyManagedInstalledBackendFoundation:
    value = object.__new__(LoveExternallyManagedInstalledBackendFoundation)
    for name, item in {
        "scheduler": object(),
        "dispatcher": object(),
        "scheduler_ref": "scheduler:love-installed",
        "authority_store": object(),
        "postgresql_adapter_port": port,
        "command_store": object(),
        "task_launch_transaction": launch,
        "handler_execution_transaction": finish,
        "projection_port": object(),
        "embedder": object(),
        "retrieval_executor": object(),
    }.items():
        object.__setattr__(value, name, item)
    return value


def test_core_reuses_shared_connection_and_installed_transactions(
    monkeypatch,
) -> None:
    connection = _Connection()
    port = LovePostgreSqlSharedAdapterPort(
        schema=LOVE_POSTGRESQL_SHARED_ADAPTER_PORT_SCHEMA,
        sql_authority_ref="sql-authority:love-postgresql",
        paramstyle="format",
        _connection=connection,
    )
    launch = _LaunchTransaction()
    finish = _FinishTransaction()
    foundation = _foundation(port=port, launch=launch, finish=finish)

    def continuation_factory(connection, **kwargs):
        return _ContinuationStore(connection, **kwargs)

    def runner_factory(**kwargs):
        return _Runner(**kwargs)

    monkeypatch.setattr(
        module,
        "_load_required_factory",
        lambda environment, variable_name: (
            continuation_factory
            if variable_name == module.CONTINUATION_STORE_FACTORY_ENV
            else runner_factory
        ),
    )

    core = module.build_github_research_love_postgresql_execution_core(
        foundation=foundation,
        environment={},
    )

    assert core.adapter_port is port
    assert core.continuation_store.connection is connection
    assert core.continuation_store.schema_initialized is True
    assert core.task_launch_transaction is launch
    assert core.handler_execution_transaction is finish

    replacement_launch = object()
    runner = core.step_runner_builder(
        custom_ref="custom:test",
        task_launch_transaction=replacement_launch,
    )
    assert runner.values["task_launch_transaction"] is launch
    assert runner.values["handler_execution_transaction"] is finish
    assert runner.values["continuation_store"] is core.continuation_store
    assert runner.values["postgresql_adapter_port"] is port
    assert runner.values["custom_ref"] == "custom:test"

    mapping = core.to_mapping()
    assert mapping["postgresql_connection_reused"] is True
    assert mapping["task_launch_transaction_reused"] is True
    assert mapping["handler_execution_transaction_reused"] is True
    assert mapping["new_backend_opened"] is False


def test_missing_factory_fails_closed() -> None:
    with pytest.raises(
        module.GitHubResearchLovePostgreSqlExecutionCoreError,
        match=module.CONTINUATION_STORE_FACTORY_ENV,
    ):
        module._load_required_factory(
            {},
            module.CONTINUATION_STORE_FACTORY_ENV,
        )
