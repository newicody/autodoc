"""Prepare and dispatch the second love-specialist visit through the Scheduler.

This unit consumes the successful r16-r10 first-visit result, rebuilds its exact
typed LaboratoryVisitResult, delegates continuation construction to the
existing r11 collaboration contract, registers the digest-backed first analysis
and second task in the existing append-only runtime resolver, then submits a
second and distinct LABORATORY_VISIT_REQUEST through the existing Scheduler.

It does not call either specialist directly, create or start a Scheduler,
replace the laboratory handler, synthesize the two analyses, persist SQL/Qdrant
data, or mutate GitHub.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
from typing import Any

from context.github_research_love_first_visit_dispatch_0287 import (
    GitHubResearchLoveFirstVisitDispatchResult,
    GitHubResearchLoveRuntimeResolver,
)
from context.laboratory_framework_contract_0273 import (
    LABORATORY_VISIT_RESULT_SCHEMA,
    LaboratoryVisitResult,
)
from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
)
from context.native_love_laboratory_collaboration_scheduler_binding_0287 import (
    NativeLoveCollaborativeVisitRequestHandler,
    submit_native_love_collaboration_visit,
)
from context.native_love_laboratory_second_specialist_0287 import (
    NativeLoveCollaborationPreparation,
    prepare_second_specialist_collaboration,
)
from contracts.event import EventType

SCHEMA = "missipy.github.research_love_second_visit_dispatch.v1"


class GitHubResearchLoveSecondVisitDispatchError(RuntimeError):
    """Raised when the second specialist chain is incoherent."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveSecondVisitDispatchCommand:
    """One bounded second-visit request against an injected live runtime."""

    runtime_ports: ImportedActionsRuntimePorts
    first_dispatch: GitHubResearchLoveFirstVisitDispatchResult
    priority: int = 100
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.first_dispatch,
            GitHubResearchLoveFirstVisitDispatchResult,
        ):
            raise TypeError(
                "first_dispatch must be GitHubResearchLoveFirstVisitDispatchResult"
            )
        if (
            isinstance(self.priority, bool)
            or not isinstance(self.priority, int)
            or self.priority < -1_000
            or self.priority > 1_000_000
        ):
            raise ValueError("priority is outside the Scheduler policy range")
        if (
            self.timeout_seconds is not None
            and (
                isinstance(self.timeout_seconds, bool)
                or self.timeout_seconds <= 0
            )
        ):
            raise ValueError("timeout_seconds must be > 0 when provided")


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveSecondVisitDispatchResult:
    """Proof that the second analysis executed through a distinct Scheduler visit."""

    valid: bool
    status: str
    issues: tuple[str, ...]
    work_package_ref: str = ""
    first_visit_ref: str = ""
    second_visit_ref: str = ""
    preparation: Mapping[str, Any] = field(default_factory=dict)
    scheduler_receipt: Mapping[str, Any] = field(default_factory=dict)

    def to_mapping(self) -> dict[str, Any]:
        execution = self.scheduler_receipt.get("execution")
        execution = execution if isinstance(execution, Mapping) else {}
        result = execution.get("result")
        result = result if isinstance(result, Mapping) else {}
        return {
            "schema": SCHEMA,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
            "work_package_ref": self.work_package_ref,
            "first_visit_ref": self.first_visit_ref,
            "second_visit_ref": self.second_visit_ref,
            "preparation": dict(self.preparation),
            "scheduler_receipt": dict(self.scheduler_receipt),
            "second_analysis_result": dict(result),
            "first_analysis_artifact_registered": self.valid,
            "second_task_registered": self.valid,
            "existing_scheduler_reused": True,
            "existing_dispatcher_reused": True,
            "existing_laboratory_handler_reused": True,
            "existing_collaboration_preparation_reused": True,
            "scheduler_created": False,
            "scheduler_started": False,
            "parallel_dispatcher_created": False,
            "parallel_eventbus_created": False,
            "direct_specialist_invocation": False,
            "first_visit_reexecuted": False,
            "second_specialist_execution_started": bool(
                self.scheduler_receipt
            ),
            "second_specialist_execution_completed": self.valid,
            "global_synthesis_created": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
        }


