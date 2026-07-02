from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import os
import tempfile


_CONTRACT_SCHEMA = "missipy.source_candidate.external_projection_contract.v1"
_PAYLOAD_SCHEMA = "missipy.source_candidate.github_projection_payload.v1"


@dataclass(frozen=True)
class SourceCandidateGithubProjectionPayloadPolicy:
    """Policy for building a local GitHub projection payload.

    This module only creates a dry-run payload. It does not contact GitHub and
    it does not mutate any remote state.
    """

    repository: str
    project_key: str | None = None
    max_operations: int = 50


@dataclass(frozen=True)
class SourceCandidateGithubProjectionOperation:
    action: str
    candidate_id: str
    title: str
    body: str
    labels: tuple[str, ...]
    safety_flags: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "candidate_id": self.candidate_id,
            "title": self.title,
            "body": self.body,
            "labels": list(self.labels),
            "safety_flags": list(self.safety_flags),
        }


@dataclass(frozen=True)
class SourceCandidateGithubProjectionPayload:
    repository: str
    project_key: str | None
    dry_run: bool
    remote_mutation: bool
    projection_allowed: bool
    blocked_reasons: tuple[str, ...]
    operation_count: int
    operations: tuple[SourceCandidateGithubProjectionOperation, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _PAYLOAD_SCHEMA,
            "repository": self.repository,
            "project_key": self.project_key,
            "dry_run": self.dry_run,
            "remote_mutation": self.remote_mutation,
            "projection_allowed": self.projection_allowed,
            "blocked_reasons": list(self.blocked_reasons),
            "operation_count": self.operation_count,
            "operations": [operation.to_json_dict() for operation in self.operations],
        }


def build_source_candidate_github_projection_payload(
    contract_payload: Mapping[str, Any],
    policy: SourceCandidateGithubProjectionPayloadPolicy,
) -> SourceCandidateGithubProjectionPayload:
    """Build a local GitHub dry-run payload from an external projection contract."""

    _validate_policy(policy)
    if contract_payload.get("schema") != _CONTRACT_SCHEMA:
        raise ValueError("external projection contract schema mismatch")

    projection_allowed = bool(contract_payload.get("projection_allowed"))
    blocked_reasons = tuple(_string(item) for item in _sequence(contract_payload.get("blocked_reasons")))

    operations: list[SourceCandidateGithubProjectionOperation] = []
    if projection_allowed:
        for item in _contract_items(contract_payload):
            operation = _operation_from_item(item)
            if operation.action != "no_op":
                operations.append(operation)
            if len(operations) >= policy.max_operations:
                break

    return SourceCandidateGithubProjectionPayload(
        repository=policy.repository,
        project_key=policy.project_key,
        dry_run=True,
        remote_mutation=False,
        projection_allowed=projection_allowed,
        blocked_reasons=blocked_reasons,
        operation_count=len(operations),
        operations=tuple(operations),
    )


def build_source_candidate_github_projection_payload_from_file(
    contract_path: Path,
    policy: SourceCandidateGithubProjectionPayloadPolicy,
) -> SourceCandidateGithubProjectionPayload:
    return build_source_candidate_github_projection_payload(
        _read_json_object(contract_path),
        policy,
    )


def write_source_candidate_github_projection_payload(
    path: Path,
    payload: SourceCandidateGithubProjectionPayload,
) -> Path:
    _atomic_write_json(path, payload.to_json_dict())
    return path


def read_source_candidate_github_projection_payload(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    if payload.get("schema") != _PAYLOAD_SCHEMA:
        raise ValueError("GitHub projection payload schema mismatch")
    return dict(payload)


def _operation_from_item(item: Mapping[str, Any]) -> SourceCandidateGithubProjectionOperation:
    candidate_id = _string(item.get("candidate_id"))
    title = _string(item.get("title"), default=candidate_id)
    recommended_action = _string(item.get("recommended_action"), default="review")
    safety_flags = tuple(_string(flag) for flag in _sequence(item.get("safety_flags")))
    labels = _github_labels(item)

    action = _github_action(recommended_action, safety_flags)
    return SourceCandidateGithubProjectionOperation(
        action=action,
        candidate_id=candidate_id,
        title=f"SourceCandidate: {title}",
        body=_operation_body(item),
        labels=labels,
        safety_flags=safety_flags,
    )


def _github_action(recommended_action: str, safety_flags: tuple[str, ...]) -> str:
    if "terminal" in safety_flags:
        return "no_op"
    if recommended_action in {"inspect", "review", "write-audit", "relaunch"}:
        return "create_issue"
    return "create_issue"


def _operation_body(item: Mapping[str, Any]) -> str:
    lines = [
        "SourceCandidate projection dry-run.",
        "",
        f"- candidate_id: {_string(item.get('candidate_id'))}",
        f"- status: {_string(item.get('status'), default='unknown')}",
        f"- recommended_action: {_string(item.get('recommended_action'), default='review')}",
        f"- audit_present: {bool(item.get('audit_present'))}",
    ]
    target_context_id = item.get("target_context_id")
    if isinstance(target_context_id, str) and target_context_id.strip():
        lines.append(f"- target_context_id: {target_context_id}")
    safety_flags = _sequence(item.get("safety_flags"))
    if safety_flags:
        lines.append("- safety_flags: " + ", ".join(_string(flag) for flag in safety_flags))
    lines.append("")
    lines.append("This is a dry-run payload. No remote mutation has been performed.")
    return "\n".join(lines)


def _github_labels(item: Mapping[str, Any]) -> tuple[str, ...]:
    labels = ["autodoc", "source-candidate", "dry-run"]
    for raw in _sequence(item.get("labels")):
        value = _string(raw)
        if value.startswith("status:"):
            labels.append(value.replace(":", "/"))
        elif value.startswith("decision:"):
            labels.append(value.replace(":", "/"))
    for flag in _sequence(item.get("safety_flags")):
        labels.append(f"safety/{_string(flag).replace('_', '-')}")
    return tuple(dict.fromkeys(labels))


def _validate_policy(policy: SourceCandidateGithubProjectionPayloadPolicy) -> None:
    if policy.max_operations <= 0:
        raise ValueError("max_operations must be greater than zero")
    if "/" not in policy.repository or policy.repository.count("/") != 1:
        raise ValueError("repository must use owner/name format")
    owner, name = policy.repository.split("/", 1)
    if not owner.strip() or not name.strip():
        raise ValueError("repository must use owner/name format")


def _contract_items(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    raw_items = payload.get("items")
    if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes, bytearray)):
        raise ValueError("external projection contract items must be a list")
    items: list[Mapping[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, Mapping):
            raise ValueError("external projection contract item must be an object")
        items.append(item)
    return tuple(items)


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _sequence(raw: object) -> tuple[object, ...]:
    if raw is None:
        return ()
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        return tuple(raw)
    raise ValueError("expected list")


def _string(raw: object, *, default: str | None = None) -> str:
    if isinstance(raw, str) and raw.strip():
        return raw
    if default is not None:
        return default
    raise ValueError("expected non-empty string")


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        tmp_name = handle.name
        handle.write(text)
    os.replace(tmp_name, path)
