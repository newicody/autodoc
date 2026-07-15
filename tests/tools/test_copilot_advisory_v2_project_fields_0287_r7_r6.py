from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Mapping

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "templates/github/projects-repository/scripts"
SCRIPT = SCRIPTS / "project_copilot_advisory_v2_fields.py"


def _load() -> ModuleType:
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location("copilot_v2_fields", SCRIPT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPTS))


def _files(tmp_path: Path) -> tuple[Path, Path]:
    config = {
        "schema": "autodoc.github.projects_repository_configuration.v1",
        "project": {"owner_kind": "user", "owner": "newicody", "number": 3},
        "copilot_projection": {
            "status_field": "Copilot",
            "status_value": "Terminé",
            "summary_field": "Avis Copilot",
            "route_field": "Route Copilot",
            "confidence_field": "Confiance Copilot",
            "updated_field": "Dernière mise à jour",
            "artifact_field": "Artefact",
            "cycle_field": "Cycle",
        },
    }
    preview = {
        "schema": "missipy.github.copilot_advisory_publication_preview.v2",
        "source_candidate_ref": "request:1",
        "advisory_artifact_ref": "advisory:1",
        "concrete_objective": "Étudier la demande.",
        "expected_result": "Produire un avis observable.",
        "provided_constraints": ["Rester consultatif."],
        "success_criteria": ["Le board affiche l’avis."],
        "repository": "newicody/projects",
        "issue_number": 7,
        "advisory_schema": "missipy.github.copilot_advisory.v2",
        "request_authoritative": True,
        "advisory_is_authority": False,
        "operator_decision_required": True,
        "publication_gate_required": True,
        "github_mutation_performed": False,
        "remote_mutation_allowed": False,
    }
    config_path = tmp_path / "projectv2_views.json"
    preview_path = tmp_path / "preview.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    preview_path.write_text(json.dumps(preview), encoding="utf-8")
    return config_path, preview_path


class FakeTransport:
    def __init__(self, *, corrupt_readback: bool = False) -> None:
        self.corrupt_readback = corrupt_readback
        self.writes: list[Mapping[str, Any]] = []
        self.field_names = {
            "FIELD_STATUS": "Copilot",
            "FIELD_SUMMARY": "Avis Copilot",
            "FIELD_UPDATED": "Dernière mise à jour",
            "FIELD_ARTIFACT": "Artefact",
            "FIELD_CYCLE": "Cycle",
        }

    def graphql(self, query: str, variables: Mapping[str, Any]) -> Any:
        if "projectOwner" in variables:
            return self._inventory()
        if "updateProjectV2ItemFieldValue" in query:
            self.writes.append(dict(variables))
            return {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "ITEM"}}}}
        if set(variables) == {"item"}:
            return self._readback()
        raise AssertionError(f"unexpected GraphQL call: {variables}")

    def _inventory(self) -> dict[str, Any]:
        fields = [
            {
                "__typename": "ProjectV2SingleSelectField",
                "id": "FIELD_STATUS",
                "name": "Copilot",
                "dataType": "SINGLE_SELECT",
                "options": [{"id": "OPTION_DONE", "name": "Terminé"}],
            },
            *(
                {
                    "__typename": "ProjectV2Field",
                    "id": field_id,
                    "name": name,
                    "dataType": "TEXT" if name != "Dernière mise à jour" else "DATE",
                }
                for field_id, name in self.field_names.items()
                if field_id != "FIELD_STATUS"
            ),
        ]
        return {
            "data": {
                "user": {
                    "projectV2": {
                        "id": "PROJECT",
                        "fields": {"nodes": fields},
                    }
                },
                "repository": {
                    "issue": {
                        "projectItems": {
                            "nodes": [
                                {
                                    "id": "ITEM",
                                    "project": {"id": "PROJECT", "number": 3},
                                }
                            ]
                        }
                    }
                },
            }
        }

    def _readback(self) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        for write in self.writes:
            field_id = str(write["field"])
            field_name = self.field_names[field_id]
            value = write["value"]
            field = {"id": field_id, "name": field_name}
            if "singleSelectOptionId" in value:
                entry = {
                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                    "optionId": value["singleSelectOptionId"],
                    "name": "Terminé",
                    "field": field,
                }
            elif "date" in value:
                entry = {
                    "__typename": "ProjectV2ItemFieldDateValue",
                    "date": value["date"],
                    "field": field,
                }
            else:
                entry = {
                    "__typename": "ProjectV2ItemFieldTextValue",
                    "text": value["text"],
                    "field": field,
                }
            nodes.append(entry)
        if self.corrupt_readback and nodes:
            nodes[-1]["text"] = "corrupted"
        return {
            "data": {
                "node": {
                    "id": "ITEM",
                    "fieldValues": {"nodes": nodes},
                }
            }
        }


def _command(module: ModuleType, config: Path, preview: Path, **changes: Any) -> Any:
    values = {
        "configuration_path": config,
        "preview_path": preview,
        "repository": "newicody/projects",
        "issue_number": 7,
        "policy_decision_id": "policy:copilot-v2-board",
        "operator_decision": "approve",
        "updated_date": "2026-07-15",
    }
    values.update(changes)
    return module.CopilotFieldProjectionCommand(**values)


def test_v2_plan_uses_generic_fields_and_execute_verifies_readback(tmp_path: Path) -> None:
    module = _load()
    config, preview = _files(tmp_path)
    plan = module.plan_copilot_v2_field_projection(
        _command(module, config, preview),
        transport=FakeTransport(),
    )
    assert plan.valid is True
    assert [item.field_name for item in plan.mutations] == [
        "Copilot",
        "Avis Copilot",
        "Dernière mise à jour",
        "Artefact",
        "Cycle",
    ]
    assert plan.to_mapping()["route_field_mutated"] is False
    assert plan.to_mapping()["confidence_field_mutated"] is False

    execute = _command(
        module,
        config,
        preview,
        execute=True,
        remote_mutation_allowed=True,
        project_projection_allowed=True,
        confirm_plan_digest=plan.plan_digest,
    )
    result = module.execute_copilot_v2_field_projection(
        execute,
        transport=FakeTransport(),
    )
    assert result.mutation_performed is True
    assert result.readback_verified is True


def test_v2_execute_fails_closed_on_readback_mismatch(tmp_path: Path) -> None:
    module = _load()
    config, preview = _files(tmp_path)
    plan = module.plan_copilot_v2_field_projection(
        _command(module, config, preview),
        transport=FakeTransport(),
    )
    execute = _command(
        module,
        config,
        preview,
        execute=True,
        remote_mutation_allowed=True,
        project_projection_allowed=True,
        confirm_plan_digest=plan.plan_digest,
    )
    with pytest.raises(RuntimeError, match="ProjectV2 readback mismatch"):
        module.execute_copilot_v2_field_projection(
            execute,
            transport=FakeTransport(corrupt_readback=True),
        )
