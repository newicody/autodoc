from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import os
import tempfile


_CONTRACT_SCHEMA = "missipy.source_candidate.external_projection_contract.v1"


@dataclass(frozen=True)
class SourceCandidateExternalProjectionContractPolicy:
    """Policy for building a generic external projection contract.

    This contract is target-neutral. It describes what may be projected outside
    the local SourceCandidate chain without binding the local core to GitHub or
    any other external surface.
    """

    target_kind: str = "generic_project_surface"
    max_items: int = 50
    require_gate_pass: bool = True


@dataclass(frozen=True)
class SourceCandidateExternalProjectionItem:
    candidate_id: str
    title: str
    status: str
    recommended_action: str
    audit_present: bool
    labels: tuple[str, ...]
    decision_action: str | None
    target_context_id: str | None
    safety_flags: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "title": self.title,
            "status": self.status,
            "recommended_action": self.recommended_action,
            "audit_present": self.audit_present,
            "labels": list(self.labels),
            "decision_action": self.decision_action,
            "target_context_id": self.target_context_id,
            "safety_flags": list(self.safety_flags),
        }


@dataclass(frozen=True)
class SourceCandidateExternalProjectionContract:
    target_kind: str
    source_handoff_path: Path
    gate_passed: bool
    projection_allowed: bool
    blocked_reasons: tuple[str, ...]
    item_count: int
    items: tuple[SourceCandidateExternalProjectionItem, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _CONTRACT_SCHEMA,
            "target_kind": self.target_kind,
            "source_handoff_path": str(self.source_handoff_path),
            "gate_passed": self.gate_passed,
            "projection_allowed": self.projection_allowed,
            "blocked_reasons": list(self.blocked_reasons),
            "item_count": self.item_count,
            "items": [item.to_json_dict() for item in self.items],
        }


def build_source_candidate_external_projection_contract(
    handoff_path: Path,
    policy: SourceCandidateExternalProjectionContractPolicy | None = None,
) -> SourceCandidateExternalProjectionContract:
    """Build a target-neutral external projection contract from a handoff dry-run."""

    active_policy = policy or SourceCandidateExternalProjectionContractPolicy()
    if active_policy.max_items <= 0:
        raise ValueError("max_items must be greater than zero")
    if not active_policy.target_kind.strip():
        raise ValueError("target_kind must not be empty")

    manifest = _read_json_object(handoff_path / "handoff_manifest.json")
    preview = _read_json_object(handoff_path / "projection_preview.json")
    gate_report = _read_json_object(handoff_path / "projection_gate_report.json")

    gate_result = _mapping(gate_report.get("gate_result"))
    gate_passed = bool(manifest.get("passed")) and bool(gate_result.get("passed"))

    blocked_reasons = _blocked_reasons(
        gate_passed=gate_passed,
        require_gate_pass=active_policy.require_gate_pass,
    )

    raw_items = _items(preview)
    items = tuple(_build_item(item) for item in raw_items[: active_policy.max_items])

    return SourceCandidateExternalProjectionContract(
        target_kind=active_policy.target_kind,
        source_handoff_path=handoff_path,
        gate_passed=gate_passed,
        projection_allowed=len(blocked_reasons) == 0,
        blocked_reasons=tuple(blocked_reasons),
        item_count=len(items),
        items=items,
    )


def write_source_candidate_external_projection_contract(
    path: Path,
    contract: SourceCandidateExternalProjectionContract,
) -> Path:
    """Write the external projection contract JSON atomically."""

    _atomic_write_json(path, contract.to_json_dict())
    return path


def read_source_candidate_external_projection_contract(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    if payload.get("schema") != _CONTRACT_SCHEMA:
        raise ValueError("external projection contract schema mismatch")
    return dict(payload)


def _build_item(raw: Mapping[str, Any]) -> SourceCandidateExternalProjectionItem:
    audit_present = bool(raw.get("audit_present"))
    recommended_action = _string(raw.get("recommended_action"), default="review")
    status = _string(raw.get("status"), default="unknown")
    decision_action = _optional_string(raw.get("decision_action"))
    labels = tuple(_string(item) for item in _string_sequence(raw.get("labels")))
    safety_flags = tuple(
        flag
        for flag in (
            "audit_missing" if not audit_present else "",
            "terminal" if status in {"archived", "merged", "promoted", "rejected"} else "",
            "relaunch_requested" if recommended_action == "relaunch" else "",
        )
        if flag
    )

    return SourceCandidateExternalProjectionItem(
        candidate_id=_string(raw.get("candidate_id")),
        title=_string(raw.get("title"), default=_string(raw.get("candidate_id"))),
        status=status,
        recommended_action=recommended_action,
        audit_present=audit_present,
        labels=labels,
        decision_action=decision_action,
        target_context_id=_optional_string(raw.get("target_context_id")),
        safety_flags=safety_flags,
    )


def _blocked_reasons(*, gate_passed: bool, require_gate_pass: bool) -> list[str]:
    if require_gate_pass and not gate_passed:
        return ["gate_not_passed"]
    return []


def _items(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    raw_items = payload.get("items")
    if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes, bytearray)):
        raise ValueError("projection preview items must be a list")
    items: list[Mapping[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, Mapping):
            raise ValueError("projection preview item must be an object")
        items.append(item)
    return tuple(items)


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _mapping(raw: object) -> Mapping[str, Any]:
    return raw if isinstance(raw, Mapping) else {}


def _string(raw: object, *, default: str | None = None) -> str:
    if isinstance(raw, str) and raw.strip():
        return raw
    if default is not None:
        return default
    raise ValueError("expected non-empty string")


def _optional_string(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw
    return None


def _string_sequence(raw: object) -> tuple[object, ...]:
    if raw is None:
        return ()
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        return tuple(raw)
    raise ValueError("expected a list of strings")


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
