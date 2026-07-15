from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

from context.specialist_capability_growth_projects_publication_plan_0286 import (
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA,
    SpecialistCapabilityGrowthProjectV2FieldMutation,
    SpecialistCapabilityGrowthProjectsPublicationPlan,
)

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = (
    ROOT
    / "tools/apply_specialist_capability_growth_projects_projection_0286.py"
)


def _load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location("phase_0286_r6_cli", TOOL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _plan(module: ModuleType) -> SpecialistCapabilityGrowthProjectsPublicationPlan:
    mutation = SpecialistCapabilityGrowthProjectV2FieldMutation(
        field_name="Spécialiste",
        desired_value="specialist:demo",
        current_value=None,
        action="set",
    )
    body = "approved projection\n"
    body_digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    draft = SpecialistCapabilityGrowthProjectsPublicationPlan(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA,
        valid=True,
        action="create_comment_and_set_fields",
        issues=(),
        repository="newicody/projects",
        issue_number=42,
        project_id="PVT_project3",
        project_item_id="PVTI_item42",
        policy_decision_id="policy:0286:r6:test",
        review_ref="review:42",
        revision_ref="revision:42",
        sql_ref="sql:42",
        decision_ref="decision:42",
        projection_digest_sha256="a" * 64,
        marker="autodoc:specialist-capability-growth:test",
        comment_action="create",
        comment_body=body,
        comment_body_sha256=body_digest,
        existing_comment_id=None,
        existing_comment_url="",
        projectv2_action="set",
        projectv2_field_mutations=(mutation,),
        plan_digest="0" * 64,
    )
    return SpecialistCapabilityGrowthProjectsPublicationPlan(
        schema=draft.schema,
        valid=draft.valid,
        action=draft.action,
        issues=draft.issues,
        repository=draft.repository,
        issue_number=draft.issue_number,
        project_id=draft.project_id,
        project_item_id=draft.project_item_id,
        policy_decision_id=draft.policy_decision_id,
        review_ref=draft.review_ref,
        revision_ref=draft.revision_ref,
        sql_ref=draft.sql_ref,
        decision_ref=draft.decision_ref,
        projection_digest_sha256=draft.projection_digest_sha256,
        marker=draft.marker,
        comment_action=draft.comment_action,
        comment_body=draft.comment_body,
        comment_body_sha256=draft.comment_body_sha256,
        existing_comment_id=draft.existing_comment_id,
        existing_comment_url=draft.existing_comment_url,
        projectv2_action=draft.projectv2_action,
        projectv2_field_mutations=draft.projectv2_field_mutations,
        plan_digest=module.recompute_plan_digest(draft),
    )


def _mapping(plan: SpecialistCapabilityGrowthProjectsPublicationPlan) -> dict[str, object]:
    return plan.to_mapping()


def test_rehydrate_verifies_comment_and_plan_digests(tmp_path: Path) -> None:
    module = _load_tool()
    plan = _plan(module)
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(_mapping(plan)), encoding="utf-8")
    loaded = module.load_publication_plan(path)
    assert loaded.plan_digest == plan.plan_digest

    tampered = _mapping(plan)
    tampered["sql_ref"] = "sql:tampered"
    path.write_text(json.dumps(tampered), encoding="utf-8")
    try:
        module.load_publication_plan(path)
    except ValueError as exc:
        assert "plan_digest mismatch" in str(exc)
    else:
        raise AssertionError("tampered plan must be rejected")


def test_preview_does_not_construct_the_gh_port(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_tool()
    plan = _plan(module)
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(_mapping(plan)), encoding="utf-8")

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("preview must not create the gh port")

    monkeypatch.setattr(
        module,
        "GhSpecialistCapabilityGrowthExecutionPort",
        forbidden,
    )
    assert (
        module.main(
            (
                "--plan",
                str(path),
                "--operator-decision",
                "approve",
                "--format",
                "json",
            )
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["result"]["mode"] == "preview"
    assert report["result"]["github_mutation_performed"] is False


def test_project_field_metadata_supports_text_and_single_select(
    monkeypatch,
) -> None:
    module = _load_tool()
    port = module.GhSpecialistCapabilityGrowthExecutionPort("gh")
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_graphql(query: str, variables: dict[str, object]) -> dict[str, object]:
        calls.append((query, variables))
        if "fields(first: 100)" in query:
            return {
                "data": {
                    "node": {
                        "fields": {
                            "nodes": [
                                {
                                    "id": "PVTF_text",
                                    "name": "Spécialiste",
                                    "dataType": "TEXT",
                                },
                                {
                                    "id": "PVTSSF_decision",
                                    "name": "Décision capacité",
                                    "dataType": "SINGLE_SELECT",
                                    "options": [
                                        {"id": "opt_approve", "name": "approve"}
                                    ],
                                },
                            ]
                        }
                    }
                }
            }
        return {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_item42"}}}}

    monkeypatch.setattr(port, "_gh_graphql", fake_graphql)
    result = port.apply_projectv2_fields(
        project_id="PVT_project3",
        project_item_id="PVTI_item42",
        field_values=(
            ("Spécialiste", "specialist:demo"),
            ("Décision capacité", "approve"),
        ),
    )
    assert result.action == "updated"
    assert result.changed_fields == (
        "Spécialiste",
        "Décision capacité",
    )
    assert len(calls) == 3
