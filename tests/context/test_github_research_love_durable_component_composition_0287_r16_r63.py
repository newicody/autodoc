from context.github_research_love_externally_managed_durable_component_composition_0287 import (
    EXTERNALLY_MANAGED_EXECUTION_COMPONENTS_SCHEMA,
    GitHubResearchLoveExternallyManagedExecutionComponents,
)


class Continuation:
    def load_snapshot(self, **kwargs):
        return kwargs

    def commit_promotion(self, **kwargs):
        return kwargs


class First:
    def load(self, **kwargs):
        return kwargs


class Grouped:
    def load_first_dispatch_command(self, **kwargs):
        return kwargs

    def load_second_dispatch_command(self, **kwargs):
        return kwargs

    def load_pair_stage_input(self, **kwargs):
        return kwargs


class Downstream:
    def load_recall_command(self, **kwargs):
        return kwargs

    def load_synthesis_command(self, **kwargs):
        return kwargs

    def load_final_deliverable_command(self, **kwargs):
        return kwargs


class Publication:
    def load_publication_command(self, **kwargs):
        return kwargs

    def load_publication_authorization(self, **kwargs):
        return kwargs

    def load_cycle_closure_result(self, **kwargs):
        return kwargs


def test_execution_bundle_requires_the_six_non_observation_ports() -> None:
    value = GitHubResearchLoveExternallyManagedExecutionComponents(
        schema=EXTERNALLY_MANAGED_EXECUTION_COMPONENTS_SCHEMA,
        continuation_store=Continuation(),
        step_runner_builder=lambda **kwargs: kwargs,
        first_visit_input_provider=First(),
        grouped_input_provider=Grouped(),
        downstream_input_provider=Downstream(),
        publication_input_provider=Publication(),
        evidence_refs=("evidence:test-r16-r63",),
    )
    mapping = value.to_mapping()
    assert mapping["component_count"] == 6
    assert mapping["foundation_reused"] is True
    assert mapping["postgresql_connection_reused"] is True
    assert mapping["new_backend_opened"] is False
