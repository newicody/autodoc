from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate import (
    SourceCandidateDecision,
    SourceCandidateInput,
    SourceCandidateOrigin,
    apply_source_candidate_decision,
    build_source_candidate,
)
from context.source_candidate_store import (
    SourceCandidateReportPolicy,
    SourceCandidateStorePolicy,
    SourceCandidateStoreReport,
    SourceCandidateStoreSnapshot,
    load_source_candidate_store,
    source_candidate_store_snapshot_from_json_dict,
    upsert_source_candidate,
    write_source_candidate_store,
    write_source_candidate_store_report,
)


def _candidate(title: str = "Local artifact"):
    return build_source_candidate(
        SourceCandidateInput(
            title=title,
            body="Artifact-dir ready for local intake.",
            origin=SourceCandidateOrigin(kind="artifact_dir", reference="/tmp/autodoc_e5_dry_run"),
            labels=("e5", "candidate"),
            metadata={"phase": "5.15"},
        )
    ).candidate


def test_missing_store_loads_as_empty_snapshot(tmp_path: Path) -> None:
    policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")

    snapshot = load_source_candidate_store(policy)

    assert snapshot.repository == "newicody/autodoc"
    assert snapshot.candidate_count == 0
    assert snapshot.to_json_dict()["schema"] == "missipy.source_candidate.store.v1"


def test_upsert_writes_and_reloads_source_candidate(tmp_path: Path) -> None:
    policy = SourceCandidateStorePolicy(tmp_path / "nested" / "source_candidates.json")
    candidate = _candidate()

    result = upsert_source_candidate(policy, candidate)
    reloaded = load_source_candidate_store(policy)

    assert result.inserted is True
    assert result.replaced is False
    assert result.snapshot.candidate_count == 1
    assert reloaded.candidate_count == 1
    assert reloaded.find(candidate.candidate_id) is not None
    payload = json.loads(policy.path.read_text(encoding="utf-8"))
    assert payload["candidate_count"] == 1
    assert payload["candidates"][0]["candidate_id"] == candidate.candidate_id


def test_upsert_replaces_existing_candidate_without_duplicate(tmp_path: Path) -> None:
    policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    candidate = _candidate()
    decided = apply_source_candidate_decision(
        candidate,
        SourceCandidateDecision(action="archive", reason="covered elsewhere"),
    )

    first = upsert_source_candidate(policy, candidate)
    second = upsert_source_candidate(policy, decided)
    reloaded = load_source_candidate_store(policy)

    assert first.inserted is True
    assert second.inserted is False
    assert second.replaced is True
    assert reloaded.candidate_count == 1
    stored = reloaded.find(candidate.candidate_id)
    assert stored is not None
    assert stored.status == "archived"
    assert stored.decision is not None
    assert stored.decision.reason == "covered elsewhere"


def test_write_source_candidate_report_is_optional_and_atomic(tmp_path: Path) -> None:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    report_policy = SourceCandidateReportPolicy(tmp_path / "reports" / "last_write.json")
    candidate = _candidate("Report me")

    result = upsert_source_candidate(store_policy, candidate, report=report_policy)
    report_payload = json.loads(report_policy.path.read_text(encoding="utf-8"))

    assert report_payload["schema"] == "missipy.source_candidate.store_report.v1"
    assert report_payload["operation"] == "upsert_source_candidate"
    assert report_payload["write_result"]["schema"] == "missipy.source_candidate.store_write.v1"
    assert report_payload["write_result"]["candidate_id"] == candidate.candidate_id
    assert report_payload["write_result"]["path"] == str(store_policy.path)
    assert result.snapshot.candidate_count == 1


def test_store_snapshot_json_roundtrip_preserves_candidates() -> None:
    candidate = _candidate("Roundtrip")
    snapshot = SourceCandidateStoreSnapshot(candidates=(candidate,), metadata={"source": "unit-test"})

    restored = source_candidate_store_snapshot_from_json_dict(snapshot.to_json_dict())

    assert restored.candidate_count == 1
    assert restored.metadata["source"] == "unit-test"
    assert restored.find(candidate.candidate_id) is not None


def test_store_rejects_invalid_schema_and_duplicate_ids(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text('{"schema":"wrong","candidates":[]}', encoding="utf-8")

    with pytest.raises(ValueError, match="store schema"):
        load_source_candidate_store(SourceCandidateStorePolicy(bad_path))

    candidate = _candidate()
    with pytest.raises(ValueError, match="candidate ids must be unique"):
        SourceCandidateStoreSnapshot(candidates=(candidate, candidate))


def test_report_policy_with_none_path_is_noop(tmp_path: Path) -> None:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    candidate = _candidate("No report")
    result = upsert_source_candidate(store_policy, candidate)
    report = SourceCandidateStoreReport(result)

    returned = write_source_candidate_store_report(SourceCandidateReportPolicy(), report)

    assert returned is report


def test_write_source_candidate_store_returns_snapshot(tmp_path: Path) -> None:
    policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    candidate = _candidate("Write direct")
    snapshot = SourceCandidateStoreSnapshot(candidates=(candidate,))

    returned = write_source_candidate_store(policy, snapshot)

    assert returned is snapshot
    assert load_source_candidate_store(policy).candidate_count == 1
