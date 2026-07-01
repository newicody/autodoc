
from __future__ import annotations

from pathlib import Path

import pytest

from context.source_candidate import (
    SourceCandidateDecision,
    SourceCandidateInput,
    SourceCandidateOrigin,
    apply_source_candidate_decision,
    build_source_candidate,
)
from context.source_candidate_review import (
    SourceCandidateReviewCommand,
    SourceCandidateReviewPolicy,
    run_source_candidate_review,
)
from context.source_candidate_store import SourceCandidateStorePolicy, upsert_source_candidate


def _candidate(title: str, body: str = "body", status_action: str | None = None):
    candidate = build_source_candidate(
        SourceCandidateInput(
            title=title,
            body=body,
            origin=SourceCandidateOrigin(kind="manual", reference=title),
            labels=("review",),
            metadata={"phase": "6.2"},
        )
    ).candidate
    if status_action is not None:
        candidate = apply_source_candidate_decision(
            candidate,
            SourceCandidateDecision(action=status_action, reason="unit-test"),
        )
    return candidate


def test_review_missing_store_returns_empty_projection(tmp_path: Path) -> None:
    result = run_source_candidate_review(
        SourceCandidateReviewCommand(
            store_policy=SourceCandidateStorePolicy(tmp_path / "missing.json"),
        )
    )

    assert result.snapshot_count == 0
    assert result.matched_count == 0
    assert result.returned_count == 0
    assert result.candidate_ids == ()
    assert result.to_json_dict()["schema"] == "missipy.source_candidate.review.v1"
    assert "No SourceCandidate" in result.to_text()


def test_review_excludes_terminal_candidates_by_default(tmp_path: Path) -> None:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    active = _candidate("Active candidate")
    archived = _candidate("Archived candidate", status_action="archive")
    upsert_source_candidate(store_policy, archived)
    upsert_source_candidate(store_policy, active)

    result = run_source_candidate_review(SourceCandidateReviewCommand(store_policy=store_policy))

    assert result.snapshot_count == 2
    assert result.matched_count == 1
    assert result.returned_count == 1
    assert result.items[0].candidate.candidate_id == active.candidate_id
    assert result.items[0].candidate.actionable is True


def test_review_can_include_terminal_candidates_and_filter_status(tmp_path: Path) -> None:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    rejected = _candidate("Rejected candidate", status_action="reject")
    archived = _candidate("Archived candidate", status_action="archive")
    active = _candidate("Active candidate")
    upsert_source_candidate(store_policy, rejected)
    upsert_source_candidate(store_policy, archived)
    upsert_source_candidate(store_policy, active)

    result = run_source_candidate_review(
        SourceCandidateReviewCommand(
            store_policy=store_policy,
            review_policy=SourceCandidateReviewPolicy(
                include_terminal=True,
                status_filter=("archived",),
            ),
        )
    )

    assert result.snapshot_count == 3
    assert result.matched_count == 1
    assert result.items[0].candidate.candidate_id == archived.candidate_id
    assert result.items[0].candidate.terminal is True


def test_review_limit_and_body_preview_are_stable(tmp_path: Path) -> None:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    upsert_source_candidate(store_policy, _candidate("A", body="abcdef"))
    upsert_source_candidate(store_policy, _candidate("B", body="ghijkl"))

    result = run_source_candidate_review(
        SourceCandidateReviewCommand(
            store_policy=store_policy,
            review_policy=SourceCandidateReviewPolicy(limit=1, body_preview_chars=4),
        )
    )

    payload = result.to_json_dict()
    assert result.snapshot_count == 2
    assert result.matched_count == 2
    assert result.returned_count == 1
    assert payload["returned_count"] == 1
    assert payload["items"][0]["body_preview"].endswith("…")
    assert payload["items"][0]["decision_options"] == [
        "archive",
        "inspect",
        "merge",
        "promote",
        "reject",
        "relaunch",
    ]


@pytest.mark.parametrize(
    "policy",
    [
        SourceCandidateReviewPolicy(limit=1),
        SourceCandidateReviewPolicy(body_preview_chars=1),
        SourceCandidateReviewPolicy(status_filter=("new",)),
    ],
)
def test_review_policy_accepts_valid_values(policy: SourceCandidateReviewPolicy) -> None:
    assert policy.limit > 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 0},
        {"body_preview_chars": 0},
        {"status_filter": ("unknown",)},
    ],
)
def test_review_policy_rejects_invalid_values(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        SourceCandidateReviewPolicy(**kwargs)
