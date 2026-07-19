"""Porte d'acceptation du cycle GitHub → Scheduler → laboratoire → GitHub.

Cette unité ne lance aucune étape du cycle. Elle relit les rapports externes
produits par les outils existants et vérifie que leurs preuves décrivent un
même run, une même Issue et un cycle fermé.

JSON reste ici une frontière de rapport CLI. Il ne devient jamais une
autorité interne du Scheduler. PostgreSQL demeure l'autorité durable.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

ACCEPTANCE_SCHEMA = "missipy.github.research_love_end_to_end_acceptance.v1"
FETCH_SCHEMA = "missipy.github_actions.artifact_fetch_cycle_once.v1"
OPERATIONAL_CLOSED_LOOP_SCHEMA = (
    "missipy.github.research_love_operational_closed_loop.v1"
)
PREPARED_SCHEMA = "missipy.github.research_love_closed_loop_prepared.v1"

EXPECTED_STAGE_ORDER = (
    "ready_run_admissibility",
    "scheduler_intake",
    "scheduler_dispatch",
    "first_specialist",
    "second_specialist",
    "analysis_sql",
    "analysis_qdrant",
    "analysis_recall",
    "liaison_synthesis",
    "final_deliverable_sql",
    "publication_plan",
)

TERMINAL_PHASES = frozenset(
    {"SUCCEEDED", "FAILED", "CANCELLED", "TIMED_OUT"}
)


class GitHubResearchLoveEndToEndAcceptanceError(RuntimeError):
    """Erreur de forme d'une preuve fournie à la porte d'acceptation."""


@dataclass(frozen=True, slots=True)
class EndToEndAcceptanceCommand:
    repository: str
    issue_number: int
    run_id: str
    fetch_cycle: Mapping[str, Any]
    prepared_report: Mapping[str, Any]
    completed_report: Mapping[str, Any]
    temporal_observations: tuple[Mapping[str, str], ...]
    minimum_handler_count: int = 10

    def __post_init__(self) -> None:
        repository = self.repository.strip()
        run_id = self.run_id.strip()
        if "/" not in repository:
            raise GitHubResearchLoveEndToEndAcceptanceError(
                "repository doit être owner/name"
            )
        if (
            isinstance(self.issue_number, bool)
            or not isinstance(self.issue_number, int)
            or self.issue_number <= 0
        ):
            raise GitHubResearchLoveEndToEndAcceptanceError(
                "issue_number doit être strictement positif"
            )
        if not run_id.isdigit():
            raise GitHubResearchLoveEndToEndAcceptanceError(
                "run_id doit contenir uniquement des chiffres"
            )
        if (
            isinstance(self.minimum_handler_count, bool)
            or not isinstance(self.minimum_handler_count, int)
            or self.minimum_handler_count <= 0
        ):
            raise GitHubResearchLoveEndToEndAcceptanceError(
                "minimum_handler_count doit être strictement positif"
            )
        object.__setattr__(self, "repository", repository)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "fetch_cycle", MappingProxyType(dict(self.fetch_cycle)))
        object.__setattr__(
            self,
            "prepared_report",
            MappingProxyType(dict(self.prepared_report)),
        )
        object.__setattr__(
            self,
            "completed_report",
            MappingProxyType(dict(self.completed_report)),
        )
        object.__setattr__(
            self,
            "temporal_observations",
            tuple(MappingProxyType(dict(row)) for row in self.temporal_observations),
        )


@dataclass(frozen=True, slots=True)
class EndToEndAcceptanceReport:
    schema: str
    valid: bool
    status: str
    repository: str
    issue_number: int
    run_id: str
    issues: tuple[str, ...]
    checks: Mapping[str, bool] = field(default_factory=dict)
    evidence: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != ACCEPTANCE_SCHEMA:
            raise GitHubResearchLoveEndToEndAcceptanceError(
                "schéma d'acceptation non pris en charge"
            )
        if self.status not in {"accepted", "rejected"}:
            raise GitHubResearchLoveEndToEndAcceptanceError(
                "statut d'acceptation non pris en charge"
            )
        if self.valid != (self.status == "accepted"):
            raise GitHubResearchLoveEndToEndAcceptanceError(
                "valid et status divergent"
            )
        object.__setattr__(self, "issues", tuple(dict.fromkeys(self.issues)))
        object.__setattr__(self, "checks", MappingProxyType(dict(self.checks)))
        object.__setattr__(self, "evidence", MappingProxyType(dict(self.evidence)))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "status": self.status,
            "repository": self.repository,
            "issue_number": self.issue_number,
            "run_id": self.run_id,
            "issues": list(self.issues),
            "checks": dict(self.checks),
            "evidence": dict(self.evidence),
            "boundaries": {
                "validation_only": True,
                "new_scheduler_created": False,
                "new_dispatcher_created": False,
                "new_laboratory_manager_created": False,
                "remote_mutation_performed": False,
                "postgresql_remains_durable_authority": True,
                "qdrant_remains_projection_only": True,
                "json_is_external_report_boundary_only": True,
                "vispy_remains_observation_only": True,
            },
        }


def validate_github_research_love_end_to_end(
    command: EndToEndAcceptanceCommand,
) -> EndToEndAcceptanceReport:
    """Valider les preuves d'un cycle réel déjà exécuté."""

    issues: list[str] = []
    checks: dict[str, bool] = {}

    checks["fetch_cycle"] = _validate_fetch(command, issues)
    checks["prepared_cycle"] = _validate_prepared(command, issues)
    checks["completed_cycle"] = _validate_completed(command, issues)
    checks["temporal_observations"] = _validate_temporal(command, issues)
    checks["cross_report_correlation"] = _validate_cross_correlation(
        command,
        issues,
    )

    valid = all(checks.values()) and not issues
    evidence = {
        "expected_stage_order": list(EXPECTED_STAGE_ORDER),
        "minimum_handler_count": command.minimum_handler_count,
        "observed_handler_count": len(
            {
                row.get("handler_ref", "")
                for row in command.temporal_observations
                if row.get("handler_ref", "")
            }
        ),
        "observed_task_count": len(
            {
                row.get("task_ref", "")
                for row in command.temporal_observations
                if row.get("task_ref", "")
            }
        ),
        "publication_plan_digest": _publication_plan_digest(
            command.prepared_report
        ),
    }
    return EndToEndAcceptanceReport(
        schema=ACCEPTANCE_SCHEMA,
        valid=valid,
        status="accepted" if valid else "rejected",
        repository=command.repository,
        issue_number=command.issue_number,
        run_id=command.run_id,
        issues=tuple(issues),
        checks=checks,
        evidence=evidence,
    )


