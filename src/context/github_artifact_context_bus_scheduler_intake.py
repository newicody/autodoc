"""Context bus reader for GitHub artifact scheduler intake.

0178 closes the direct JSON shortcut by reading existing context.bus JSONL facts
before producing scheduler intake data.

Path:

    context.bus.jsonl
    -> ContextBusMessage.from_mapping(...)
    -> topic github.artifact_dataset.context
    -> payload_schema missipy.github_artifact.dataset_context.v1
    -> github artifact scheduler intake candidate/plan

Boundary:

- This module reads context.bus JSONL, not arbitrary direct JSON intake.
- This module reuses runtime.shm_runtime_schema.ContextBusMessage.
- This module reuses context.github_artifact_scheduler_intake builders.
- This module does not instantiate EventBus.
- This module does not modify Scheduler.run().
- This module does not call handle_scheduler_route_request.
- This module does not write to VisPy.
- This module does not call GitHub.
"""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Iterable, Mapping

from context.github_artifact_scheduler_intake import (
    GithubArtifactSchedulerIntakePlan,
    build_github_artifact_scheduler_intake_plan,
)
from runtime.shm_runtime_schema import ContextBusMessage


GITHUB_ARTIFACT_DATASET_CONTEXT_TOPIC = "github.artifact_dataset.context"
GITHUB_ARTIFACT_DATASET_CONTEXT_SCHEMA = "missipy.github_artifact.dataset_context.v1"


class ContextBusSchedulerIntakeReaderError(ValueError):
    """Raised when a context.bus message cannot safely become scheduler intake."""


def build_github_artifact_scheduler_intake_from_context_bus_message(
    message: ContextBusMessage | Mapping[str, Any],
    *,
    policy_decision_id: str | None = None,
    authorized: bool = False,
    priority: int = 50,
) -> GithubArtifactSchedulerIntakePlan:
    """Build a scheduler intake plan from an existing ContextBusMessage.

    The input must be a context.bus fact emitted through the existing runtime SHM
    schema. Direct JSON intake should use the lower-level 0177 builder only in
    tests or explicitly controlled tooling.
    """

    context_message = (
        message if isinstance(message, ContextBusMessage) else ContextBusMessage.from_mapping(message)
    )
    _validate_github_artifact_context_message(context_message)
    payload = context_message.payload
    if not isinstance(payload, Mapping):
        raise ContextBusSchedulerIntakeReaderError("context payload must be a mapping")

    candidate_raw = {
        "observation_ref": context_message.context_id,
        "repository": _payload_text(payload, "repository"),
        "run_id": _payload_text(payload, "run_id"),
        "artifact_id": _payload_text(payload, "artifact_id"),
        "dataset_root_ref": _payload_text(payload, "dataset_root_ref"),
        "status": _payload_text(payload, "status"),
        "priority": priority,
        "requested_at": context_message.occurred_at,
    }
    return build_github_artifact_scheduler_intake_plan(
        candidate_raw,
        policy_decision_id=policy_decision_id,
        authorized=authorized,
    )


def read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl(
    path: Path | str,
    *,
    policy_decision_id: str | None = None,
    authorized: bool = False,
    priority: int = 50,
    include_non_matching: bool = False,
) -> list[GithubArtifactSchedulerIntakePlan]:
    """Read context.bus JSONL and build plans from matching GitHub artifact facts."""

    plans: list[GithubArtifactSchedulerIntakePlan] = []
    for message in iter_context_bus_messages(path):
        if _is_github_artifact_context_message(message):
            plans.append(
                build_github_artifact_scheduler_intake_from_context_bus_message(
                    message,
                    policy_decision_id=policy_decision_id,
                    authorized=authorized,
                    priority=priority,
                )
            )
        elif include_non_matching:
            raise ContextBusSchedulerIntakeReaderError(
                f"non matching context bus message: topic={message.topic!r} payload_schema={message.payload_schema!r}"
            )
    return plans


def iter_context_bus_messages(path: Path | str) -> Iterable[ContextBusMessage]:
    """Yield ContextBusMessage objects from a JSONL context.bus file."""

    bus_path = Path(path)
    with bus_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ContextBusSchedulerIntakeReaderError(
                    f"invalid JSONL at {bus_path}:{line_number}"
                ) from exc
            if not isinstance(item, Mapping):
                raise ContextBusSchedulerIntakeReaderError(
                    f"context bus line must be an object at {bus_path}:{line_number}"
                )
            yield ContextBusMessage.from_mapping(item)


def _validate_github_artifact_context_message(message: ContextBusMessage) -> None:
    if not _is_github_artifact_context_message(message):
        raise ContextBusSchedulerIntakeReaderError(
            "context bus message must use topic github.artifact_dataset.context and payload_schema "
            "missipy.github_artifact.dataset_context.v1"
        )


def _is_github_artifact_context_message(message: ContextBusMessage) -> bool:
    return (
        message.topic == GITHUB_ARTIFACT_DATASET_CONTEXT_TOPIC
        and message.payload_schema == GITHUB_ARTIFACT_DATASET_CONTEXT_SCHEMA
    )


def _payload_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContextBusSchedulerIntakeReaderError(f"payload field {field} must be a non-empty string")
    return value.strip()
