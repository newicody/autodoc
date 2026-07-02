from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate_phase7_handoff_contract import (
    build_source_candidate_phase7_handoff_contract,
    build_source_candidate_phase7_handoff_contract_from_closure_report,
    read_source_candidate_phase7_handoff_contract,
    render_source_candidate_phase7_handoff_contract,
    write_source_candidate_phase7_handoff_contract,
)


def _closure_payload() -> dict[str, object]:
    return {
        "schema": "missipy.source_candidate.phase7_closure_report.v1",
        "root": "/tmp/repo",
        "phase": "7",
        "status": "closed",
        "artifact_count": 1,
        "missing_count": 0,
        "local_only": True,
        "remote_mutation_enabled": False,
        "scheduler_modified": False,
        "network_enabled": False,
        "next_phase": "8",
        "artifacts": [],
    }


def test_phase7_handoff_contract_freezes_external_boundaries() -> None:
    contract = build_source_candidate_phase7_handoff_contract(
        closure_report_payload=_closure_payload(),
    )

    assert contract.phase == "7"
    assert contract.status == "frozen"
    assert contract.local_source_of_truth is True
    assert contract.external_service_calls_allowed is False
    assert contract.remote_mutation_allowed is False
    assert contract.scheduler_execution_allowed is False
    assert contract.generated_svg_policy_required is True
    assert contract.operator_confirmation_required is True
    assert contract.next_phase == "8"


def test_phase7_handoff_contract_builds_from_closure_report_file(tmp_path: Path) -> None:
    closure = tmp_path / "closure.json"
    closure.write_text(json.dumps(_closure_payload()) + "\n", encoding="utf-8")

    contract = build_source_candidate_phase7_handoff_contract_from_closure_report(closure)

    assert contract.closure_report_path == closure
    assert contract.status == "frozen"


def test_phase7_handoff_contract_rejects_open_remote_mutation(tmp_path: Path) -> None:
    payload = _closure_payload()
    payload["remote_mutation_enabled"] = True

    with pytest.raises(ValueError, match="remote mutation disabled"):
        build_source_candidate_phase7_handoff_contract(closure_report_payload=payload)


def test_phase7_handoff_contract_writes_and_reads_json(tmp_path: Path) -> None:
    output = tmp_path / "handoff.json"
    contract = build_source_candidate_phase7_handoff_contract()

    returned = write_source_candidate_phase7_handoff_contract(output, contract)
    payload = read_source_candidate_phase7_handoff_contract(output)

    assert returned == output
    assert payload["schema"] == "missipy.source_candidate.phase7_handoff_contract.v1"
    assert payload["status"] == "frozen"


def test_phase7_handoff_contract_render_is_stable() -> None:
    text = render_source_candidate_phase7_handoff_contract(
        build_source_candidate_phase7_handoff_contract()
    )

    assert "source candidate phase 7 handoff contract" in text
    assert "status: frozen" in text
    assert "remote_mutation_allowed: False" in text
    assert "next_phase_options:" in text
