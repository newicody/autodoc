from __future__ import annotations

from dataclasses import dataclass

import pytest

from context.github_research_love_final_deliverable_sql_0287 import (
    GitHubResearchLoveFinalDeliverableError,
    _resolve_final_deliverable_created_at,
)


@dataclass(frozen=True)
class _TimedEntity:
    created_at: str


class _Store:
    def __init__(
        self,
        *,
        artifact: _TimedEntity | None = None,
        revision: _TimedEntity | None = None,
    ) -> None:
        self.artifact = artifact
        self.revision = revision

    def get_object(self, object_ref: str):
        return None

    def put_object(self, item):
        raise AssertionError("write not expected")

    def get_artifact(self, artifact_ref: str):
        return self.artifact

    def put_artifact(self, item):
        raise AssertionError("write not expected")

    def get_revision(self, revision_ref: str):
        return self.revision

    def put_revision(self, item):
        raise AssertionError("write not expected")


def _resolve(store: _Store, requested: str = "2026-07-20T03:00:00Z") -> str:
    return _resolve_final_deliverable_created_at(
        store,  # type: ignore[arg-type]
        artifact_ref="artifact:github-love-final-test",
        revision_ref="context-revision:github-love-final-test",
        requested_created_at=requested,
    )


def test_first_materialization_uses_requested_timestamp() -> None:
    assert _resolve(_Store()) == "2026-07-20T03:00:00Z"


def test_replay_preserves_first_timestamp_from_complete_pair() -> None:
    first = "2026-07-20T02:00:00Z"
    store = _Store(
        artifact=_TimedEntity(first),
        revision=_TimedEntity(first),
    )
    assert _resolve(store) == first


@pytest.mark.parametrize("existing_name", ["artifact", "revision"])
def test_partial_replay_preserves_existing_timestamp(existing_name: str) -> None:
    first = "2026-07-20T02:00:00Z"
    store = _Store(**{existing_name: _TimedEntity(first)})
    assert _resolve(store) == first


def test_divergent_historical_timestamps_fail_closed() -> None:
    store = _Store(
        artifact=_TimedEntity("2026-07-20T02:00:00Z"),
        revision=_TimedEntity("2026-07-20T02:00:01Z"),
    )
    with pytest.raises(
        GitHubResearchLoveFinalDeliverableError,
        match="disagree on created_at",
    ):
        _resolve(store)
