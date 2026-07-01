from __future__ import annotations

import pytest

from context.local_server_boundary import (
    LocalServerBoundary,
    LocalServerBoundaryPolicy,
    LocalServerEndpoint,
    build_local_server_boundary,
    default_local_server_endpoints,
)


def test_default_local_server_boundary_is_contract_only_for_newicody_autodoc() -> None:
    boundary = build_local_server_boundary()

    assert boundary.schema == "missipy.local_server.boundary.v1"
    assert boundary.policy.repository == "newicody/autodoc"
    assert boundary.policy.implementation_state == "contract_only"
    assert boundary.policy.bind_host == "127.0.0.1"
    assert boundary.policy.external_network_allowed is False
    assert boundary.policy.github_api_allowed is False
    assert boundary.policy.token_allowed is False
    assert boundary.policy.daemon_allowed is False
    assert boundary.policy.scheduler_autoload_allowed is False
    assert boundary.policy.model_execution_allowed is False


def test_default_endpoint_names_are_stable() -> None:
    boundary = build_local_server_boundary()

    assert boundary.endpoint_names == (
        "status_get",
        "source_candidate_create",
        "source_candidate_decide",
        "e5_context_intake",
        "report_get",
    )


def test_endpoint_projection_is_serializable_and_explicit() -> None:
    boundary = build_local_server_boundary()
    payload = boundary.to_json_dict()

    assert payload["endpoint_count"] == 5
    assert payload["policy"]["repository"] == "newicody/autodoc"
    assert payload["endpoints"][0] == {
        "name": "status_get",
        "method": "GET",
        "path": "/status",
        "description": "Read passive local runtime status.",
        "request_schema": "missipy.local_server.empty_request.v1",
        "response_schema": "missipy.local_server.status_response.v1",
        "mutates_local_state": False,
        "implemented": False,
        "loopback_only": True,
        "requires_token": False,
        "external_network": False,
        "side_effects": [],
    }


def test_text_projection_mentions_disabled_boundaries() -> None:
    text = build_local_server_boundary().to_text()

    assert "repository: newicody/autodoc" in text
    assert "network: disabled" in text
    assert "github_api: disabled" in text
    assert "tokens: disabled" in text
    assert "scheduler_autoload: disabled" in text
    assert "model_execution: disabled" in text


def test_boundary_rejects_external_network_endpoint() -> None:
    endpoint = LocalServerEndpoint(
        name="bad",
        method="GET",
        path="/bad",
        description="Bad endpoint.",
        request_schema="bad.request.v1",
        response_schema="bad.response.v1",
        external_network=True,
    )

    with pytest.raises(ValueError, match="external network"):
        LocalServerBoundary(endpoints=(endpoint,))


def test_policy_rejects_non_loopback_host() -> None:
    with pytest.raises(ValueError, match="loopback-only"):
        LocalServerBoundaryPolicy(bind_host="0.0.0.0")


def test_default_endpoints_are_contract_only_and_loopback_only() -> None:
    for endpoint in default_local_server_endpoints():
        assert endpoint.implemented is False
        assert endpoint.loopback_only is True
        assert endpoint.external_network is False
        assert endpoint.requires_token is False