def _validate_fetch(
    command: EndToEndAcceptanceCommand,
    issues: list[str],
) -> bool:
    value = command.fetch_cycle
    local: list[str] = []
    if value.get("schema") != FETCH_SCHEMA:
        local.append("fetch: schéma inattendu")
    if value.get("valid") is not True:
        local.append("fetch: rapport non valide")
    if value.get("mode") != "execute":
        local.append("fetch: mode execute requis")
    if value.get("status") != "artifacts-fetched":
        local.append("fetch: statut artifacts-fetched requis")

    matches = [
        candidate
        for candidate in _walk_mappings(value)
        if _matches_identity(candidate, command)
    ]
    if not matches:
        local.append(
            "fetch: aucune preuve corrélée repository/issue_number/run_id"
        )
    roles = {
        str(candidate.get("role", ""))
        for candidate in _walk_mappings(value)
        if _matches_run(candidate, command)
    }
    expected_roles = {
        "authoritative_request",
        "copilot_advisory",
        "run_manifest",
    }
    if roles and not expected_roles.issubset(roles):
        local.append("fetch: triplet de rôles incomplet")
    issues.extend(local)
    return not local


def _validate_prepared(
    command: EndToEndAcceptanceCommand,
    issues: list[str],
) -> bool:
    value = command.prepared_report
    local: list[str] = []
    if value.get("schema") != OPERATIONAL_CLOSED_LOOP_SCHEMA:
        local.append("prepare: schéma opérationnel inattendu")
    if value.get("valid") is not True:
        local.append("prepare: rapport non valide")
    if value.get("mode") != "prepare":
        local.append("prepare: mode prepare requis")
    if value.get("status") != "publication-confirmation-required":
        local.append("prepare: confirmation de publication non demandée")

    input_value = _mapping(value.get("input"))
    prepared = _mapping(value.get("prepared"))
    if input_value.get("repository") != command.repository:
        local.append("prepare: repository divergent")
    if str(input_value.get("run_id", "")) != command.run_id:
        local.append("prepare: run_id divergent")
    if prepared.get("schema") != PREPARED_SCHEMA:
        local.append("prepare: schéma prepared inattendu")
    if prepared.get("valid") is not True:
        local.append("prepare: résultat prepared non valide")
    if int(prepared.get("issue_number", 0) or 0) != command.issue_number:
        local.append("prepare: issue_number divergent")
    stage_order = tuple(prepared.get("stage_order", ()))
    if stage_order != EXPECTED_STAGE_ORDER:
        local.append("prepare: ordre des onze étapes divergent")
    digest = str(value.get("publication_plan_digest", ""))
    if not digest.startswith("sha256:") or len(digest) <= len("sha256:"):
        local.append("prepare: digest de publication absent ou invalide")
    issues.extend(local)
    return not local


