from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate import SourceCandidateInput, build_source_candidate
from context.source_candidate_operator_bundle import (
    SourceCandidateOperatorBundlePolicy,
    write_source_candidate_operator_bundle,
)
from context.source_candidate_operator_bundle_cli import main
from context.source_candidate_operator_report import build_source_candidate_operator_report
from context.source_candidate_review import (
    SourceCandidateReviewCommand,
    SourceCandidateReviewPolicy,
    run_source_candidate_review,
)
from context.source_candidate_review_audit import (
    SourceCandidateReviewAuditPolicy,
    enrich_source_candidate_review_with_audit,
)
from context.source_candidate_store import SourceCandidateStorePolicy, upsert_source_candidate


def _store(tmp_path: Path) -> SourceCandidateStorePolicy:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    candidate = build_source_candidate(
        SourceCandidateInput(title="Bundle candidate", body="Needs a bundle")
    ).candidate
    upsert_source_candidate(store_policy, candidate)
    return store_policy


def _report(tmp_path: Path):
    store_policy = _store(tmp_path)
    review = run_source_candidate_review(
        SourceCandidateReviewCommand(
            store_policy=store_policy,
            review_policy=SourceCandidateReviewPolicy(),
        )
    )
    review_audit = enrich_source_candidate_review_with_audit(
        review,
        SourceCandidateReviewAuditPolicy(),
    )
    return store_policy, build_source_candidate_operator_report(review_audit)


def test_operator_bundle_writes_manifest_json_and_text_reports(tmp_path: Path) -> None:
    _store_policy, report = _report(tmp_path)
    bundle_dir = tmp_path / "bundle"

    result = write_source_candidate_operator_bundle(
        report,
        SourceCandidateOperatorBundlePolicy(bundle_dir),
    )

    assert result.path == bundle_dir
    assert result.artifact_count == 2
    assert (bundle_dir / "manifest.json").exists()
    assert (bundle_dir / "operator_report.json").exists()
    assert (bundle_dir / "operator_report.txt").exists()
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "missipy.source_candidate.operator_bundle.v1"
    assert manifest["artifact_count"] == 2
    assert manifest["returned_count"] == 1
    assert manifest["artifacts"][0]["role"] == "operator_report_json"
    assert "SourceCandidate operator report" in (bundle_dir / "operator_report.txt").read_text(encoding="utf-8")


def test_operator_bundle_can_write_only_json(tmp_path: Path) -> None:
    _store_policy, report = _report(tmp_path)
    bundle_dir = tmp_path / "bundle"

    result = write_source_candidate_operator_bundle(
        report,
        SourceCandidateOperatorBundlePolicy(bundle_dir, include_text=False),
    )

    assert result.artifact_count == 1
    assert (bundle_dir / "operator_report.json").exists()
    assert not (bundle_dir / "operator_report.txt").exists()


def test_operator_bundle_rejects_empty_bundle(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one"):
        SourceCandidateOperatorBundlePolicy(tmp_path / "bundle", include_json=False, include_text=False)


def test_operator_bundle_rejects_nested_artifact_names(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="simple relative"):
        SourceCandidateOperatorBundlePolicy(tmp_path / "bundle", json_name="nested/report.json")


def test_operator_bundle_cli_writes_bundle_and_renders_json_summary(tmp_path: Path, capsys) -> None:
    store_policy = _store(tmp_path)
    bundle_dir = tmp_path / "bundle"

    exit_code = main(
        [
            "--store-file",
            str(store_policy.path),
            "--bundle-dir",
            str(bundle_dir),
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["schema"] == "missipy.source_candidate.operator_bundle.v1"
    assert summary["path"] == str(bundle_dir)
    assert summary["artifact_count"] == 2
    assert (bundle_dir / "manifest.json").exists()
