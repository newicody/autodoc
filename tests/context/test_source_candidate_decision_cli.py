from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate import SourceCandidateInput, build_source_candidate
from context.source_candidate_decision_cli import main
from context.source_candidate_store import SourceCandidateStorePolicy, load_source_candidate_store, upsert_source_candidate


def _stored_candidate(tmp_path: Path) -> tuple[Path, str]:
    store_path = tmp_path / "source_candidates.json"
    store_policy = SourceCandidateStorePolicy(store_path)
    candidate = build_source_candidate(
        SourceCandidateInput(title="CLI decision", body="Candidate body")
    ).candidate
    upsert_source_candidate(store_policy, candidate)
    return store_path, candidate.candidate_id


def test_source_candidate_decision_cli_json_stdout(tmp_path: Path, capsys) -> None:
    store_path, candidate_id = _stored_candidate(tmp_path)

    exit_code = main(
        [
            "--store-file",
            str(store_path),
            "--candidate-id",
            candidate_id,
            "--action",
            "merge",
            "--target-context-id",
            "ctx-1",
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "missipy.source_candidate.decision.v1"
    assert payload["candidate_id"] == candidate_id
    assert payload["action"] == "merge"
    assert payload["after_status"] == "merged"

    reloaded = load_source_candidate_store(SourceCandidateStorePolicy(store_path)).find(candidate_id)
    assert reloaded is not None
    assert reloaded.status == "merged"
    assert reloaded.decision is not None
    assert reloaded.decision.target_context_id == "ctx-1"


def test_source_candidate_decision_cli_text_stdout(tmp_path: Path, capsys) -> None:
    store_path, candidate_id = _stored_candidate(tmp_path)

    exit_code = main(
        [
            "--store-file",
            str(store_path),
            "--candidate-id",
            candidate_id,
            "--action",
            "inspect",
            "--reason",
            "needs more work",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "SourceCandidate decision" in output
    assert "action: inspect" in output
    assert "status: new -> analyzed" in output
