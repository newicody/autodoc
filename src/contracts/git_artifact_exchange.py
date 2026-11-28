"""Git-commit artifact transport contract for the one-shot Copilot framing exchange.

The repository commit is the asynchronous transport boundary: Copilot writes
its artifacts, the server writes its response, and each side reads the pushed
artifact from Git. This module is pure and performs no Git/network operation.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import re
from typing import Any

SCHEMA = "missipy.github.git_artifact_exchange_envelope.v1"
CHAIN_SCHEMA = "missipy.github.git_artifact_exchange_chain.v1"
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ROLE_DETAILS = {
    "copilot_initial": ("copilot-initial.json", "copilot"),
    "server_response": ("server-response.json", "server"),
    "copilot_refined": ("copilot-refined.json", "copilot"),
}
_ROLE_ORDER = ("copilot_initial", "server_response", "copilot_refined")


class GitArtifactExchangeError(ValueError):
    """Raised when a Git-backed exchange artifact is invalid or conflicting."""


@dataclass(frozen=True, slots=True)
class GitExchangeArtifact:
    repository: str
    issue_number: int
    cycle_ordinal: int
    role: str
    producer: str
    created_at: str
    payload: Mapping[str, Any]
    payload_digest: str
    artifact_path: str
    artifact_ref: str
    predecessor_ref: str = ""
    predecessor_digest: str = ""

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "repository": self.repository,
            "issue_number": self.issue_number,
            "cycle_ordinal": self.cycle_ordinal,
            "role": self.role,
            "producer": self.producer,
            "created_at": self.created_at,
            "payload": dict(self.payload),
            "payload_digest": self.payload_digest,
            "artifact_path": self.artifact_path,
            "artifact_ref": self.artifact_ref,
            "predecessor_ref": self.predecessor_ref,
            "predecessor_digest": self.predecessor_digest,
            "transport": "git_commit_push",
            "append_only": True,
            "github_actions_artifact_is_transport": False,
            "direct_copilot_server_call": False,
            "execution_authorized": False,
        }


def canonical_payload_digest(payload: Mapping[str, Any]) -> str:
    try:
        encoded = json.dumps(
            dict(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise GitArtifactExchangeError("payload must be canonical JSON data") from exc
    return hashlib.sha256(encoded).hexdigest()


def artifact_path(issue_number: int, cycle_ordinal: int, role: str) -> str:
    _validate_positive_integer("issue_number", issue_number)
    _validate_positive_integer("cycle_ordinal", cycle_ordinal)
    if role not in _ROLE_DETAILS:
        raise GitArtifactExchangeError(f"unsupported exchange role: {role}")
    filename, _ = _ROLE_DETAILS[role]
    return (
        f"autodoc/exchanges/issues/{issue_number}/cycles/"
        f"{cycle_ordinal}/{filename}"
    )


def build_git_exchange_artifact(
    *,
    repository: str,
    issue_number: int,
    cycle_ordinal: int,
    role: str,
    payload: Mapping[str, Any],
    created_at: str,
    predecessor_ref: str = "",
    predecessor_digest: str = "",
) -> GitExchangeArtifact:
    repository = _required_repository(repository)
    _validate_positive_integer("issue_number", issue_number)
    _validate_positive_integer("cycle_ordinal", cycle_ordinal)
    if role not in _ROLE_DETAILS:
        raise GitArtifactExchangeError(f"unsupported exchange role: {role}")
    if not isinstance(payload, Mapping):
        raise GitArtifactExchangeError("payload must be an object")
    created_at = _required_text("created_at", created_at)
    _validate_timestamp(created_at)
    _, producer = _ROLE_DETAILS[role]
    path = artifact_path(issue_number, cycle_ordinal, role)
    expected_predecessor = _expected_predecessor(
        repository, issue_number, cycle_ordinal, role
    )
    if expected_predecessor is None:
        if predecessor_ref or predecessor_digest:
            raise GitArtifactExchangeError(
                "initial Copilot artifact must not have a predecessor"
            )
    else:
        expected_ref, expected_role = expected_predecessor
        if predecessor_ref != expected_ref:
            raise GitArtifactExchangeError("predecessor_ref mismatch")
        if not _SHA256_RE.fullmatch(predecessor_digest):
            raise GitArtifactExchangeError("predecessor_digest must be sha256")
    digest = canonical_payload_digest(payload)
    ref = f"git-artifact:{repository}:{path}"
    return GitExchangeArtifact(
        repository=repository,
        issue_number=issue_number,
        cycle_ordinal=cycle_ordinal,
        role=role,
        producer=producer,
        created_at=created_at,
        payload=dict(payload),
        payload_digest=digest,
        artifact_path=path,
        artifact_ref=ref,
        predecessor_ref=predecessor_ref,
        predecessor_digest=predecessor_digest,
    )


def validate_git_exchange_artifact(value: Mapping[str, Any]) -> dict[str, Any]:
    if value.get("schema") != SCHEMA:
        raise GitArtifactExchangeError("unexpected Git exchange schema")
    repository = _required_repository(value.get("repository"))
    issue_number = _positive_integer("issue_number", value.get("issue_number"))
    cycle = _positive_integer("cycle_ordinal", value.get("cycle_ordinal"))
    role = _required_text("role", value.get("role"))
    if role not in _ROLE_DETAILS:
        raise GitArtifactExchangeError("unsupported exchange role")
    _, expected_producer = _ROLE_DETAILS[role]
    if value.get("producer") != expected_producer:
        raise GitArtifactExchangeError("producer does not match artifact role")
    path = artifact_path(issue_number, cycle, role)
    if value.get("artifact_path") != path:
        raise GitArtifactExchangeError("artifact_path is not canonical")
    expected_ref = f"git-artifact:{repository}:{path}"
    if value.get("artifact_ref") != expected_ref:
        raise GitArtifactExchangeError("artifact_ref mismatch")
    _validate_timestamp(_required_text("created_at", value.get("created_at")))
    payload = value.get("payload")
    if not isinstance(payload, Mapping):
        raise GitArtifactExchangeError("payload must be an object")
    digest = _required_text("payload_digest", value.get("payload_digest"))
    if not _SHA256_RE.fullmatch(digest):
        raise GitArtifactExchangeError("payload_digest must be sha256")
    if canonical_payload_digest(payload) != digest:
        raise GitArtifactExchangeError("payload_digest does not match payload")
    predecessor_ref = str(value.get("predecessor_ref", "")).strip()
    predecessor_digest = str(value.get("predecessor_digest", "")).strip()
    expected_predecessor = _expected_predecessor(
        repository, issue_number, cycle, role
    )
    if expected_predecessor is None:
        if predecessor_ref or predecessor_digest:
            raise GitArtifactExchangeError("initial artifact cannot have predecessor")
    else:
        expected_ref, _ = expected_predecessor
        if predecessor_ref != expected_ref:
            raise GitArtifactExchangeError("predecessor_ref mismatch")
        if not _SHA256_RE.fullmatch(predecessor_digest):
            raise GitArtifactExchangeError("predecessor_digest must be sha256")
    if value.get("transport") != "git_commit_push":
        raise GitArtifactExchangeError("exchange transport must be git_commit_push")
    for flag in (
        "append_only",
        "github_actions_artifact_is_transport",
        "direct_copilot_server_call",
        "execution_authorized",
    ):
        expected = {
            "append_only": True,
            "github_actions_artifact_is_transport": False,
            "direct_copilot_server_call": False,
            "execution_authorized": False,
        }[flag]
        if value.get(flag) is not expected:
            raise GitArtifactExchangeError(f"{flag} boundary violation")
    return dict(value)


def validate_git_exchange_chain(
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if len(artifacts) != len(_ROLE_ORDER):
        raise GitArtifactExchangeError("initial exchange must contain exactly three artifacts")
    validated = tuple(validate_git_exchange_artifact(item) for item in artifacts)
    first, response, refined = validated
    identities = {
        (item["repository"], item["issue_number"], item["cycle_ordinal"])
        for item in validated
    }
    if len(identities) != 1:
        raise GitArtifactExchangeError("exchange artifacts must share one research cycle")
    if tuple(item["role"] for item in validated) != _ROLE_ORDER:
        raise GitArtifactExchangeError("exchange artifact order is invalid")
    if response["predecessor_digest"] != first["payload_digest"]:
        raise GitArtifactExchangeError("server response does not bind initial artifact digest")
    if refined["predecessor_digest"] != response["payload_digest"]:
        raise GitArtifactExchangeError("refined artifact does not bind server response digest")
    return {
        "schema": CHAIN_SCHEMA,
        "valid": True,
        "repository": first["repository"],
        "issue_number": first["issue_number"],
        "cycle_ordinal": first["cycle_ordinal"],
        "artifact_refs": [item["artifact_ref"] for item in validated],
        "artifact_digests": [item["payload_digest"] for item in validated],
        "transport": "git_commit_push",
        "exchange_count": 1,
        "recursive_clarification_allowed": False,
        "execution_authorized": False,
    }


def classify_existing_path(existing: Mapping[str, Any] | None, candidate: Mapping[str, Any]) -> str:
    """Return create/replay/collision without ever authorizing an overwrite."""
    validate_git_exchange_artifact(candidate)
    if existing is None:
        return "create"
    validate_git_exchange_artifact(existing)
    if existing.get("artifact_path") != candidate.get("artifact_path"):
        raise GitArtifactExchangeError("existing artifact path mismatch")
    if existing.get("payload_digest") == candidate.get("payload_digest"):
        return "replay"
    return "collision"


def _expected_predecessor(
    repository: str, issue_number: int, cycle: int, role: str
) -> tuple[str, str] | None:
    if role == "copilot_initial":
        return None
    predecessor_role = (
        "copilot_initial" if role == "server_response" else "server_response"
    )
    path = artifact_path(issue_number, cycle, predecessor_role)
    return f"git-artifact:{repository}:{path}", predecessor_role


def _required_repository(value: object) -> str:
    text = _required_text("repository", value)
    if not _REPOSITORY_RE.fullmatch(text):
        raise GitArtifactExchangeError("repository must use owner/name")
    return text


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GitArtifactExchangeError(f"{name} must be a non-empty string")
    return value.strip()


def _positive_integer(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise GitArtifactExchangeError(f"{name} must be a positive integer")
    return value


def _validate_positive_integer(name: str, value: object) -> None:
    _positive_integer(name, value)


def _validate_timestamp(value: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GitArtifactExchangeError("created_at must be an ISO-8601 timestamp") from exc
