from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import os
import tempfile


_HANDOFF_SCHEMA = "missipy.source_candidate.phase7_handoff_contract.v1"
_CLOSURE_SCHEMA = "missipy.source_candidate.phase7_closure_report.v1"


DEFAULT_PHASE7_HANDOFF_NEXT_PHASE_OPTIONS: tuple[str, ...] = (
    "github_read_only_import_prototype",
    "local_document_context_ingestion",
    "retrieval_evaluation_set",
    "operator_feedback_loop",
)


@dataclass(frozen=True)
class SourceCandidatePhase7HandoffContract:
    phase: str
    status: str
    closure_report_path: Path | None
    local_source_of_truth: bool
    external_service_calls_allowed: bool
    remote_mutation_allowed: bool
    scheduler_execution_allowed: bool
    generated_svg_policy_required: bool
    operator_confirmation_required: bool
    next_phase: str
    next_phase_options: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _HANDOFF_SCHEMA,
            "phase": self.phase,
            "status": self.status,
            "closure_report_path": str(self.closure_report_path) if self.closure_report_path is not None else None,
            "local_source_of_truth": self.local_source_of_truth,
            "external_service_calls_allowed": self.external_service_calls_allowed,
            "remote_mutation_allowed": self.remote_mutation_allowed,
            "scheduler_execution_allowed": self.scheduler_execution_allowed,
            "generated_svg_policy_required": self.generated_svg_policy_required,
            "operator_confirmation_required": self.operator_confirmation_required,
            "next_phase": self.next_phase,
            "next_phase_options": list(self.next_phase_options),
        }


def build_source_candidate_phase7_handoff_contract(
    *,
    closure_report_path: Path | None = None,
    closure_report_payload: Mapping[str, Any] | None = None,
    next_phase: str = "8",
    next_phase_options: Sequence[str] = DEFAULT_PHASE7_HANDOFF_NEXT_PHASE_OPTIONS,
) -> SourceCandidatePhase7HandoffContract:
    """Build the frozen handoff contract from Part 7 to Part 8.

    The contract deliberately keeps every external and autonomous execution
    boundary closed. It records what Part 8 may open, but it does not grant that
    capability.
    """

    if closure_report_payload is not None:
        _validate_closure_report_payload(closure_report_payload)

    return SourceCandidatePhase7HandoffContract(
        phase="7",
        status="frozen",
        closure_report_path=closure_report_path,
        local_source_of_truth=True,
        external_service_calls_allowed=False,
        remote_mutation_allowed=False,
        scheduler_execution_allowed=False,
        generated_svg_policy_required=True,
        operator_confirmation_required=True,
        next_phase=next_phase,
        next_phase_options=tuple(next_phase_options),
    )


def build_source_candidate_phase7_handoff_contract_from_closure_report(
    closure_report_path: Path,
    *,
    next_phase: str = "8",
    next_phase_options: Sequence[str] = DEFAULT_PHASE7_HANDOFF_NEXT_PHASE_OPTIONS,
) -> SourceCandidatePhase7HandoffContract:
    payload = _read_json_object(closure_report_path)
    return build_source_candidate_phase7_handoff_contract(
        closure_report_path=closure_report_path,
        closure_report_payload=payload,
        next_phase=next_phase,
        next_phase_options=next_phase_options,
    )


def write_source_candidate_phase7_handoff_contract(
    path: Path,
    contract: SourceCandidatePhase7HandoffContract,
) -> Path:
    _atomic_write_json(path, contract.to_json_dict())
    return path


def read_source_candidate_phase7_handoff_contract(path: Path) -> dict[str, object]:
    payload = _read_json_object(path)
    if payload.get("schema") != _HANDOFF_SCHEMA:
        raise ValueError("phase 7 handoff contract schema mismatch")
    return dict(payload)


def render_source_candidate_phase7_handoff_contract(
    contract: SourceCandidatePhase7HandoffContract,
) -> str:
    lines = [
        "source candidate phase 7 handoff contract",
        f"phase: {contract.phase}",
        f"status: {contract.status}",
        f"closure_report_path: {contract.closure_report_path or '<none>'}",
        f"local_source_of_truth: {contract.local_source_of_truth}",
        f"external_service_calls_allowed: {contract.external_service_calls_allowed}",
        f"remote_mutation_allowed: {contract.remote_mutation_allowed}",
        f"scheduler_execution_allowed: {contract.scheduler_execution_allowed}",
        f"generated_svg_policy_required: {contract.generated_svg_policy_required}",
        f"operator_confirmation_required: {contract.operator_confirmation_required}",
        f"next_phase: {contract.next_phase}",
        "next_phase_options:",
    ]
    lines.extend(f"- {option}" for option in contract.next_phase_options)
    return "\n".join(lines)


def _validate_closure_report_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("schema") != _CLOSURE_SCHEMA:
        raise ValueError("phase 7 closure report schema mismatch")
    if payload.get("phase") != "7":
        raise ValueError("phase 7 closure report phase mismatch")
    if payload.get("local_only") is not True:
        raise ValueError("phase 7 closure report must be local-only")
    if payload.get("remote_mutation_enabled") is not False:
        raise ValueError("phase 7 closure report must keep remote mutation disabled")
    if payload.get("scheduler_modified") is not False:
        raise ValueError("phase 7 closure report must keep scheduler unmodified")
    if payload.get("network_enabled") is not False:
        raise ValueError("phase 7 closure report must keep network disabled")


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


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
