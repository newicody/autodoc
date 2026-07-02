from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate import SourceCandidateDecision, SourceCandidateInput, build_source_candidate
from context.source_candidate_decision import (
    SourceCandidateDecisionAuditPolicy,
    SourceCandidateDecisionCommand,
    run_source_candidate_decision,
)
from context.source_candidate_decision_cli import main
from context.source_candidate_store import SourceCandidateStorePolicy, upsert_source_candidate


def _store_with_candidate(tmp_path: Path) -> tuple[SourceCandidateStorePolicy, str]:
    policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    candidate = build_source_candidate(
        SourceCandidateInput(title="Audit target", body="Keep an audit trail")
    ).candidate
    upsert_source_candidate(policy, candidate)
    return policy, candidate.candidate_id


def test_source_candidate_decision_writes_stable_audit_report(tmp_path: Path) -> None:
    store_policy, candidate_id = _store_with_candidate(tmp_path)
    audit_path = tmp_path / "audit" / "decision.json"

    result = run_source_candidate_decision(
        SourceCandidateDecisionCommand(
            store_policy=store_policy,
            candidate_id=candidate_id,
            decision=SourceCandidateDecision(action="archive", reason="done"),
            audit_policy=SourceCandidateDecisionAuditPolicy(audit_path),
        )
    )

    payload = json.loads(audit_path.read_text(encoding="utf-8"))
    assert result.audit_path == audit_path
    assert result.to_json_dict()["audit_path"] == str(audit_path)
    assert payload["schema"] == "missipy.source_candidate.decision_audit.v1"
    assert payload["operation"] == "source_candidate_decision"
    assert payload["candidate_id"] == candidate_id
    assert payload["action"] == "archive"
    assert payload["before_status"] == "new"
    assert payload["after_status"] == "archived"
    assert payload["reason"] == "done"
    assert payload["write_result"]["candidate_id"] == candidate_id
    assert payload["candidate_before"]["candidate_id"] == candidate_id
    assert payload["candidate_after"]["status"] == "archived"


def test_source_candidate_decision_audit_can_omit_candidate_snapshots(tmp_path: Path) -> None:
    store_policy, candidate_id = _store_with_candidate(tmp_path)
    audit_path = tmp_path / "decision_audit.json"

    run_source_candidate_decision(
        SourceCandidateDecisionCommand(
            store_policy=store_policy,
            candidate_id=candidate_id,
            decision=SourceCandidateDecision(action="reject", reason="noise"),
            audit_policy=SourceCandidateDecisionAuditPolicy(
                audit_path,
                include_candidates=False,
            ),
        )
    )

    payload = json.loads(audit_path.read_text(encoding="utf-8"))
    assert "candidate_before" not in payload
    assert "candidate_after" not in payload
    assert payload["after_status"] == "rejected"


def test_source_candidate_decision_cli_writes_audit_file(tmp_path: Path, capsys) -> None:
    store_policy, candidate_id = _store_with_candidate(tmp_path)
    audit_path = tmp_path / "decision_cli_audit.json"

    exit_code = main(
        [
            "--store-file",
            str(store_policy.path),
            "--candidate-id",
            candidate_id,
            "--action",
            "inspect",
            "--reason",
            "operator review",
            "--audit-file",
            str(audit_path),
            "--audit-without-candidates",
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    result_payload = json.loads(capsys.readouterr().out)
    audit_payload = json.loads(audit_path.read_text(encoding="utf-8"))
    assert result_payload["audit_path"] == str(audit_path)
    assert audit_payload["candidate_id"] == candidate_id
    assert audit_payload["action"] == "inspect"
    assert "candidate_before" not in audit_payload
