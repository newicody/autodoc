from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import run_github_research_love_closed_loop_0287 as tool


class FakeLease:
    def __init__(self) -> None:
        self.ports = SimpleNamespace(
            runtime_ref="runtime:test",
            projection_port=SimpleNamespace(
                read_named_reference_point=lambda **kwargs: None,
            ),
        )
        self.closed = False

    def close(self, *, current_process_id: int):
        self.closed = True
        return SimpleNamespace(
            to_mapping=lambda: {
                "valid": True,
                "action": "closed",
                "process_id": current_process_id,
            }
        )

    def to_readback_mapping(self):
        return {
            "runtime_ref": "runtime:test",
            "closed": self.closed,
        }


def test_prepare_writes_digest_and_closes_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "prepared.json"
    lease = FakeLease()
    ready_run = {
        "repository": "newicody/projects",
        "run_id": "29622831972",
    }
    artifacts = (object(), object(), object())
    publication_plan = SimpleNamespace(
        plan_digest="sha256:" + "1" * 64,
    )
    prepared = SimpleNamespace(
        valid=True,
        status="publication-confirmation-required",
        issues=(),
        publication_plan=publication_plan,
        to_mapping=lambda: {
            "schema": (
                "missipy.github.research_love_closed_loop_prepared.v1"
            ),
            "valid": True,
            "status": "publication-confirmation-required",
            "stages": {
                "final_deliverable_sql": {"valid": True},
                "publication_plan": {
                    "schema": (
                        "missipy.github.research_love_final_remote_"
                        "publication_plan.v1"
                    ),
                    "plan_digest": publication_plan.plan_digest,
                },
            },
        },
    )

    monkeypatch.setattr(
        tool,
        "_load_one_fetched_ready_run",
        lambda **kwargs: (ready_run, artifacts),
    )
    monkeypatch.setattr(
        tool,
        "_resolve_prepare_project_target",
        lambda **kwargs: {
            "schema": (
                "missipy.github.research_projectv2_target_resolution.v1"
            ),
            "status": "resolved",
            "project_item_id": "PVTI_test",
            "project_field_ref": "PVTF_test",
            "project_field_name": "Résumé",
            "target": {
                "project_id": "PVT_test",
                "project_owner": "newicody",
                "project_number": 3,
                "project_item_id": "PVTI_test",
                "field_ref": "PVTF_test",
                "field_name": "Résumé",
            },
            "boundaries": {
                "read_only_graphql_resolution": True,
            },
        },
    )
    monkeypatch.setattr(
        tool,
        "_acquire_runtime",
        lambda **kwargs: lease,
    )
    captured = {}

    async def fake_prepare(command):
        captured["command"] = command
        return prepared

    monkeypatch.setattr(
        tool,
        "prepare_github_research_love_closed_loop",
        fake_prepare,
    )

    exit_code = tool.main(
        (
            "prepare",
            "--fetch-cycle-report",
            str(tmp_path / "fetch.json"),
            "--run-id",
            "29622831972",
            "--runtime-factory",
            "runtime_factory:create",
            "--policy-decision-id",
            "policy:github-love-operational-test",
            "--issue-number",
            "15",
            "--project-owner",
            "newicody",
            "--project-number",
            "3",
            "--output",
            str(output),
        )
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["valid"] is True
    assert payload["publication_plan_digest"] == (
        "sha256:" + "1" * 64
    )
    assert payload["boundaries"]["remote_publication_performed"] is False
    assert payload["boundaries"]["project_target_resolved_read_only"] is True
    assert payload["input"]["project_target"]["project_item_id"] == "PVTI_test"
    assert captured["command"].project_item_id == "PVTI_test"
    assert captured["command"].project_field_ref == "PVTF_test"
    assert payload["runtime_close"]["receipt"]["action"] == "closed"
    assert lease.closed is True


def test_prepare_blocks_target_resolution_before_runtime_acquisition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "prepared.json"
    monkeypatch.setattr(
        tool,
        "_load_one_fetched_ready_run",
        lambda **kwargs: (
            {
                "repository": "newicody/projects",
                "run_id": "29622831972",
            },
            (object(), object(), object()),
        ),
    )
    monkeypatch.setattr(
        tool.project_target_tool,
        "resolve_project_target_report",
        lambda **kwargs: {
            "schema": (
                "missipy.github.research_projectv2_target_resolution.v1"
            ),
            "valid": False,
            "status": "failed",
            "issues": ["Issue is not attached to the requested ProjectV2"],
            "target": None,
            "boundaries": {
                "read_only_graphql_resolution": True,
            },
        },
    )
    monkeypatch.setattr(
        tool,
        "_acquire_runtime",
        lambda **kwargs: pytest.fail(
            "runtime must not open after target resolution failure"
        ),
    )

    exit_code = tool.main(
        (
            "prepare",
            "--fetch-cycle-report",
            str(tmp_path / "fetch.json"),
            "--run-id",
            "29622831972",
            "--runtime-factory",
            "runtime_factory:create",
            "--policy-decision-id",
            "policy:github-love-operational-test",
            "--issue-number",
            "15",
            "--project-owner",
            "newicody",
            "--project-number",
            "3",
            "--output",
            str(output),
        )
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert exit_code == 2
    assert payload["valid"] is False
    assert "Issue is not attached" in payload["issues"][0]


def test_complete_reuses_prepared_json_without_recomputing_local_stages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    digest = "sha256:" + "2" * 64
    prepared_path = tmp_path / "prepared.json"
    output = tmp_path / "completed.json"
    prepared_path.write_text(
        json.dumps(
            {
                "schema": tool.REPORT_SCHEMA,
                "valid": True,
                "mode": "prepare",
                "status": "publication-confirmation-required",
                "publication_plan_digest": digest,
                "input": {
                    "repository": "newicody/projects",
                    "run_id": "29622831972",
                    "policy_decision_id": (
                        "policy:github-love-operational-test"
                    ),
                    "ready_run": {
                        "repository": "newicody/projects",
                        "run_id": "29622831972",
                    },
                },
                "prepared": {
                    "schema": (
                        "missipy.github.research_love_closed_loop_prepared.v1"
                    ),
                    "valid": True,
                    "status": "publication-confirmation-required",
                    "stages": {
                        "final_deliverable_sql": {
                            "schema": "final",
                            "valid": True,
                        },
                        "publication_plan": {
                            "schema": (
                                "missipy.github.research_love_final_remote_"
                                "publication_plan.v1"
                            ),
                            "plan_digest": digest,
                        },
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    lease = FakeLease()
    wrapped_plan = SimpleNamespace(plan_digest=digest)
    remote = SimpleNamespace(
        valid=True,
        status="published",
        to_mapping=lambda: {
            "schema": (
                "missipy.github.research_love_final_remote_"
                "publication_result.v1"
            ),
            "valid": True,
            "status": "published",
        },
    )
    closure = SimpleNamespace(
        valid=True,
        status="closed",
        issues=(),
        to_mapping=lambda: {
            "valid": True,
            "status": "closed",
            "cycle_closed": True,
        },
    )

    monkeypatch.setattr(
        tool,
        "_acquire_runtime",
        lambda **kwargs: lease,
    )
    monkeypatch.setattr(
        tool,
        "_publication_plan_from_mapping",
        lambda value: wrapped_plan,
    )
    monkeypatch.setattr(
        tool.publication_tool,
        "GitHubCliFinalDeliverablePublicationAdapter",
        lambda **kwargs: SimpleNamespace(),
    )
    monkeypatch.setattr(
        tool.publication_tool,
        "_env_flag",
        lambda name: True,
    )
    monkeypatch.setattr(
        tool,
        "GitHubResearchLoveFinalPublicationExecution",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )
    monkeypatch.setattr(
        tool,
        "execute_github_research_love_final_publication",
        lambda *args, **kwargs: remote,
    )
    monkeypatch.setattr(
        tool,
        "GitHubResearchLovePublicationEvidenceCommand",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )
    monkeypatch.setattr(
        tool,
        "close_github_research_love_cycle",
        lambda command: closure,
    )
    monkeypatch.setattr(
        tool,
        "prepare_github_research_love_closed_loop",
        lambda command: pytest.fail("local stages must not be recomputed"),
    )

    exit_code = tool.main(
        (
            "complete",
            "--prepared-report",
            str(prepared_path),
            "--confirm-plan-digest",
            digest,
            "--runtime-factory",
            "runtime_factory:create",
            "--output",
            str(output),
        )
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["status"] == "closed"
    assert payload["closure"]["cycle_closed"] is True
    assert payload["boundaries"]["prepared_local_stages_recomputed"] is False
    assert lease.closed is True


def test_wrong_digest_is_blocked_before_runtime_acquisition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared_path = tmp_path / "prepared.json"
    output = tmp_path / "completed.json"
    prepared_path.write_text(
        json.dumps(
            {
                "schema": tool.REPORT_SCHEMA,
                "valid": True,
                "mode": "prepare",
                "status": "publication-confirmation-required",
                "publication_plan_digest": "sha256:" + "3" * 64,
                "input": {
                    "repository": "newicody/projects",
                    "run_id": "1",
                    "policy_decision_id": (
                        "policy:github-love-operational-test"
                    ),
                    "ready_run": {
                        "repository": "newicody/projects",
                        "run_id": "1",
                    },
                },
                "prepared": {
                    "schema": (
                        "missipy.github.research_love_closed_loop_prepared.v1"
                    ),
                    "valid": True,
                    "status": "publication-confirmation-required",
                    "stages": {
                        "final_deliverable_sql": {},
                        "publication_plan": {},
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        tool,
        "_acquire_runtime",
        lambda **kwargs: pytest.fail(
            "runtime must not be acquired after digest mismatch"
        ),
    )

    exit_code = tool.main(
        (
            "complete",
            "--prepared-report",
            str(prepared_path),
            "--confirm-plan-digest",
            "sha256:" + "4" * 64,
            "--runtime-factory",
            "runtime_factory:create",
            "--output",
            str(output),
        )
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert exit_code == 2
    assert payload["valid"] is False
    assert "confirm-plan-digest mismatch" in payload["issues"][0]


def test_tool_reuses_existing_adapters_and_creates_no_runtime_infrastructure() -> None:
    source = Path(tool.__file__).read_text(encoding="utf-8")

    assert "prepare_github_research_love_closed_loop(" in source
    assert "execute_github_research_love_final_publication(" in source
    assert "close_github_research_love_cycle(" in source
    assert "acquire_imported_actions_runtime_lease(" in source
    assert "GitHubCliFinalDeliverablePublicationAdapter(" in source
    assert "artifact_loader._load_ready_run_contents(" in source
    assert "lease.ports.projection_port" in source
    assert '"policy_decision_id": _policy_decision_id(' in source
    assert "AUTODOC_LOVE_INSTALLED_RUNTIME_CONFIG" in source
    assert "project_target_tool.resolve_project_target_report(" in source
    assert "project_target_resolved_read_only" in source

    for forbidden in (
        "Scheduler(",
        "Dispatcher(",
        "EventBus(",
        "QdrantClient(",
        "psycopg.connect(",
        "openvino.Core(",
        "CREATE TABLE",
        "subprocess.run(",
        "requests.",
    ):
        assert forbidden not in source
