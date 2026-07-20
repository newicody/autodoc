from context.github_research_love_externally_managed_durable_port_factory_0287 import (
    EXTERNALLY_MANAGED_DURABLE_COMPONENTS_SCHEMA,
    GitHubResearchLoveExternallyManagedDurableComponents,
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


class Observation:
    def initialize_schema(self):
        return None

    def append_many(self, values):
        return len(values)


def test_typed_component_bundle_requires_all_seven_ports() -> None:
    value = GitHubResearchLoveExternallyManagedDurableComponents(
        schema=EXTERNALLY_MANAGED_DURABLE_COMPONENTS_SCHEMA,
        continuation_store=Continuation(),
        step_runner_builder=lambda **kwargs: kwargs,
        first_visit_input_provider=First(),
        grouped_input_provider=Grouped(),
        downstream_input_provider=Downstream(),
        publication_input_provider=Publication(),
        observation_store=Observation(),
        evidence_refs=("evidence:test-r16-r61",),
    )
    mapping = value.to_mapping()
    assert mapping["component_count"] == 7
    assert mapping["foundation_reused"] is True
    assert mapping["new_backend_opened"] is False
