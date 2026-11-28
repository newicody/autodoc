"""Typed contract for the one-shot Copilot/server scientific-framing exchange.

This module validates immutable artifacts only. It does not evaluate component
capabilities, invoke Copilot, publish to GitHub, admit work, or orchestrate tasks.
Those actions remain at their existing server and adapter boundaries.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from typing import Any

INITIAL_SCHEMA = "missipy.github.copilot_advisory.v2"
SERVER_RESPONSE_SCHEMA = "missipy.github.server_scientific_framing_response.v1"
REFINED_REQUEST_SCHEMA = "missipy.github.copilot_refined_research_request.v1"
HANDSHAKE_SCHEMA = "missipy.github.copilot_scientific_framing_handshake.v1"
_ALLOWED_STATUSES = {"coherent", "partially_coherent", "incoherent"}


class ScientificFramingContractError(ValueError):
    """Raised when an artifact violates the one-shot framing contract."""


@dataclass(frozen=True, slots=True)
class FramingHandshake:
    handshake_ref: str
    request_artifact_ref: str
    initial_advisory_ref: str
    initial_advisory_digest: str

    def to_mapping(self) -> dict[str, str]:
        return {
            "schema": HANDSHAKE_SCHEMA,
            "handshake_ref": self.handshake_ref,
            "request_artifact_ref": self.request_artifact_ref,
            "initial_advisory_ref": self.initial_advisory_ref,
            "initial_advisory_digest": self.initial_advisory_digest,
            "exchange_limit": "one_server_response_and_one_copilot_refinement",
            "recursive_clarification_allowed": "false",
            "execution_authorized": "false",
        }


def canonical_digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_initial_advisory(
    request: Mapping[str, Any], advisory: Mapping[str, Any]
) -> FramingHandshake:
    """Bind the existing Copilot v2 first opinion to its authoritative request."""
    if advisory.get("schema") != INITIAL_SCHEMA:
        raise ScientificFramingContractError("unexpected initial advisory schema")
    request_ref = _required_text("request artifact_ref", request.get("artifact_ref"))
    advisory_request_ref = _required_text(
        "advisory request_artifact_ref", advisory.get("request_artifact_ref")
    )
    if advisory_request_ref != request_ref:
        raise ScientificFramingContractError("initial advisory/request mismatch")
    advisory_ref = _required_text("advisory artifact_ref", advisory.get("artifact_ref"))
    for name in (
        "concrete_objective",
        "expected_result",
    ):
        _required_text(name, advisory.get(name))
    for name in ("provided_constraints", "success_criteria"):
        _string_list(name, advisory.get(name))
    if not _string_list("success_criteria", advisory.get("success_criteria")):
        raise ScientificFramingContractError("success_criteria must not be empty")
    if advisory.get("trusted") is not False:
        raise ScientificFramingContractError("initial advisory must remain untrusted")
    if advisory.get("usable_as_authority") is not False:
        raise ScientificFramingContractError("initial advisory cannot be authoritative")
    digest = canonical_digest(advisory)
    identity = hashlib.sha256(
        "\\0".join((request_ref, advisory_ref, digest)).encode("utf-8")
    ).hexdigest()
    return FramingHandshake(
        handshake_ref=f"copilot-framing:{identity}",
        request_artifact_ref=request_ref,
        initial_advisory_ref=advisory_ref,
        initial_advisory_digest=digest,
    )


def validate_server_response(
    handshake: FramingHandshake, response: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate the server's single coherence response; do not infer its content."""
    if response.get("schema") != SERVER_RESPONSE_SCHEMA:
        raise ScientificFramingContractError("unexpected server response schema")
    if response.get("handshake_ref") != handshake.handshake_ref:
        raise ScientificFramingContractError("server response handshake mismatch")
    if response.get("request_artifact_ref") != handshake.request_artifact_ref:
        raise ScientificFramingContractError("server response request mismatch")
    if response.get("initial_advisory_ref") != handshake.initial_advisory_ref:
        raise ScientificFramingContractError("server response advisory mismatch")
    if response.get("initial_advisory_digest") != handshake.initial_advisory_digest:
        raise ScientificFramingContractError("server response advisory digest mismatch")
    status = _required_text("coherence_status", response.get("coherence_status"))
    if status not in _ALLOWED_STATUSES:
        raise ScientificFramingContractError("unsupported coherence_status")
    _required_text("assessment", response.get("assessment"))
    _string_list("supported_representations", response.get("supported_representations"))
    _string_list("unsupported_representations", response.get("unsupported_representations"))
    _string_list("available_data", response.get("available_data"))
    _string_list("missing_data", response.get("missing_data"))
    _string_list("verified_capabilities", response.get("verified_capabilities"))
    _string_list("constraints", response.get("constraints"))
    _string_list("report_outline", response.get("report_outline"))
    provenance = response.get("provenance")
    if not isinstance(provenance, list):
        raise ScientificFramingContractError("provenance must be an array")
    for index, item in enumerate(provenance):
        if not isinstance(item, Mapping):
            raise ScientificFramingContractError(f"provenance[{index}] must be an object")
        _required_text(f"provenance[{index}].source_ref", item.get("source_ref"))
        _required_text(f"provenance[{index}].observed_at", item.get("observed_at"))
        _required_text(f"provenance[{index}].freshness", item.get("freshness"))
    if response.get("execution_authorized") is not False:
        raise ScientificFramingContractError("server response cannot authorize execution")
    if response.get("recursive_clarification_allowed") is not False:
        raise ScientificFramingContractError("recursive clarification must be disabled")
    return dict(response)


def validate_refined_request(
    handshake: FramingHandshake,
    server_response: Mapping[str, Any],
    refined: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate Copilot's single reformulation against the exact server response."""
    response = validate_server_response(handshake, server_response)
    if refined.get("schema") != REFINED_REQUEST_SCHEMA:
        raise ScientificFramingContractError("unexpected refined request schema")
    for field, expected in (
        ("handshake_ref", handshake.handshake_ref),
        ("request_artifact_ref", handshake.request_artifact_ref),
        ("initial_advisory_ref", handshake.initial_advisory_ref),
        ("server_response_digest", canonical_digest(response)),
    ):
        if refined.get(field) != expected:
            raise ScientificFramingContractError(f"refined request {field} mismatch")
    _required_text("concrete_objective", refined.get("concrete_objective"))
    _required_text("expected_result", refined.get("expected_result"))
    _string_list("provided_constraints", refined.get("provided_constraints"))
    criteria = _string_list("success_criteria", refined.get("success_criteria"))
    if not criteria:
        raise ScientificFramingContractError("refined success_criteria must not be empty")
    _string_list("scientific_representations", refined.get("scientific_representations"))
    if refined.get("trusted") is not False:
        raise ScientificFramingContractError("refined request must remain untrusted")
    if refined.get("usable_as_authority") is not False:
        raise ScientificFramingContractError("refined request cannot be authoritative")
    return dict(refined)


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScientificFramingContractError(f"{name} must be a non-empty string")
    return value.strip()


def _string_list(name: str, value: object) -> list[str]:
    if not isinstance(value, list):
        raise ScientificFramingContractError(f"{name} must be an array")
    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ScientificFramingContractError(
                f"{name}[{index}] must be a non-empty string"
            )
        normalized.append(item.strip())
    return normalized
