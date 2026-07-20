from __future__ import annotations

from context.github_research_love_externally_managed_installed_composition_0287 import (
    EXTERNALLY_MANAGED_COMPONENTS_SCHEMA,
    GitHubResearchLoveExternallyManagedInstalledComponents,
    GitHubResearchLoveExternallyManagedInstalledCompositionError,
    compose_github_research_love_externally_managed_service,
)
from context.github_research_love_openrc_scheduler_service_0287 import (
    OpenRcSchedulerServiceSettings,
)
from context.love_installed_runtime_factory_0287 import (
    INSTALLED_RUNTIME_FACTORY_SCHEMA,
    InstalledRuntimeFactorySettings,
)


class Scheduler:
    running = False

    async def run(self) -> None:
        self.running = True

    async def shutdown(self) -> None:
        self.running = False


class CommandStore:
    def claim_next_pending(self, *, scheduler_ref: str, claimed_at: str):
        del scheduler_ref, claimed_at
        return None


class ContinuationStore:
    def load_snapshot(self, **kwargs):
        raise AssertionError(kwargs)

    def commit_promotion(self, **kwargs):
        raise AssertionError(kwargs)


class ObservationStore:
    initialized = False

    def initialize_schema(self) -> None:
        self.initialized = True

    def append_many(self, observations) -> int:
        return len(tuple(observations))


class Provider:
    def load(self, **kwargs):
        raise AssertionError(kwargs)

    def load_first_dispatch_command(self, **kwargs):
        raise AssertionError(kwargs)

    def load_second_dispatch_command(self, **kwargs):
        raise AssertionError(kwargs)

    def load_pair_stage_input(self, **kwargs):
        raise AssertionError(kwargs)

    def load_recall_command(self, **kwargs):
        raise AssertionError(kwargs)

    def load_synthesis_command(self, **kwargs):
        raise AssertionError(kwargs)

    def load_final_deliverable_command(self, **kwargs):
        raise AssertionError(kwargs)

    def load_publication_command(self, **kwargs):
        raise AssertionError(kwargs)

    def load_publication_authorization(self, **kwargs):
        raise AssertionError(kwargs)

    def load_cycle_closure_result(self, **kwargs):
        raise AssertionError(kwargs)


class StepRunner:
    async def run_ready_task(self, **kwargs):
        raise AssertionError(kwargs)


def _settings(lifecycle: str = "externally-managed") -> InstalledRuntimeFactorySettings:
    return InstalledRuntimeFactorySettings(
        schema=INSTALLED_RUNTIME_FACTORY_SCHEMA,
        config_path="/tmp/love.ini",
        provider_ref="context.real:build",
        runtime_ref="runtime:love-installed",
        scheduler_ref="scheduler:main",
        scheduler_lifecycle=lifecycle,
        sql_authority_ref="sql-authority:postgresql-love",
        projection_backend_ref="projection:qdrant-live",
        embedding_backend_ref="openvino:multilingual-e5-small",
        retrieval_backend_ref="qdrant:hybrid-live",
        model_ref="model:intfloat-multilingual-e5-small",
        model_revision="main",
        qdrant_collection="autodoc-love",
        base_revision_ref="context-revision:base",
        evidence_refs=("evidence:installed-runtime",),
    )


def _components() -> GitHubResearchLoveExternallyManagedInstalledComponents:
    provider = Provider()
    observation = ObservationStore()

    def build_step_runner(**kwargs):
        assert len(kwargs["bootstrap"].handler_refs) == 10
        assert kwargs["scheduler_ref"] == "scheduler:main"
        assert kwargs["information_sink"].scheduler_ref == "scheduler:main"
        return StepRunner()

    return GitHubResearchLoveExternallyManagedInstalledComponents(
        schema=EXTERNALLY_MANAGED_COMPONENTS_SCHEMA,
        scheduler=Scheduler(),
        scheduler_ref="scheduler:main",
        command_store=CommandStore(),
        continuation_store=ContinuationStore(),
        step_runner_builder=build_step_runner,
        first_visit_input_provider=provider,
        grouped_input_provider=provider,
        downstream_input_provider=provider,
        publication_input_provider=provider,
        observation_store=observation,
        close_callbacks=(lambda: None,),
        evidence_refs=("evidence:externally-managed-components",),
    )


def test_composition_builds_one_service_with_ten_handlers() -> None:
    components = _components()
    bundle = compose_github_research_love_externally_managed_service(
        settings=_settings(),
        components=components,
        service_settings=OpenRcSchedulerServiceSettings(
            scheduler_ref="scheduler:main"
        ),
        clock=lambda: "2026-07-20T08:00:00Z",
    )

    assert bundle.service.scheduler is components.scheduler
    assert bundle.service.runtime.scheduler is components.scheduler
    assert len(bundle.service.runtime.bootstrap.handler_refs) == 10
    assert len(bundle.service.runtime.bootstrap.capability_refs) == 10
    assert components.observation_store.initialized is True
    assert bundle.evidence_refs == (
        "evidence:installed-runtime",
        "evidence:externally-managed-components",
    )


def test_tool_bounded_configuration_is_rejected() -> None:
    try:
        compose_github_research_love_externally_managed_service(
            settings=_settings("tool-bounded"),
            components=_components(),
            service_settings=OpenRcSchedulerServiceSettings(
                scheduler_ref="scheduler:main"
            ),
        )
    except GitHubResearchLoveExternallyManagedInstalledCompositionError as exc:
        assert "externally-managed" in str(exc)
    else:
        raise AssertionError("tool-bounded composition should fail closed")


def test_scheduler_reference_mismatch_is_rejected() -> None:
    try:
        compose_github_research_love_externally_managed_service(
            settings=_settings(),
            components=_components(),
            service_settings=OpenRcSchedulerServiceSettings(
                scheduler_ref="scheduler:other"
            ),
        )
    except GitHubResearchLoveExternallyManagedInstalledCompositionError as exc:
        assert "scheduler_ref" in str(exc)
    else:
        raise AssertionError("divergent Scheduler identity should fail closed")
