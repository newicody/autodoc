from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "templates/github/projects-repository"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RECONCILE = _load(
    "reconcile_projectv2_configuration_0284",
    BUNDLE / "scripts/reconcile_projectv2_configuration.py",
)
PROJECT = _load(
    "project_copilot_advisory_fields_0284",
    BUNDLE / "scripts/project_copilot_advisory_fields.py",
)


class ConfigurationTransport:
    def __init__(self) -> None:
        self.rest_calls: list[tuple[str, str, dict[str, Any] | None]] = []
        self.graphql_calls: list[tuple[str, dict[str, Any]]] = []

    def rest(self, method: str, endpoint: str, payload=None):
        data = None if payload is None else dict(payload)
        self.rest_calls.append((method, endpoint, data))
        if method == "GET" and endpoint == "users/newicody":
            return {"id": 42, "login": "newicody"}
        if method == "GET" and endpoint.endswith("/fields?per_page=100"):
            return [
                {"id": 1, "name": "Title", "data_type": "title"},
                {"id": 2, "name": "Status", "data_type": "single_select"},
            ]
        raise AssertionError((method, endpoint, payload))

    def graphql(self, query: str, variables):
        self.graphql_calls.append((query, dict(variables)))
        return {
            "data": {
                "user": {
                    "projectV2": {
                        "views": {"nodes": [{"name": "Tous"}]}
                    }
                }
            }
        }


class ProjectionTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def graphql(self, query: str, variables):
        values = dict(variables)
        self.calls.append((query, values))
        if "query(" in query:
            return _projection_inventory()
        return {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "ITEM"}}}}


def _projection_inventory() -> dict[str, Any]:
    fields = [
        {"__typename": "ProjectV2SingleSelectField", "id": "F_STATUS", "name": "Copilot", "dataType": "SINGLE_SELECT", "options": [{"id": "OPT_DONE", "name": "Terminé"}]},
        {"__typename": "ProjectV2Field", "id": "F_SUMMARY", "name": "Avis Copilot", "dataType": "TEXT"},
        {"__typename": "ProjectV2Field", "id": "F_ROUTE", "name": "Route Copilot", "dataType": "TEXT"},
        {"__typename": "ProjectV2Field", "id": "F_CONF", "name": "Confiance Copilot", "dataType": "NUMBER"},
        {"__typename": "ProjectV2Field", "id": "F_DATE", "name": "Dernière mise à jour", "dataType": "DATE"},
        {"__typename": "ProjectV2Field", "id": "F_ARTIFACT", "name": "Artefact", "dataType": "TEXT"},
        {"__typename": "ProjectV2Field", "id": "F_CYCLE", "name": "Cycle", "dataType": "TEXT"},
    ]
    return {
        "data": {
            "user": {"projectV2": {"id": "PROJECT", "fields": {"nodes": fields}}},
            "repository": {
                "issue": {
                    "projectItems": {
                        "nodes": [
                            {"id": "ITEM", "project": {"id": "PROJECT", "number": 3}}
                        ]
                    }
                }
            },
        }
    }


def _preview(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "missipy.github.copilot_advisory_publication_preview.v1",
                "source_candidate_ref": "source-candidate:cycle-1",
                "advisory_context_ref": "ctx:github-advisory:1",
                "advisory_artifact_ref": "github-advisory:1",
                "summary": "Avis consultatif",
                "suggested_route": "Examiner cette piste",
                "questions": [],
                "risks": [],
                "confidence": 0.75,
                "advisory_is_authority": False,
                "operator_decision_required": True,
                "publication_gate_required": True,
                "github_mutation_performed": False,
            }
        ),
        encoding="utf-8",
    )


def test_configuration_plan_lists_missing_fields_views_and_manual_layout() -> None:
    transport = ConfigurationTransport()
    plan = RECONCILE.plan_projectv2_configuration(
        RECONCILE.ProjectConfigurationCommand(
            configuration_path=BUNDLE / "projectv2_views.json"
        ),
        transport=transport,
    )
    assert plan.valid
    assert any(item["name"] == "Avis Copilot" for item in plan.missing_fields)
    assert any(item["name"] == "Copilot" for item in plan.missing_views)
    assert "Tous" in plan.existing_views
    assert any("group_by=Thème" in step for step in plan.manual_layout_steps)
    assert not any(method == "POST" for method, _, _ in transport.rest_calls)


def test_configuration_execute_requires_digest_and_both_gates() -> None:
    transport = ConfigurationTransport()
    command = RECONCILE.ProjectConfigurationCommand(
        configuration_path=BUNDLE / "projectv2_views.json",
        execute=True,
        remote_mutation_allowed=True,
        project_configuration_allowed=False,
    )
    try:
        RECONCILE.execute_projectv2_configuration(command, transport=transport)
    except ValueError as exc:
        assert "configuration mutation is locked" in str(exc)
    else:
        raise AssertionError("one ProjectV2 configuration gate was accepted")


