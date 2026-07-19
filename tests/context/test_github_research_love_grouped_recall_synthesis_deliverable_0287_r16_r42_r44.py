from __future__ import annotations

from context.github_research_love_grouped_recall_synthesis_deliverable_0287 import (
    BUILD_FINAL_DELIVERABLE_CAPABILITY_REF,
    RECALL_TWO_ANALYSES_CAPABILITY_REF,
    SYNTHESIZE_LIAISON_CAPABILITY_REF,
    build_github_research_love_complete_grouped_scheduler_bootstrap,
)


class _FirstVisitProvider:
    def load(self, **_kwargs):
        raise AssertionError("le bootstrap ne doit pas charger d'entrée")


class _GroupedProvider:
    def load_first_dispatch_command(self, **_kwargs):
        raise AssertionError

    def load_second_dispatch_command(self, **_kwargs):
        raise AssertionError

    def load_pair_stage_input(self, **_kwargs):
        raise AssertionError


class _DownstreamProvider:
    def load_recall_command(self, **_kwargs):
        raise AssertionError

    def load_synthesis_command(self, **_kwargs):
        raise AssertionError

    def load_final_deliverable_command(self, **_kwargs):
        raise AssertionError


def test_complete_grouped_bootstrap_catalogs_seven_local_capabilities() -> None:
    bootstrap = build_github_research_love_complete_grouped_scheduler_bootstrap(
        _FirstVisitProvider(),
        _GroupedProvider(),
        _DownstreamProvider(),
    )

    assert len(bootstrap.handler_refs) == 7
    assert len(bootstrap.capability_refs) == 7
    assert RECALL_TWO_ANALYSES_CAPABILITY_REF in bootstrap.capability_refs
    assert SYNTHESIZE_LIAISON_CAPABILITY_REF in bootstrap.capability_refs
    assert BUILD_FINAL_DELIVERABLE_CAPABILITY_REF in bootstrap.capability_refs
    assert not any("publish" in ref for ref in bootstrap.capability_refs)
    assert not any("close-cycle" in ref for ref in bootstrap.capability_refs)


def test_downstream_provider_is_explicitly_validated() -> None:
    try:
        build_github_research_love_complete_grouped_scheduler_bootstrap(
            _FirstVisitProvider(),
            _GroupedProvider(),
            object(),
        )
    except TypeError as exc:
        assert "load_recall_command" in str(exc)
    else:
        raise AssertionError("un fournisseur aval incomplet doit être refusé")
