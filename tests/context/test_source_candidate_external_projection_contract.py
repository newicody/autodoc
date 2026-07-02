from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate_external_projection_contract import (
    SourceCandidateExternalProjectionContractPolicy,
    build_source_candidate_external_projection_contract,
    read_source_candidate_external_projection_contract,
    write_source_candidate_external_projection_contract,
)


def _write_handoff(path: Path, *, passed: bool = True, audit_present: bool = True) -> None:
    path.mkdir(parents=True)
    (path / "handoff_manifest.json").write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.projection_handoff_dry_run.v1",
                "path": str(path),
                "manifest_path": str(path / "handoff_manifest.json"),
                "projection_bundle_path": str(path / "projection_bundle"),
                "passed": passed,
                "item_count": 1,
                "artifacts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "projection_preview.json").write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.projection_preview.v1",
                "target_name": "operator_project_surface",
                "source_report_schema": "missipy.source_candidate.operator_report.v1",
                "item_count": 1,
                "items": [
                    {
                        "candidate_id": "candidate-a",
                        "title": "Ready",
                        "status": "new",
                        "decision_action": "inspect",
                        "decision_reason": "check",
                        "target_context_id": None,
                        "audit_present": audit_present,
                        "recommended_action": "inspect",
                        "labels": ["status:new"],
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "projection_gate_report.json").write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.projection_gate_report.v1",
                "gate_result": {
                    "schema": "missipy.source_candidate.projection_gate.v1",
                    "passed": passed,
                    "item_count": 1,
                    "issue_count": 0 if passed else 1,
                    "issues": [],
                },
                "text": "projection gate: PASS" if passed else "projection gate: FAIL",
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_external_projection_contract_builds_from_handoff(tmp_path: Path) -> None:
    handoff = tmp_path / "handoff"
    _write_handoff(handoff)

    contract = build_source_candidate_external_projection_contract(handoff)

    assert contract.target_kind == "generic_project_surface"
    assert contract.gate_passed is True
    assert contract.projection_allowed is True
    assert contract.item_count == 1
    assert contract.items[0].candidate_id == "candidate-a"
    assert contract.items[0].safety_flags == ()


def test_external_projection_contract_blocks_when_gate_failed(tmp_path: Path) -> None:
    handoff = tmp_path / "handoff"
    _write_handoff(handoff, passed=False)

    contract = build_source_candidate_external_projection_contract(handoff)

    assert contract.gate_passed is False
    assert contract.projection_allowed is False
    assert contract.blocked_reasons == ("gate_not_passed",)


def test_external_projection_contract_can_be_targeted_without_binding_adapter(tmp_path: Path) -> None:
    handoff = tmp_path / "handoff"
    _write_handoff(handoff)

    contract = build_source_candidate_external_projection_contract(
        handoff,
        SourceCandidateExternalProjectionContractPolicy(target_kind="github_project_surface"),
    )

    assert contract.target_kind == "github_project_surface"
    assert contract.projection_allowed is True


def test_external_projection_contract_marks_missing_audit_as_safety_flag(tmp_path: Path) -> None:
    handoff = tmp_path / "handoff"
    _write_handoff(handoff, audit_present=False)

    contract = build_source_candidate_external_projection_contract(handoff)

    assert contract.items[0].safety_flags == ("audit_missing",)


def test_external_projection_contract_writes_and_reads_json(tmp_path: Path) -> None:
    handoff = tmp_path / "handoff"
    output = tmp_path / "external_projection_contract.json"
    _write_handoff(handoff)
    contract = build_source_candidate_external_projection_contract(handoff)

    returned = write_source_candidate_external_projection_contract(output, contract)
    payload = read_source_candidate_external_projection_contract(output)

    assert returned == output
    assert payload["schema"] == "missipy.source_candidate.external_projection_contract.v1"
    assert payload["projection_allowed"] is True


def test_external_projection_contract_rejects_invalid_policy(tmp_path: Path) -> None:
    handoff = tmp_path / "handoff"
    _write_handoff(handoff)

    with pytest.raises(ValueError, match="max_items"):
        build_source_candidate_external_projection_contract(
            handoff,
            SourceCandidateExternalProjectionContractPolicy(max_items=0),
        )