async def dispatch_second_love_visit_from_first_analysis(
    command: GitHubResearchLoveSecondVisitDispatchCommand,
) -> GitHubResearchLoveSecondVisitDispatchResult:
    """Prepare the continuation then submit exactly one second Scheduler visit."""

    try:
        ports = validate_imported_actions_runtime_ports(command.runtime_ports)
        first_dispatch = command.first_dispatch
        first_surface = first_dispatch.surface
        if first_dispatch.valid is not True:
            raise GitHubResearchLoveSecondVisitDispatchError(
                "first specialist dispatch must be valid"
            )
        if first_dispatch.status != "first-specialist-completed":
            raise GitHubResearchLoveSecondVisitDispatchError(
                "first specialist dispatch is not completed"
            )
        if first_surface is None:
            raise GitHubResearchLoveSecondVisitDispatchError(
                "first specialist surface is unavailable"
            )
        if not first_dispatch.scheduler_receipt:
            raise GitHubResearchLoveSecondVisitDispatchError(
                "first Scheduler receipt is unavailable"
            )
        first_result = _first_visit_result_from_receipt(
            first_dispatch.scheduler_receipt
        )
        preparation = _prepare_second_visit(
            first_dispatch=first_dispatch,
            first_result=first_result,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return _invalid("rejected", (str(exc),))

    running = getattr(ports.scheduler, "running", None)
    if running is False:
        return _invalid(
            "scheduler-not-running",
            (
                "the existing Scheduler must already be running; "
                "r16-r11 will not start another Scheduler",
            ),
            first_dispatch=first_dispatch,
            preparation=preparation,
        )

    try:
        resolver = _existing_runtime_resolver(ports.dispatcher)
        resolver.register_concept_analysis(
            preparation.first_analysis,
            preparation.first_artifact,
        )
        resolver.register_task(preparation.second_task)
        receipt = await submit_native_love_collaboration_visit(
            ports.scheduler,
            preparation.second_visit,
            priority=command.priority,
            timeout=command.timeout_seconds,
            source="github.research.love-second-visit",
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return _invalid(
            "second-visit-failed",
            (f"{type(exc).__name__}: {exc}",),
            first_dispatch=first_dispatch,
            preparation=preparation,
        )

    receipt_mapping = receipt.to_mapping()
    execution = receipt_mapping.get("execution")
    execution = execution if isinstance(execution, Mapping) else {}
    if execution.get("specialist_stage") != "second_analysis":
        return _invalid(
            "second-analysis-invalid",
            ("laboratory receipt is not a second-specialist analysis",),
            first_dispatch=first_dispatch,
            preparation=preparation,
            scheduler_receipt=receipt_mapping,
        )
    if execution.get("result_valid") is not True:
        raw_issues = execution.get("validation_issues")
        validation_issues = (
            tuple(str(item) for item in raw_issues)
            if isinstance(raw_issues, (list, tuple))
            else ()
        )
        return _invalid(
            "second-analysis-invalid",
            validation_issues or ("second-specialist result is invalid",),
            first_dispatch=first_dispatch,
            preparation=preparation,
            scheduler_receipt=receipt_mapping,
        )
    if receipt_mapping.get("visit_ref") != preparation.second_visit.visit_ref:
        return _invalid(
            "second-analysis-invalid",
            ("second Scheduler receipt visit_ref mismatch",),
            first_dispatch=first_dispatch,
            preparation=preparation,
            scheduler_receipt=receipt_mapping,
        )

    return GitHubResearchLoveSecondVisitDispatchResult(
        valid=True,
        status="second-specialist-completed",
        issues=(),
        work_package_ref=first_dispatch.work_package_ref,
        first_visit_ref=preparation.second_visit.parent_visit_ref or "",
        second_visit_ref=preparation.second_visit.visit_ref,
        preparation=preparation.to_mapping(),
        scheduler_receipt=receipt_mapping,
    )


def _prepare_second_visit(
    *,
    first_dispatch: GitHubResearchLoveFirstVisitDispatchResult,
    first_result: LaboratoryVisitResult,
) -> NativeLoveCollaborationPreparation:
    surface = first_dispatch.surface
    assert surface is not None
    suffix = hashlib.sha256(
        (
            first_dispatch.work_package_ref
            + "|"
            + surface.first_visit.visit_ref
            + "|"
            + first_result.visit_ref
        ).encode("utf-8")
    ).hexdigest()[:16]
    return prepare_second_specialist_collaboration(
        first_visit=surface.first_visit,
        first_result=first_result,
        second_task_ref=f"specialist-task:love-second-{suffix}",
        second_visit_ref=f"laboratory-visit:love-second-{suffix}",
        capability="love.relational_dynamics",
        objective=(
            "Analyser profondément les dynamiques relationnelles, "
            "la réciprocité, les limites et les tensions."
        ),
    )


def _existing_runtime_resolver(dispatcher: Any) -> GitHubResearchLoveRuntimeResolver:
    handlers = getattr(dispatcher, "handlers", None)
    handler = (
        handlers.get(EventType.LABORATORY_VISIT_REQUEST)
        if isinstance(handlers, Mapping)
        else None
    )
    if not isinstance(handler, NativeLoveCollaborativeVisitRequestHandler):
        raise GitHubResearchLoveSecondVisitDispatchError(
            "the existing love laboratory handler is unavailable"
        )
    resolver = handler.provider.resolver
    if not isinstance(resolver, GitHubResearchLoveRuntimeResolver):
        raise GitHubResearchLoveSecondVisitDispatchError(
            "the existing handler does not own the GitHub research resolver"
        )
    return resolver


def _first_visit_result_from_receipt(
    receipt: Mapping[str, Any],
) -> LaboratoryVisitResult:
    execution = _mapping(receipt.get("execution"))
    if execution.get("specialist_stage") != "first_analysis":
        raise GitHubResearchLoveSecondVisitDispatchError(
            "first receipt does not contain a first-specialist analysis"
        )
    if execution.get("result_valid") is not True:
        raise GitHubResearchLoveSecondVisitDispatchError(
            "first-specialist result is not valid"
        )
    raw = _mapping(execution.get("result"))
    if raw.get("schema") != LABORATORY_VISIT_RESULT_SCHEMA:
        raise GitHubResearchLoveSecondVisitDispatchError(
            "first visit result schema mismatch"
        )
    return LaboratoryVisitResult(
        schema=str(raw["schema"]),
        visit_ref=_required_text(raw, "visit_ref"),
        laboratory_ref=_required_text(raw, "laboratory_ref"),
        specialist_ref=_required_text(raw, "specialist_ref"),
        status=_required_text(raw, "status"),
        output_contract_ref=_required_text(raw, "output_contract_ref"),
        machine_result=dict(_mapping(raw.get("machine_result"))),
        human_representation=_required_text(raw, "human_representation"),
        confidence=_required_float(raw, "confidence"),
        evidence_refs=_text_tuple(raw.get("evidence_refs")),
        assumptions=_text_tuple(raw.get("assumptions")),
        requested_context_refs=_text_tuple(
            raw.get("requested_context_refs")
        ),
        requested_specialist_refs=_text_tuple(
            raw.get("requested_specialist_refs")
        ),
        requested_laboratory_refs=_text_tuple(
            raw.get("requested_laboratory_refs")
        ),
        followup_request_refs=_text_tuple(
            raw.get("followup_request_refs")
        ),
        provenance_refs=_text_tuple(raw.get("provenance_refs")),
        conversation_ref=_optional_text(raw.get("conversation_ref")),
        parent_visit_ref=_optional_text(raw.get("parent_visit_ref")),
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _required_text(value: Mapping[str, Any], name: str) -> str:
    text = _optional_text(value.get(name))
    if text is None:
        raise GitHubResearchLoveSecondVisitDispatchError(
            f"{name} must not be empty"
        )
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise GitHubResearchLoveSecondVisitDispatchError(
            "expected a non-empty string"
        )
    return value.strip()


def _required_float(value: Mapping[str, Any], name: str) -> float:
    raw = value.get(name)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise GitHubResearchLoveSecondVisitDispatchError(
            f"{name} must be numeric"
        )
    return float(raw)


def _text_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise GitHubResearchLoveSecondVisitDispatchError(
            "expected a list of strings"
        )
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise GitHubResearchLoveSecondVisitDispatchError(
                "list entries must be non-empty strings"
            )
        result.append(item.strip())
    return tuple(result)


def _invalid(
    status: str,
    issues: tuple[str, ...] | list[str],
    *,
    first_dispatch: GitHubResearchLoveFirstVisitDispatchResult | None = None,
    preparation: NativeLoveCollaborationPreparation | None = None,
    scheduler_receipt: Mapping[str, Any] | None = None,
) -> GitHubResearchLoveSecondVisitDispatchResult:
    first_visit_ref = ""
    second_visit_ref = ""
    work_package_ref = ""
    if first_dispatch is not None:
        work_package_ref = first_dispatch.work_package_ref
        if first_dispatch.surface is not None:
            first_visit_ref = first_dispatch.surface.first_visit.visit_ref
    if preparation is not None:
        second_visit_ref = preparation.second_visit.visit_ref
    return GitHubResearchLoveSecondVisitDispatchResult(
        valid=False,
        status=status,
        issues=tuple(dict.fromkeys(str(item) for item in issues if str(item))),
        work_package_ref=work_package_ref,
        first_visit_ref=first_visit_ref,
        second_visit_ref=second_visit_ref,
        preparation=(
            preparation.to_mapping() if preparation is not None else {}
        ),
        scheduler_receipt=dict(scheduler_receipt or {}),
    )


__all__ = (
    "GitHubResearchLoveSecondVisitDispatchCommand",
    "GitHubResearchLoveSecondVisitDispatchError",
    "GitHubResearchLoveSecondVisitDispatchResult",
    "SCHEMA",
    "dispatch_second_love_visit_from_first_analysis",
)
