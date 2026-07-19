from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import validate_fetched_github_research_triplet_0287 as tool


def _ready_run() -> dict:
    return {
        "repository": "newicody/projects",
        "run_id": "30000000001",
        "handoff_ref": (
            "github-actions-ready-run:"
            "newicody-projects:30000000001"
        ),
        "status": "ready",
        "artifact_count": 3,
        "artifacts": {
            role: {
                "run_id": "30000000001",
                "artifact_id": str(index),
                "artifact_name": f"artifact-{role}",
                "availability": "already_synced",
                "staging_dir": f"/tmp/{role}",
            }
            for index, role in enumerate(
                tool._EXPECTED_ROLES,
                start=1,
            )
        },
        "local_execution_started": False,
        "remote_mutation_performed": False,
    }


def _successful_mapping(
    *,
    request_mode: str = "initial",
    parent_event_ref: str = "",
) -> dict:
    route_candidate = {
        "route_candidate_ref": "research-route-candidate:abc",
        "repository": "newicody/projects",
        "run_id": "30000000001",
        "issue_number": 16,
        "requested_status": "Recherche",
        "request_mode": request_mode,
        "parent_event_ref": parent_event_ref,
        "admissibility_digest": "abc",
        "scheduler_command_created": False,
        "scheduler_dispatch_started": False,
        "laboratory_execution_started": False,
    }
    admissibility = {
        "valid": True,
        "admissible": True,
        "status": "admissible",
        "repository": "newicody/projects",
        "run_id": "30000000001",
        "issue_number": 16,
        "requested_status": "Recherche",
        "request_mode": request_mode,
        "parent_event_ref": parent_event_ref,
        "route_candidate": route_candidate,
    }
    return {
        "schema": (
            "missipy.github."
            "ready_run_research_admissibility_assembly.v1"
        ),
        "valid": True,
        "admissible": True,
        "status": "admissible",
        "issues": [],
        "repository": "newicody/projects",
        "run_id": "30000000001",
        "handoff_ref": (
            "github-actions-ready-run:"
            "newicody-projects:30000000001"
        ),
        "run_assembly": {"valid": True},
        "work_package_build": {
            "valid": True,
            "work_package": {"ready_for_laboratory_route": True},
        },
        "admissibility": admissibility,
    }


def _install_result(
    monkeypatch: pytest.MonkeyPatch,
    mapping: dict,
) -> None:
    monkeypatch.setattr(
        tool,
        "assemble_ready_run_and_evaluate_research_admissibility",
        lambda command: SimpleNamespace(
            to_mapping=lambda: mapping
        ),
    )


def test_loaded_triplet_reuses_existing_admissibility_chain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_result(monkeypatch, _successful_mapping())

    result = tool.validate_loaded_fetched_triplet(
        ready_run=_ready_run(),
        loaded_contents=(),
    )

    assert result["valid"] is True
    assert result["admissible"] is True
    assert result["requested_status"] == "Recherche"
    assert result["request_mode"] == "initial"
    assert result["parent_event_ref"] == ""
    assert result["scheduler_intake_created"] is False
    assert result["existing_digest_validation_reused"] is True


def test_automatic_gate_rejects_continuation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_result(
        monkeypatch,
        _successful_mapping(
            request_mode="continuation",
            parent_event_ref="event:previous",
        ),
    )

    with pytest.raises(
        tool.FetchedResearchTripletValidationError,
        match="request_mode must be initial",
    ):
        tool.validate_loaded_fetched_triplet(
            ready_run=_ready_run(),
            loaded_contents=(),
        )


def test_gate_rejects_existing_inadmissible_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapping = _successful_mapping()
    mapping["valid"] = False
    mapping["admissible"] = False
    mapping["issues"] = ["manifest digest mismatch"]
    _install_result(monkeypatch, mapping)

    with pytest.raises(
        tool.FetchedResearchTripletValidationError,
        match="manifest digest mismatch",
    ):
        tool.validate_loaded_fetched_triplet(
            ready_run=_ready_run(),
            loaded_contents=(),
        )


def test_gate_requires_exact_three_ready_run_roles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_result(monkeypatch, _successful_mapping())
    ready_run = _ready_run()
    del ready_run["artifacts"]["copilot_advisory"]

    with pytest.raises(
        tool.FetchedResearchTripletValidationError,
        match="exactly the three expected roles",
    ):
        tool.validate_loaded_fetched_triplet(
            ready_run=ready_run,
            loaded_contents=(),
        )


def test_route_candidate_cannot_start_scheduler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapping = _successful_mapping()
    mapping["admissibility"]["route_candidate"][
        "scheduler_dispatch_started"
    ] = True
    _install_result(monkeypatch, mapping)

    with pytest.raises(
        tool.FetchedResearchTripletValidationError,
        match="must not dispatch",
    ):
        tool.validate_loaded_fetched_triplet(
            ready_run=_ready_run(),
            loaded_contents=(),
        )


def test_validation_digest_binds_run_and_artifact_ids(
    tmp_path: Path,
) -> None:
    validation = {
        "repository": "newicody/projects",
        "run_id": "30000000001",
        "issue_number": 16,
        "requested_status": "Recherche",
        "request_mode": "initial",
        "parent_event_ref": "",
        "route_candidate": {
            "route_candidate_ref": "research-route-candidate:abc",
            "admissibility_digest": "abc",
        },
    }
    first = tool._validation_digest(  # noqa: SLF001
        fetch_cycle_report=tmp_path / "cycle.json",
        ready_run=_ready_run(),
        validation=validation,
    )
    changed = _ready_run()
    changed["artifacts"]["run_manifest"]["artifact_id"] = "999"
    second = tool._validation_digest(  # noqa: SLF001
        fetch_cycle_report=tmp_path / "cycle.json",
        ready_run=changed,
        validation=validation,
    )

    assert first.startswith("sha256:")
    assert second.startswith("sha256:")
    assert first != second


def test_tool_does_not_modify_workflow_or_create_remote_side_effects() -> None:
    source = Path(tool.__file__).read_text(encoding="utf-8")

    assert "assemble_fetched_github_research_admissibility_0287" in source
    assert "assemble_ready_run_and_evaluate_research_admissibility" in source
    assert '"workflow_modified": False' in source
    assert '"actions_artifact_creation_modified": False' in source
    assert '"github_request_performed": False' in source
    assert '"scheduler_intake_created": False' in source

    for forbidden in (
        "subprocess.run(",
        "requests.",
        "urlopen(",
        "gh api",
        "actions/upload-artifact",
        "Scheduler(",
        "QdrantClient(",
        "psycopg.connect(",
        "openvino.Core(",
    ):
        assert forbidden not in source
