from __future__ import annotations

from types import SimpleNamespace

import pytest

import context.github_research_love_externally_managed_component_binding_0287 as module


class _Scheduler:
    running = False

    async def run(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None


class _Continuation:
    def load_snapshot(self, **kwargs):
        return None

    def commit_promotion(self, **kwargs):
        return None


class _FirstProvider:
    def load(self, **kwargs):
        return None


class _GroupedProvider:
    def load_first_dispatch_command(self, **kwargs):
        return None

    def load_second_dispatch_command(self, **kwargs):
        return None

    def load_pair_stage_input(self, **kwargs):
        return None


class _DownstreamProvider:
    def load_recall_command(self, **kwargs):
        return None

    def load_synthesis_command(self, **kwargs):
        return None

    def load_final_deliverable_command(self, **kwargs):
        return None


class _PublicationProvider:
    def load_publication_command(self, **kwargs):
        return None

    def load_publication_authorization(self, **kwargs):
        return None

    def load_cycle_closure_result(self, **kwargs):
        return None


class _ObservationStore:
    def initialize_schema(self) -> None:
        return None

    def append_many(self, values) -> int:
        return len(values)


def _foundation(closed: list[str]):
    return SimpleNamespace(
        scheduler=_Scheduler(),
        scheduler_ref="scheduler:main",
        command_store=SimpleNamespace(claim_next_pending=lambda **kwargs: None),
        authority_store=object(),
        task_launch_transaction=object(),
        handler_execution_transaction=object(),
        projection_port=object(),
        collection=SimpleNamespace(collection_name="autodoc-love"),
        embedder=object(),
        retrieval_executor=object(),
        base_revision_ref="context-revision:love-root",
        close_callbacks=(
            lambda: closed.append("postgresql"),
            lambda: closed.append("qdrant"),
        ),
        evidence_refs=("evidence:foundation",),
    )


def _ports(*, collection_name: str = "autodoc-love"):
    return module.GitHubResearchLoveExternallyManagedDurablePorts(
        schema=module.EXTERNALLY_MANAGED_DURABLE_PORTS_SCHEMA,
        scheduler_ref="scheduler:main",
        base_revision_ref="context-revision:love-root",
        collection_name=collection_name,
        embedding_dimension=384,
        continuation_store=_Continuation(),
        step_runner_builder=lambda **kwargs: SimpleNamespace(
            run_ready_task=lambda **values: None
        ),
        first_visit_input_provider=_FirstProvider(),
        grouped_input_provider=_GroupedProvider(),
        downstream_input_provider=_DownstreamProvider(),
        publication_input_provider=_PublicationProvider(),
        observation_store=_ObservationStore(),
        evidence_refs=("evidence:durable-ports",),
    )


def _settings():
    return SimpleNamespace(config_path="/tmp/runtime.ini")


def test_binding_returns_r16_r58_components_without_new_backend(monkeypatch) -> None:
    closed: list[str] = []
    foundation = _foundation(closed)
    ports = _ports()
    monkeypatch.setattr(
        module,
        "build_love_externally_managed_installed_backend_foundation",
        lambda **kwargs: foundation,
    )
    monkeypatch.setattr(module, "_load_factory", lambda value: lambda **kwargs: ports)

    result = module.build_github_research_love_externally_managed_installed_components(
        settings=_settings(),
        environment={module.DURABLE_PORT_FACTORY_ENV: "installed:build"},
    )

    assert result.scheduler is foundation.scheduler
    assert result.command_store is foundation.command_store
    assert result.continuation_store is ports.continuation_store
    assert result.observation_store is ports.observation_store
    assert result.close_callbacks == foundation.close_callbacks
    assert result.evidence_refs == (
        "evidence:foundation",
        "evidence:durable-ports",
    )
    assert closed == []


def test_alignment_error_closes_foundation_in_reverse_order(monkeypatch) -> None:
    closed: list[str] = []
    foundation = _foundation(closed)
    ports = _ports(collection_name="wrong-collection")
    monkeypatch.setattr(
        module,
        "build_love_externally_managed_installed_backend_foundation",
        lambda **kwargs: foundation,
    )
    monkeypatch.setattr(module, "_load_factory", lambda value: lambda **kwargs: ports)

    with pytest.raises(
        module.GitHubResearchLoveExternallyManagedComponentBindingError,
        match="collection Qdrant",
    ):
        module.build_github_research_love_externally_managed_installed_components(
            settings=_settings(),
            environment={module.DURABLE_PORT_FACTORY_ENV: "installed:build"},
        )

    assert closed == ["qdrant", "postgresql"]


def test_missing_durable_factory_fails_closed(monkeypatch) -> None:
    closed: list[str] = []
    foundation = _foundation(closed)
    monkeypatch.setattr(
        module,
        "build_love_externally_managed_installed_backend_foundation",
        lambda **kwargs: foundation,
    )

    with pytest.raises(
        module.GitHubResearchLoveExternallyManagedComponentBindingError,
        match="fabrique de ports durables absente",
    ):
        module.build_github_research_love_externally_managed_installed_components(
            settings=_settings(),
            environment={},
        )

    assert closed == ["qdrant", "postgresql"]
