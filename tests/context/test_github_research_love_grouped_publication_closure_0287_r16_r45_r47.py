from __future__ import annotations

from context.github_research_love_grouped_publication_closure_0287 import (
    CLOSE_CYCLE_CAPABILITY_REF,
    PREPARE_PUBLICATION_CAPABILITY_REF,
    PUBLISH_REMOTE_CAPABILITY_REF,
    ExplicitGitHubResearchLoveGroupedPublicationInputProvider,
    build_github_research_love_full_grouped_scheduler_bootstrap,
)


class _FirstVisitProvider:
    def load(self, **_kwargs):
        raise AssertionError


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


class _PublicationProvider:
    def load_publication_command(self, **_kwargs):
        raise AssertionError

    def load_publication_authorization(self, **_kwargs):
        raise AssertionError

    def load_cycle_closure_result(self, **_kwargs):
        raise AssertionError


def test_full_grouped_bootstrap_catalogs_ten_capabilities() -> None:
    bootstrap = build_github_research_love_full_grouped_scheduler_bootstrap(
        _FirstVisitProvider(),
        _GroupedProvider(),
        _DownstreamProvider(),
        _PublicationProvider(),
    )

    assert len(bootstrap.handler_refs) == 10
    assert len(bootstrap.capability_refs) == 10
    assert PREPARE_PUBLICATION_CAPABILITY_REF in bootstrap.capability_refs
    assert PUBLISH_REMOTE_CAPABILITY_REF in bootstrap.capability_refs
    assert CLOSE_CYCLE_CAPABILITY_REF in bootstrap.capability_refs


def test_explicit_publication_provider_delegates_three_loaders() -> None:
    calls: list[str] = []
    provider = ExplicitGitHubResearchLoveGroupedPublicationInputProvider(
        publication_command_loader=lambda **_kwargs: calls.append("plan"),
        publication_authorization_loader=lambda **_kwargs: calls.append("publish"),
        cycle_closure_loader=lambda **_kwargs: calls.append("close"),
    )

    provider.load_publication_command(command=object(), execution_context=object())
    provider.load_publication_authorization(
        command=object(),
        execution_context=object(),
        publication_plan=object(),
    )
    provider.load_cycle_closure_result(command=object(), execution_context=object())

    assert calls == ["plan", "publish", "close"]


def test_publication_provider_is_explicitly_validated() -> None:
    try:
        build_github_research_love_full_grouped_scheduler_bootstrap(
            _FirstVisitProvider(),
            _GroupedProvider(),
            _DownstreamProvider(),
            object(),
        )
    except TypeError as exc:
        assert "load_publication_command" in str(exc)
    else:
        raise AssertionError("un fournisseur de publication incomplet doit être refusé")
