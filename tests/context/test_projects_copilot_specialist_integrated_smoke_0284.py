from __future__ import annotations

from types import SimpleNamespace

from context.projects_copilot_specialist_integrated_smoke_0284 import (
    PROJECTS_FIELD_PREVIEW_SCHEMA,
    _all_strings,
    _first_value_for_key,
    _project_fields_preview,
    _project_fields_preview_valid,
)


def _projection() -> SimpleNamespace:
    return SimpleNamespace(
        summary="Avis consultatif borné",
        suggested_route="route:portable-specialist",
        confidence=0.75,
        advisory_artifact_ref="github-advisory:0284-r7",
    )


def _command() -> SimpleNamespace:
    return SimpleNamespace(
        repository="newicody/projects",
        issue_number=77,
        policy_decision_id="policy:0284:r7",
        updated_date="2026-07-14",
        cycle_ref="cycle:0284-r7",
    )


def test_projects_field_preview_matches_the_copied_bundle_contract() -> None:
    preview = _project_fields_preview(
        command=_command(),
        projection=_projection(),
    )

    assert preview["schema"] == PROJECTS_FIELD_PREVIEW_SCHEMA
    assert preview["configuration_owner"] == "newicody/projects"
    assert preview["fields"] == {
        "Copilot": "Terminé",
        "Avis Copilot": "Avis consultatif borné",
        "Route Copilot": "route:portable-specialist",
        "Confiance Copilot": 0.75,
        "Dernière mise à jour": "2026-07-14",
        "Artefact": "github-advisory:0284-r7",
        "Cycle": "cycle:0284-r7",
    }
    assert preview["forbidden_fields_untouched"] == ["Résumé", "Serveur"]
    assert preview["remote_mutation_allowed"] is False
    assert preview["projectv2_mutation_performed"] is False
    assert _project_fields_preview_valid(preview) is True


def test_projects_field_preview_rejects_authority_or_server_field_drift() -> None:
    preview = _project_fields_preview(
        command=_command(),
        projection=_projection(),
    )
    preview["advisory_is_authority"] = True
    preview["fields"]["Serveur"] = "Terminé"

    assert _project_fields_preview_valid(preview) is False


def test_recursive_reference_scan_finds_injected_context_and_candidate() -> None:
    mapping = {
        "orientation": {
            "context_refs": ["ctx:github-advisory:abc"],
            "source_candidate_ref": "source-candidate:github-request:123",
        }
    }

    values = _all_strings(mapping)

    assert "ctx:github-advisory:abc" in values
    assert "source-candidate:github-request:123" in values


def test_final_ref_lookup_is_recursive_and_bounded() -> None:
    mapping = {
        "specialist_smoke": {
            "existing_smoke": {
                "result": {"final_ref": "final:laboratory:0284-r7"}
            }
        }
    }

    assert (
        _first_value_for_key(mapping, "final_ref")
        == "final:laboratory:0284-r7"
    )
    assert _first_value_for_key(mapping, "missing") == ""
