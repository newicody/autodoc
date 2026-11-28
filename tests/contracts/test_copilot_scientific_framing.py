from __future__ import annotations

import pytest

from contracts.copilot_scientific_framing import (
    REFINED_REQUEST_SCHEMA,
    SERVER_RESPONSE_SCHEMA,
    ScientificFramingContractError,
    canonical_digest,
    validate_initial_advisory,
    validate_refined_request,
    validate_server_response,
)


def _request():
    return {"artifact_ref": "github-request:42"}


def _advisory():
    return {
        "schema": "missipy.github.copilot_advisory.v2",
        "artifact_ref": "github-advisory:42",
        "request_artifact_ref": "github-request:42",
        "concrete_objective": "Produire une analyse scientifique.",
        "expected_result": "Un rapport complet avec représentations adaptées.",
        "provided_constraints": ["Ne pas inventer de données."],
        "success_criteria": ["Résultats sourcés et reproductibles."],
        "trusted": False,
        "usable_as_authority": False,
    }


def _server_response(handshake):
    return {
        "schema": SERVER_RESPONSE_SCHEMA,
        "handshake_ref": handshake.handshake_ref,
        "request_artifact_ref": handshake.request_artifact_ref,
        "initial_advisory_ref": handshake.initial_advisory_ref,
        "initial_advisory_digest": handshake.initial_advisory_digest,
        "coherence_status": "partially_coherent",
        "assessment": "Les représentations proposées sont réalisables sous réserves.",
        "supported_representations": ["tableaux", "courbes temporelles"],
        "unsupported_representations": ["carte thermique sans données spatiales"],
        "available_data": ["dataset:measurements:v3"],
        "missing_data": ["metadata:calibration"],
        "verified_capabilities": ["laboratory:analysis"],
        "constraints": ["Les mesures doivent être datées."],
        "report_outline": ["Méthode", "Résultats", "Limites"],
        "provenance": [{
            "source_ref": "sql:dataset:measurements:v3",
            "observed_at": "2026-11-28T12:00:00Z",
            "freshness": "current",
        }],
        "execution_authorized": False,
        "recursive_clarification_allowed": False,
    }


def test_initial_advisory_creates_stable_handshake_identity():
    handshake = validate_initial_advisory(_request(), _advisory())
    again = validate_initial_advisory(_request(), _advisory())
    assert handshake == again
    assert handshake.handshake_ref.startswith("copilot-framing:")


def test_server_response_is_correlated_and_cannot_authorize_execution():
    handshake = validate_initial_advisory(_request(), _advisory())
    response = _server_response(handshake)
    assert validate_server_response(handshake, response) == response

    invalid = {**response, "execution_authorized": True}
    with pytest.raises(ScientificFramingContractError, match="cannot authorize"):
        validate_server_response(handshake, invalid)


def test_server_response_rejects_stale_or_unrelated_handshake():
    handshake = validate_initial_advisory(_request(), _advisory())
    response = _server_response(handshake)
    invalid = {**response, "initial_advisory_digest": "0" * 64}
    with pytest.raises(ScientificFramingContractError, match="digest mismatch"):
        validate_server_response(handshake, invalid)


def test_refined_request_is_bound_to_the_single_server_response():
    handshake = validate_initial_advisory(_request(), _advisory())
    response = _server_response(handshake)
    refined = {
        "schema": REFINED_REQUEST_SCHEMA,
        "handshake_ref": handshake.handshake_ref,
        "request_artifact_ref": handshake.request_artifact_ref,
        "initial_advisory_ref": handshake.initial_advisory_ref,
        "server_response_digest": canonical_digest(response),
        "concrete_objective": "Réaliser l'analyse sur les données disponibles.",
        "expected_result": "Un rapport avec tableaux et courbes temporelles.",
        "provided_constraints": ["Mesures datées."],
        "success_criteria": ["Chaque courbe cite sa source."],
        "scientific_representations": ["tableaux", "courbes temporelles"],
        "trusted": False,
        "usable_as_authority": False,
    }
    assert validate_refined_request(handshake, response, refined) == refined

    altered = {**refined, "server_response_digest": "f" * 64}
    with pytest.raises(ScientificFramingContractError, match="server_response_digest"):
        validate_refined_request(handshake, response, altered)


def test_refined_request_rejects_authority_or_empty_criteria():
    handshake = validate_initial_advisory(_request(), _advisory())
    response = _server_response(handshake)
    refined = {
        "schema": REFINED_REQUEST_SCHEMA,
        "handshake_ref": handshake.handshake_ref,
        "request_artifact_ref": handshake.request_artifact_ref,
        "initial_advisory_ref": handshake.initial_advisory_ref,
        "server_response_digest": canonical_digest(response),
        "concrete_objective": "Objectif.",
        "expected_result": "Rapport.",
        "provided_constraints": [],
        "success_criteria": [],
        "scientific_representations": ["tableaux"],
        "trusted": False,
        "usable_as_authority": False,
    }
    with pytest.raises(ScientificFramingContractError, match="success_criteria"):
        validate_refined_request(handshake, response, refined)
    with pytest.raises(ScientificFramingContractError, match="cannot be authoritative"):
        validate_refined_request(
            handshake, response, {**refined, "success_criteria": ["ok"], "usable_as_authority": True}
        )