def test_copilot_projection_is_hint_only_and_excludes_server_fields(tmp_path: Path) -> None:
    preview = tmp_path / "preview.json"
    _preview(preview)
    plan = PROJECT.plan_copilot_field_projection(
        PROJECT.CopilotFieldProjectionCommand(
            configuration_path=BUNDLE / "projectv2_views.json",
            preview_path=preview,
            repository="newicody/projects",
            issue_number=7,
            policy_decision_id="policy:test:projection",
            operator_decision="approve",
            updated_date="2026-07-14",
        ),
        transport=ProjectionTransport(),
    )
    assert plan.valid
    names = {mutation.field_name for mutation in plan.mutations}
    assert names == {
        "Copilot",
        "Avis Copilot",
        "Route Copilot",
        "Confiance Copilot",
        "Dernière mise à jour",
        "Artefact",
        "Cycle",
    }
    assert "Résumé" not in names
    assert "Serveur" not in names
    assert plan.advisory_is_authority is False


def test_copilot_projection_execute_requires_exact_digest(tmp_path: Path) -> None:
    preview = tmp_path / "preview.json"
    _preview(preview)
    transport = ProjectionTransport()
    command = PROJECT.CopilotFieldProjectionCommand(
        configuration_path=BUNDLE / "projectv2_views.json",
        preview_path=preview,
        repository="newicody/projects",
        issue_number=7,
        policy_decision_id="policy:test:projection",
        operator_decision="approve",
        updated_date="2026-07-14",
        execute=True,
        remote_mutation_allowed=True,
        project_projection_allowed=True,
        confirm_plan_digest="wrong",
    )
    try:
        PROJECT.execute_copilot_field_projection(command, transport=transport)
    except ValueError as exc:
        assert "confirm-plan-digest mismatch" in str(exc)
    else:
        raise AssertionError("a wrong projection digest was accepted")


class MutableConfigurationTransport:
    def __init__(self) -> None:
        self.fields: list[dict[str, Any]] = [
            {"id": 1, "name": "Title", "data_type": "title"},
            {"id": 2, "name": "Status", "data_type": "single_select"},
        ]
        self.views: list[str] = []
        self.next_id = 10

    def rest(self, method: str, endpoint: str, payload=None):
        if method == "GET" and endpoint == "users/newicody":
            return {"id": 42, "login": "newicody"}
        if method == "GET" and endpoint.endswith("/fields?per_page=100"):
            return list(self.fields)
        if method == "POST" and endpoint.endswith("/fields"):
            value = dict(payload)
            value["id"] = self.next_id
            self.next_id += 1
            if "single_select_options" in value:
                value["options"] = [
                    {"id": f"option-{self.next_id}-{index}", "name": {"raw": option["name"]}}
                    for index, option in enumerate(value["single_select_options"])
                ]
            self.fields.append(value)
            return value
        if method == "POST" and endpoint.endswith("/views"):
            self.views.append(str(payload["name"]))
            return {"value": dict(payload)}
        raise AssertionError((method, endpoint, payload))

    def graphql(self, query: str, variables):
        return {
            "data": {
                "user": {
                    "projectV2": {
                        "views": {"nodes": [{"name": name} for name in self.views]}
                    }
                }
            }
        }


def test_configuration_execute_creates_missing_objects_after_exact_plan() -> None:
    transport = MutableConfigurationTransport()
    preview = RECONCILE.plan_projectv2_configuration(
        RECONCILE.ProjectConfigurationCommand(
            configuration_path=BUNDLE / "projectv2_views.json"
        ),
        transport=transport,
    )
    result = RECONCILE.execute_projectv2_configuration(
        RECONCILE.ProjectConfigurationCommand(
            configuration_path=BUNDLE / "projectv2_views.json",
            execute=True,
            remote_mutation_allowed=True,
            project_configuration_allowed=True,
            confirm_plan_digest=preview.plan_digest,
        ),
        transport=transport,
    )
    assert result.valid
    assert result.mutation_performed
    assert not result.missing_fields
    assert not result.missing_views
    assert {"Recherches", "Résultats", "Copilot"}.issubset(transport.views)


def test_copilot_projection_execute_updates_only_declared_fields(tmp_path: Path) -> None:
    preview_path = tmp_path / "preview.json"
    _preview(preview_path)
    transport = ProjectionTransport()
    base = PROJECT.CopilotFieldProjectionCommand(
        configuration_path=BUNDLE / "projectv2_views.json",
        preview_path=preview_path,
        repository="newicody/projects",
        issue_number=7,
        policy_decision_id="policy:test:projection",
        operator_decision="approve",
        updated_date="2026-07-14",
        remote_mutation_allowed=True,
        project_projection_allowed=True,
    )
    preview = PROJECT.plan_copilot_field_projection(base, transport=transport)
    result = PROJECT.execute_copilot_field_projection(
        PROJECT.CopilotFieldProjectionCommand(
            configuration_path=base.configuration_path,
            preview_path=base.preview_path,
            repository=base.repository,
            issue_number=base.issue_number,
            policy_decision_id=base.policy_decision_id,
            operator_decision=base.operator_decision,
            updated_date=base.updated_date,
            execute=True,
            remote_mutation_allowed=True,
            project_projection_allowed=True,
            confirm_plan_digest=preview.plan_digest,
        ),
        transport=transport,
    )
    assert result.mutation_performed
    mutation_calls = [variables for query, variables in transport.calls if "mutation(" in query]
    assert len(mutation_calls) == 7
    assert {call["field"] for call in mutation_calls} == {
        "F_STATUS", "F_SUMMARY", "F_ROUTE", "F_CONF", "F_DATE", "F_ARTIFACT", "F_CYCLE"
    }