def _validate_completed(
    command: EndToEndAcceptanceCommand,
    issues: list[str],
) -> bool:
    value = command.completed_report
    local: list[str] = []
    if value.get("schema") != OPERATIONAL_CLOSED_LOOP_SCHEMA:
        local.append("complete: schéma opérationnel inattendu")
    if value.get("valid") is not True:
        local.append("complete: rapport non valide")
    if value.get("mode") != "complete":
        local.append("complete: mode complete requis")

    input_value = _mapping(value.get("input"))
    if input_value.get("repository") != command.repository:
        local.append("complete: repository divergent")
    if str(input_value.get("run_id", "")) != command.run_id:
        local.append("complete: run_id divergent")

    expected_digest = _publication_plan_digest(command.prepared_report)
    if input_value.get("publication_plan_digest") != expected_digest:
        local.append("complete: digest de publication divergent")

    remote = _mapping(value.get("remote_publication"))
    remote_status = str(remote.get("status", ""))
    if remote_status not in {"published", "published-replay"}:
        local.append("complete: publication distante non confirmée")

    closure = _mapping(value.get("closure"))
    if closure.get("valid") is not True:
        local.append("complete: preuve SQL de clôture non valide")
    if closure.get("cycle_closed") is not True:
        local.append("complete: cycle_closed doit être vrai")

    boundaries = _mapping(value.get("boundaries"))
    if boundaries.get("publication_evidence_persisted") is not True:
        local.append("complete: preuve de publication non persistée")
    if boundaries.get("cycle_closed") is not True:
        local.append("complete: frontière de clôture absente")
    issues.extend(local)
    return not local


def _validate_temporal(
    command: EndToEndAcceptanceCommand,
    issues: list[str],
) -> bool:
    local: list[str] = []
    rows = command.temporal_observations
    if not rows:
        local.append("observations: aucune trace temporelle")
        issues.extend(local)
        return False

    handlers: dict[str, list[Mapping[str, str]]] = {}
    for row in rows:
        handler_ref = row.get("handler_ref", "").strip()
        phase = row.get("phase", "").strip().upper()
        if not handler_ref.startswith("handler:"):
            local.append("observations: handler_ref non typé")
            continue
        if not row.get("scheduler_ref", "").startswith("scheduler:"):
            local.append("observations: scheduler_ref non typé")
        if not row.get("capability_ref", "").startswith("capability:"):
            local.append("observations: capability_ref non typé")
        if phase not in {"CREATED", "STARTED", "SUCCEEDED", "FAILED",
                         "CANCELLED", "TIMED_OUT", "CLOSED"}:
            local.append(f"observations: phase inconnue {phase}")
        handlers.setdefault(handler_ref, []).append(row)

    if len(handlers) < command.minimum_handler_count:
        local.append(
            "observations: nombre de handlers inférieur au minimum "
            f"({len(handlers)} < {command.minimum_handler_count})"
        )

    for handler_ref, handler_rows in handlers.items():
        phases = {
            row.get("phase", "").strip().upper()
            for row in handler_rows
        }
        if "CREATED" not in phases:
            local.append(f"observations: CREATED absent pour {handler_ref}")
        if "STARTED" not in phases:
            local.append(f"observations: STARTED absent pour {handler_ref}")
        if "CLOSED" not in phases:
            local.append(f"observations: CLOSED absent pour {handler_ref}")
        if not phases.intersection(TERMINAL_PHASES):
            local.append(
                f"observations: phase terminale absente pour {handler_ref}"
            )
    issues.extend(local)
    return not local


def _validate_cross_correlation(
    command: EndToEndAcceptanceCommand,
    issues: list[str],
) -> bool:
    local: list[str] = []
    prepared = _mapping(command.prepared_report.get("prepared"))
    completed_input = _mapping(command.completed_report.get("input"))
    work_package_ref = str(prepared.get("work_package_ref", ""))
    if not work_package_ref.startswith("research-work-package:"):
        local.append("corrélation: work_package_ref absent ou non typé")
    if str(completed_input.get("publication_plan_digest", "")) != (
        _publication_plan_digest(command.prepared_report)
    ):
        local.append("corrélation: digest prepare/complete divergent")

    matching_rows = [
        row
        for row in command.temporal_observations
        if (
            not row.get("command_ref")
            or row.get("command_ref", "").startswith("scheduler-command:")
        )
    ]
    if len(matching_rows) != len(command.temporal_observations):
        local.append("corrélation: command_ref temporel non typé")
    issues.extend(local)
    return not local


def _publication_plan_digest(value: Mapping[str, Any]) -> str:
    return str(value.get("publication_plan_digest", "")).strip()


def _matches_identity(
    candidate: Mapping[str, Any],
    command: EndToEndAcceptanceCommand,
) -> bool:
    repository = str(candidate.get("repository", "")).strip()
    run_id = str(candidate.get("run_id", "")).strip()
    issue_number = candidate.get("issue_number")
    if issue_number is None:
        issue_number = candidate.get("number")
    try:
        normalized_issue = int(issue_number)
    except (TypeError, ValueError):
        return False
    return (
        repository == command.repository
        and run_id == command.run_id
        and normalized_issue == command.issue_number
    )


def _matches_run(
    candidate: Mapping[str, Any],
    command: EndToEndAcceptanceCommand,
) -> bool:
    return (
        str(candidate.get("repository", "")).strip()
        in {"", command.repository}
        and str(candidate.get("run_id", "")).strip() == command.run_id
    )


def _walk_mappings(value: object) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from _walk_mappings(child)
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        for child in value:
            yield from _walk_mappings(child)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


__all__ = (
    "ACCEPTANCE_SCHEMA",
    "EndToEndAcceptanceCommand",
    "EndToEndAcceptanceReport",
    "EXPECTED_STAGE_ORDER",
    "GitHubResearchLoveEndToEndAcceptanceError",
    "validate_github_research_love_end_to_end",
)
