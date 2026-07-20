from __future__ import annotations

from dataclasses import dataclass

import pytest

from context.github_research_love_two_qdrant_projections_0287 import (
    GitHubResearchLoveTwoProjectionError,
    _resolve_pair_projected_at,
)
from context.love_qdrant_live_analysis_projection_0287 import (
    LoveQdrantLiveProjectionIdentity,
)


@dataclass(frozen=True)
class _Projection:
    source_ref: str
    source_content_digest: str
    model_ref: str
    model_revision: str
    dimension: int
    normalized: bool
    vector_name: str
    collection_name: str
    point_id: str
    projection_state: str
    projected_at: str | None


class _Store:
    def __init__(self, values: dict[str, _Projection]) -> None:
        self.values = dict(values)

    def get_projection(self, projection_ref: str) -> _Projection | None:
        return self.values.get(projection_ref)


class _LegacyStoreWithoutProjectionRead:
    pass


def _identity(name: str) -> LoveQdrantLiveProjectionIdentity:
    return LoveQdrantLiveProjectionIdentity(
        projection_ref=f"vector-projection:{name}",
        point_id=f"qdrant-point:{name}",
    )


def _expected(identity: LoveQdrantLiveProjectionIdentity, source: str) -> dict[str, object]:
    return {
        "source_ref": source,
        "source_content_digest": "sha256:" + "a" * 64,
        "model_ref": "model:multilingual-e5-small",
        "model_revision": "installed",
        "dimension": 384,
        "normalized": True,
        "vector_name": "dense_e5_v1",
        "collection_name": "autodoc_context_e5_384_hybrid_v1",
        "point_id": identity.point_id,
        "projection_state": "active",
    }


def _projection(
    identity: LoveQdrantLiveProjectionIdentity,
    source: str,
    projected_at: str | None,
) -> _Projection:
    return _Projection(
        **_expected(identity, source),
        projected_at=projected_at,
    )


def test_legacy_validated_port_double_without_projection_reader_uses_requested_timestamp() -> None:
    first = _identity("first")
    second = _identity("second")

    resolved = _resolve_pair_projected_at(
        _LegacyStoreWithoutProjectionRead(),
        requested_projected_at="2026-07-20T05:00:00Z",
        first_identity=first,
        second_identity=second,
        first_expected=_expected(first, "context-object:first"),
        second_expected=_expected(second, "context-object:second"),
    )

    assert resolved == "2026-07-20T05:00:00Z"


def test_first_projection_pair_uses_requested_timestamp() -> None:
    first = _identity("first")
    second = _identity("second")

    resolved = _resolve_pair_projected_at(
        _Store({}),
        requested_projected_at="2026-07-20T05:00:00Z",
        first_identity=first,
        second_identity=second,
        first_expected=_expected(first, "context-object:first"),
        second_expected=_expected(second, "context-object:second"),
    )

    assert resolved == "2026-07-20T05:00:00Z"


def test_partial_replay_preserves_first_sql_projection_timestamp() -> None:
    first = _identity("first")
    second = _identity("second")
    original = "2026-07-20T04:00:00Z"

    resolved = _resolve_pair_projected_at(
        _Store(
            {
                first.projection_ref: _projection(
                    first,
                    "context-object:first",
                    original,
                )
            }
        ),
        requested_projected_at="2026-07-20T05:00:00Z",
        first_identity=first,
        second_identity=second,
        first_expected=_expected(first, "context-object:first"),
        second_expected=_expected(second, "context-object:second"),
    )

    assert resolved == original


def test_complete_replay_requires_shared_persisted_timestamp() -> None:
    first = _identity("first")
    second = _identity("second")
    original = "2026-07-20T04:00:00Z"

    resolved = _resolve_pair_projected_at(
        _Store(
            {
                first.projection_ref: _projection(
                    first,
                    "context-object:first",
                    original,
                ),
                second.projection_ref: _projection(
                    second,
                    "context-object:second",
                    original,
                ),
            }
        ),
        requested_projected_at="2026-07-20T05:00:00Z",
        first_identity=first,
        second_identity=second,
        first_expected=_expected(first, "context-object:first"),
        second_expected=_expected(second, "context-object:second"),
    )

    assert resolved == original


def test_divergent_persisted_timestamps_fail_closed() -> None:
    first = _identity("first")
    second = _identity("second")

    with pytest.raises(
        GitHubResearchLoveTwoProjectionError,
        match="disagree on projected_at",
    ):
        _resolve_pair_projected_at(
            _Store(
                {
                    first.projection_ref: _projection(
                        first,
                        "context-object:first",
                        "2026-07-20T04:00:00Z",
                    ),
                    second.projection_ref: _projection(
                        second,
                        "context-object:second",
                        "2026-07-20T04:01:00Z",
                    ),
                }
            ),
            requested_projected_at="2026-07-20T05:00:00Z",
            first_identity=first,
            second_identity=second,
            first_expected=_expected(first, "context-object:first"),
            second_expected=_expected(second, "context-object:second"),
        )


def test_existing_projection_with_changed_identity_fails_closed() -> None:
    first = _identity("first")
    second = _identity("second")
    changed = _projection(first, "context-object:other", "2026-07-20T04:00:00Z")

    with pytest.raises(
        GitHubResearchLoveTwoProjectionError,
        match="source_ref",
    ):
        _resolve_pair_projected_at(
            _Store({first.projection_ref: changed}),
            requested_projected_at="2026-07-20T05:00:00Z",
            first_identity=first,
            second_identity=second,
            first_expected=_expected(first, "context-object:first"),
            second_expected=_expected(second, "context-object:second"),
        )
