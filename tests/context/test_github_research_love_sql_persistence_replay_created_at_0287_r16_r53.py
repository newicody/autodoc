from __future__ import annotations

from dataclasses import dataclass

import pytest

from context.github_research_love_sql_persistence_0287 import (
    GitHubResearchLoveSqlPersistenceError,
    _resolve_persistence_created_at,
)


@dataclass(frozen=True)
class _Existing:
    created_at: str


class _Store:
    def __init__(
        self,
        *,
        first: _Existing | None = None,
        second: _Existing | None = None,
        revision: _Existing | None = None,
    ) -> None:
        self.first = first
        self.second = second
        self.revision = revision

    def get_object(self, _object_ref: str) -> None:
        return None

    def put_object(self, _item: object) -> None:
        raise AssertionError("write forbidden")

    def get_artifact(self, artifact_ref: str) -> _Existing | None:
        if "-first-" in artifact_ref:
            return self.first
        if "-second-" in artifact_ref:
            return self.second
        raise AssertionError(artifact_ref)

    def put_artifact(self, _item: object) -> None:
        raise AssertionError("write forbidden")

    def get_revision(self, revision_ref: str) -> _Existing | None:
        if revision_ref.startswith("context-revision:github-love-pair-"):
            return self.revision
        return None

    def put_revision(self, _item: object) -> None:
        raise AssertionError("write forbidden")


def test_first_materialization_uses_requested_timestamp() -> None:
    resolved = _resolve_persistence_created_at(
        _Store(),
        suffix="abc123",
        requested_created_at="2026-07-20T05:00:00Z",
    )

    assert resolved == "2026-07-20T05:00:00Z"


def test_replay_preserves_first_persisted_timestamp() -> None:
    resolved = _resolve_persistence_created_at(
        _Store(first=_Existing("2026-07-20T04:00:00Z")),
        suffix="abc123",
        requested_created_at="2026-07-20T05:00:00Z",
    )

    assert resolved == "2026-07-20T04:00:00Z"


def test_complete_replay_requires_one_shared_persisted_timestamp() -> None:
    original = "2026-07-20T04:00:00Z"
    resolved = _resolve_persistence_created_at(
        _Store(
            first=_Existing(original),
            second=_Existing(original),
            revision=_Existing(original),
        ),
        suffix="abc123",
        requested_created_at="2026-07-20T05:00:00Z",
    )

    assert resolved == original


def test_disagreeing_immutable_timestamps_fail_closed() -> None:
    with pytest.raises(
        GitHubResearchLoveSqlPersistenceError,
        match="existing immutable analysis entities disagree on created_at",
    ):
        _resolve_persistence_created_at(
            _Store(
                first=_Existing("2026-07-20T04:00:00Z"),
                second=_Existing("2026-07-20T04:01:00Z"),
            ),
            suffix="abc123",
            requested_created_at="2026-07-20T05:00:00Z",
        )
