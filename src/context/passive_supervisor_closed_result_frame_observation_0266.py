"""PassiveSupervisor observation for closed ResultFrame EventBus facts.

0266 consumes the 0265 EventBus observation report and produces a passive
supervisor read model.  It does not subscribe to a live bus, does not publish
events, does not issue Requests, and does not execute runtime components.

Boundary:
- PassiveSupervisor observes only.
- EventBus facts remain facts, not commands.
- 0266 does not execute SQL, OpenVINO, or Qdrant.
- Scheduler.run is not modified.
- No RuntimeManager is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


PASSIVE_SUPERVISOR_SCHEMA = "missipy.passive_supervisor_closed_result_frame_observation.v1"


@dataclass(frozen=True)
class PassiveSupervisorClosedFrameFinding:
    """Passive finding extracted from observation-only facts."""

    finding_ref: str
    severity: str
    finding_kind: str
    message: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    passive_only: bool = True
    command: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "finding_ref": self.finding_ref,
            "severity": self.severity,
            "finding_kind": self.finding_kind,
            "message": self.message,
            "payload": dict(self.payload),
            "passive_only": self.passive_only,
            "command": self.command,
        }


@dataclass(frozen=True)
class PassiveSupervisorClosedFrameObservationReport:
    """PassiveSupervisor read model over closed frame observation facts."""

    valid: bool
    issues: tuple[str, ...]
    source_observation_ref: str
    fact_count: int = 0
    accepted_fact_count: int = 0
    rejected_fact_count: int = 0
    command_like_fact_count: int = 0
    runtime_violation_count: int = 0
    findings: tuple[PassiveSupervisorClosedFrameFinding, ...] = field(default_factory=tuple)
    passive_supervisor_observation_only: bool = True
    eventbus_observation_only: bool = True
    events_are_facts_not_commands: bool = True
    executes_runtime: bool = False
    starts_postgresql: bool = False
    starts_openvino: bool = False
    starts_qdrant: bool = False
    publishes_events: bool = False
    modifies_scheduler_run: bool = False
    creates_runtime_manager: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": PASSIVE_SUPERVISOR_SCHEMA,
            "passive_supervisor_closed_result_frame_observation": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "source_observation_ref": self.source_observation_ref,
            "fact_count": self.fact_count,
            "accepted_fact_count": self.accepted_fact_count,
            "rejected_fact_count": self.rejected_fact_count,
            "command_like_fact_count": self.command_like_fact_count,
            "runtime_violation_count": self.runtime_violation_count,
            "findings": [finding.to_mapping() for finding in self.findings],
            "passive_supervisor_observation_only": self.passive_supervisor_observation_only,
            "eventbus_observation_only": self.eventbus_observation_only,
            "events_are_facts_not_commands": self.events_are_facts_not_commands,
            "executes_runtime": self.executes_runtime,
            "starts_postgresql": self.starts_postgresql,
            "starts_openvino": self.starts_openvino,
            "starts_qdrant": self.starts_qdrant,
            "publishes_events": self.publishes_events,
            "modifies_scheduler_run": self.modifies_scheduler_run,
            "creates_runtime_manager": self.creates_runtime_manager,
        }


def _facts_from_observation_report(report: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    facts = report.get("facts", [])
    if not isinstance(facts, list):
        return ()
    return tuple(fact for fact in facts if isinstance(fact, Mapping))


def _fact_payload(fact: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = fact.get("payload", {})
    if isinstance(payload, Mapping):
        return payload
    return {}


def validate_eventbus_observation_report_for_passive_supervisor(
    report: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate that 0265 output is safe for PassiveSupervisor observation."""

    issues: list[str] = []
    if report.get("valid") is not True:
        issues.append("0265 observation report must be valid")
    if report.get("eventbus_observation_only") is not True:
        issues.append("EventBus report must be observation-only")
    if report.get("events_are_facts_not_commands") is not True:
        issues.append("EventBus report must declare events as facts, not commands")
    if report.get("executes_runtime") is not False:
        issues.append("PassiveSupervisor input must be non-runtime")
    if report.get("starts_postgresql") is not False:
        issues.append("PassiveSupervisor input must not start PostgreSQL")
    if report.get("starts_openvino") is not False:
        issues.append("PassiveSupervisor input must not start OpenVINO")
    if report.get("starts_qdrant") is not False:
        issues.append("PassiveSupervisor input must not start Qdrant")
    if report.get("modifies_scheduler_run") is not False:
        issues.append("PassiveSupervisor input must not modify Scheduler.run")
    if not _facts_from_observation_report(report):
        issues.append("PassiveSupervisor input must contain observation facts")
    return tuple(issues)


def _finding_ref(source_ref: str, suffix: str) -> str:
    normalized = source_ref.strip() or "closed-result-frame-eventbus-observation"
    return f"passive-supervisor-finding:0266:{normalized}:{suffix}"


def build_passive_supervisor_findings_from_facts(
    facts: Sequence[Mapping[str, Any]],
    *,
    source_observation_ref: str,
) -> tuple[PassiveSupervisorClosedFrameFinding, ...]:
    """Build passive findings from 0265 fact mappings."""

    findings: list[PassiveSupervisorClosedFrameFinding] = []
    for index, fact in enumerate(facts):
        fact_ref = str(fact.get("fact_ref") or f"fact:{index}")
        fact_kind = str(fact.get("fact_kind") or "unknown")
        payload = _fact_payload(fact)

        if fact.get("command") is True:
            findings.append(
                PassiveSupervisorClosedFrameFinding(
                    finding_ref=_finding_ref(source_observation_ref, f"command-like:{index}"),
                    severity="error",
                    finding_kind="command_like_fact",
                    message="Observation fact is marked as command-like",
                    payload={"fact_ref": fact_ref, "fact_kind": fact_kind},
                )
            )
            continue

        if fact.get("observation_only") is not True:
            findings.append(
                PassiveSupervisorClosedFrameFinding(
                    finding_ref=_finding_ref(source_observation_ref, f"not-observation-only:{index}"),
                    severity="error",
                    finding_kind="not_observation_only",
                    message="Observation fact does not declare observation_only=True",
                    payload={"fact_ref": fact_ref, "fact_kind": fact_kind},
                )
            )
            continue

        findings.append(
            PassiveSupervisorClosedFrameFinding(
                finding_ref=_finding_ref(source_observation_ref, f"accepted:{index}"),
                severity="info",
                finding_kind="observation_fact_accepted",
                message="Observation fact accepted by PassiveSupervisor read model",
                payload={
                    "fact_ref": fact_ref,
                    "fact_kind": fact_kind,
                    "sql_ref": payload.get("sql_ref", ""),
                    "frame_ref": payload.get("frame_ref", ""),
                },
            )
        )
    return tuple(findings)


def build_passive_supervisor_closed_frame_observation_report(
    observation_report: Mapping[str, Any],
    *,
    source_observation_ref: str,
) -> PassiveSupervisorClosedFrameObservationReport:
    """Build the PassiveSupervisor read model without executing anything."""

    issues = list(validate_eventbus_observation_report_for_passive_supervisor(observation_report))
    facts = _facts_from_observation_report(observation_report)
    findings: tuple[PassiveSupervisorClosedFrameFinding, ...] = ()

    if not issues:
        findings = build_passive_supervisor_findings_from_facts(
            facts,
            source_observation_ref=source_observation_ref,
        )

    command_like_count = sum(1 for fact in facts if fact.get("command") is True)
    runtime_violation_count = sum(
        1
        for key in ("executes_runtime", "starts_postgresql", "starts_openvino", "starts_qdrant")
        if observation_report.get(key) is True
    )
    rejected_count = sum(1 for finding in findings if finding.severity == "error")
    accepted_count = sum(1 for finding in findings if finding.finding_kind == "observation_fact_accepted")

    return PassiveSupervisorClosedFrameObservationReport(
        valid=not issues and rejected_count == 0 and runtime_violation_count == 0,
        issues=tuple(issues),
        source_observation_ref=source_observation_ref,
        fact_count=len(facts),
        accepted_fact_count=accepted_count,
        rejected_fact_count=rejected_count,
        command_like_fact_count=command_like_count,
        runtime_violation_count=runtime_violation_count,
        findings=findings,
    )


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_report(output: Path, payload: Mapping[str, Any]) -> None:
    """Write a JSON report."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
