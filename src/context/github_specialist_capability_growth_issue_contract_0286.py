"""Normalize a GitHub Issue-form request for specialist capability growth.

Phase 0286-r3 adds a dedicated request surface to ``newicody/projects``.  This
module reads the resulting Issue body or the existing authoritative-request
artifact and returns one immutable local intake contract.  It performs no
GitHub mutation, operator approval, SQL/Qdrant write, Scheduler dispatch or
laboratory execution.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Literal

GITHUB_SPECIALIST_CAPABILITY_GROWTH_ISSUE_REQUEST_SCHEMA = (
    "missipy.github.specialist_capability_growth_issue_request.v1"
)
GITHUB_SPECIALIST_CAPABILITY_GROWTH_ISSUE_CONTRACT_VERSION = "0286.r3"

SpecialistCapabilityGrowthRequestedAction = Literal[
    "add",
    "refine",
    "deprecate",
    "restore",
]

_ACTION_ALIASES = {
    "add": "add",
    "ajouter": "add",
    "refine": "refine",
    "affiner": "refine",
    "deprecate": "deprecate",
    "déprécier": "deprecate",
    "deprecier": "deprecate",
    "restore": "restore",
    "restaurer": "restore",
}
_SECTION_LABELS = {
    "specialist_ref": "Référence du spécialiste",
    "base_specialist_version": "Version de base du spécialiste",
    "action": "Action demandée",
    "capability": "Capacité concernée",
    "proposed_description": "Description de l'évolution demandée",
    "evidence_refs": "Preuves existantes",
    "evidence_expectation": "Preuves à produire ou critères de validation",
    "requested_input_contract_refs": "Contrats d'entrée demandés",
    "requested_output_contract_refs": "Contrats de sortie demandés",
    "requested_laboratory_capability_refs": "Capacités de laboratoire requises",
    "conversation_ref": "Conversation",
    "context_refs": "Contextes liés",
    "copilot": "Avis Copilot",
    "authority_boundary": "Confirmation de frontière",
}

_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}(?:[-+][a-z0-9.-]+)?$")
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_.-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HEADING_RE = re.compile(r"^###\s+(?P<label>.+?)\s*$")
_CHECKED_RE = re.compile(r"^-\s*\[[xX]\]\s*(?P<label>.+?)\s*$")
_NO_RESPONSE_VALUES = frozenset({"", "_No response_", "No response"})

_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_EVIDENCE_PREFIXES = (
    "artifact:",
    "evidence:",
    "observation:",
    "report:",
    "result:",
    "sql:",
    "test:",
)
_CONTRACT_PREFIXES = ("contract:",)
_LABORATORY_CAPABILITY_PREFIXES = ("laboratory-capability:",)
_CONVERSATION_PREFIXES = ("conversation:",)
_CONTEXT_PREFIXES = ("context:", "sql:")


class GitHubSpecialistCapabilityGrowthIssueContractError(ValueError):
    """Raised when an Issue cannot form a safe normalized request."""


@dataclass(frozen=True, slots=True)
class GitHubSpecialistCapabilityGrowthIssueRequest:
    """Immutable request extracted from the dedicated GitHub Issue form."""

    schema: str
    request_ref: str
    repository: str
    issue_number: int
    issue_url: str
    issue_title: str
    requester_ref: str
    specialist_ref: str
    base_specialist_version: str
    action: SpecialistCapabilityGrowthRequestedAction
    capability: str
    proposed_description: str
    evidence_refs: tuple[str, ...]
    evidence_expectation: str
    requested_input_contract_refs: tuple[str, ...]
    requested_output_contract_refs: tuple[str, ...]
    requested_laboratory_capability_refs: tuple[str, ...]
    conversation_ref: str
    context_refs: tuple[str, ...]
    copilot_advisory_requested: bool
    authority_boundary_acknowledged: bool
    issue_revision_digest_sha256: str
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != GITHUB_SPECIALIST_CAPABILITY_GROWTH_ISSUE_REQUEST_SCHEMA:
            raise GitHubSpecialistCapabilityGrowthIssueContractError(
                "unsupported GitHub specialist capability-growth request schema"
            )
        _require_ref("request_ref", self.request_ref, ("github-capability-growth-request:",))
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise GitHubSpecialistCapabilityGrowthIssueContractError(
                "repository must use owner/name form"
            )
        if not isinstance(self.issue_number, int) or self.issue_number <= 0:
            raise GitHubSpecialistCapabilityGrowthIssueContractError(
                "issue_number must be positive"
            )
        _require_non_empty("issue_title", self.issue_title)
        _require_ref("requester_ref", self.requester_ref, ("actor:",))
        _require_ref("specialist_ref", self.specialist_ref, _SPECIALIST_PREFIXES)
        if not _VERSION_RE.fullmatch(self.base_specialist_version):
            raise GitHubSpecialistCapabilityGrowthIssueContractError(
                "base_specialist_version must be a supported version token"
            )
        if self.action not in frozenset(_ACTION_ALIASES.values()):
            raise GitHubSpecialistCapabilityGrowthIssueContractError(
                "unsupported specialist capability-growth action"
            )
        if not _CAPABILITY_RE.fullmatch(self.capability):
            raise GitHubSpecialistCapabilityGrowthIssueContractError(
                "capability must be a lowercase capability token"
            )
        _require_non_empty("proposed_description", self.proposed_description)
        _require_non_empty("evidence_expectation", self.evidence_expectation)
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs("evidence_refs", self.evidence_refs, _EVIDENCE_PREFIXES),
        )
        object.__setattr__(
            self,
            "requested_input_contract_refs",
            _normalize_refs(
                "requested_input_contract_refs",
                self.requested_input_contract_refs,
                _CONTRACT_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "requested_output_contract_refs",
            _normalize_refs(
                "requested_output_contract_refs",
                self.requested_output_contract_refs,
                _CONTRACT_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "requested_laboratory_capability_refs",
            _normalize_refs(
                "requested_laboratory_capability_refs",
                self.requested_laboratory_capability_refs,
                _LABORATORY_CAPABILITY_PREFIXES,
            ),
        )
        _require_ref("conversation_ref", self.conversation_ref, _CONVERSATION_PREFIXES)
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs("context_refs", self.context_refs, _CONTEXT_PREFIXES),
        )
        if not self.authority_boundary_acknowledged:
            raise GitHubSpecialistCapabilityGrowthIssueContractError(
                "operator decision boundary must be acknowledged"
            )
        if not _SHA256_RE.fullmatch(self.issue_revision_digest_sha256):
            raise GitHubSpecialistCapabilityGrowthIssueContractError(
                "issue_revision_digest_sha256 must be a lowercase SHA-256 digest"
            )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def missing_proposal_prerequisites(self) -> tuple[str, ...]:
        """Return fields still needed before the 0285-r2 proposal can be built."""

        missing: list[str] = []
        if not self.evidence_refs:
            missing.append("evidence_refs")
        if self.action != "deprecate":
            if not self.requested_input_contract_refs:
                missing.append("requested_input_contract_refs")
            if not self.requested_output_contract_refs:
                missing.append("requested_output_contract_refs")
        return tuple(missing)

    @property
    def proposal_ready(self) -> bool:
        """Whether the request contains the references required by proposal r2."""

        return not self.missing_proposal_prerequisites

    @property
    def request_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_digest=False),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_mapping(self, *, include_digest: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": self.schema,
            "request_ref": self.request_ref,
            "repository": self.repository,
            "issue_number": self.issue_number,
            "issue_url": self.issue_url,
            "issue_title": self.issue_title,
            "requester_ref": self.requester_ref,
            "specialist_ref": self.specialist_ref,
            "base_specialist_version": self.base_specialist_version,
            "action": self.action,
            "capability": self.capability,
            "proposed_description": self.proposed_description,
            "evidence_refs": list(self.evidence_refs),
            "evidence_expectation": self.evidence_expectation,
            "requested_input_contract_refs": list(
                self.requested_input_contract_refs
            ),
            "requested_output_contract_refs": list(
                self.requested_output_contract_refs
            ),
            "requested_laboratory_capability_refs": list(
                self.requested_laboratory_capability_refs
            ),
            "conversation_ref": self.conversation_ref,
            "context_refs": list(self.context_refs),
            "copilot_advisory_requested": self.copilot_advisory_requested,
            "authority_boundary_acknowledged": self.authority_boundary_acknowledged,
            "issue_revision_digest_sha256": self.issue_revision_digest_sha256,
            "metadata": dict(self.metadata),
            "proposal_ready": self.proposal_ready,
            "missing_proposal_prerequisites": list(
                self.missing_proposal_prerequisites
            ),
            "approval_authoritative": False,
            "revision_authorized": False,
            "scheduler_dispatch_allowed": False,
            "sql_write_allowed": False,
            "qdrant_write_allowed": False,
            "github_projects_authoritative": False,
            "operator_decision_remains_local": True,
            "new_scheduler_created": False,
            "new_global_specialist_registry_created": False,
        }
        if include_digest:
            payload["request_digest"] = self.request_digest
        return payload


def parse_github_issue_form_sections(body: str) -> dict[str, str]:
    """Parse the stable ``### label`` sections emitted by GitHub Issue forms."""

    if not isinstance(body, str) or not body.strip():
        raise GitHubSpecialistCapabilityGrowthIssueContractError(
            "GitHub Issue body is required"
        )
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in body.splitlines():
        heading = _HEADING_RE.match(raw_line)
        if heading:
            current = heading.group("label").strip()
            if current in sections:
                raise GitHubSpecialistCapabilityGrowthIssueContractError(
                    f"duplicate GitHub Issue form section: {current}"
                )
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(raw_line)
    return {
        label: "\n".join(lines).strip()
        for label, lines in sections.items()
    }


def build_github_specialist_capability_growth_issue_request(
    source: Mapping[str, object],
    *,
    repository: str | None = None,
    actor: str | None = None,
) -> GitHubSpecialistCapabilityGrowthIssueRequest:
    """Normalize an authoritative artifact, event or raw GitHub Issue mapping."""

    envelope = _extract_issue_envelope(source, repository=repository, actor=actor)
    sections = parse_github_issue_form_sections(envelope["body"])

    def section(key: str, *, required: bool = False) -> str:
        label = _SECTION_LABELS[key]
        value = sections.get(label, "").strip()
        if value in _NO_RESPONSE_VALUES:
            value = ""
        if required and not value:
            raise GitHubSpecialistCapabilityGrowthIssueContractError(
                f"required GitHub Issue form section is missing: {label}"
            )
        return value

    issue_digest = sha256(
        json.dumps(
            {
                "repository": envelope["repository"],
                "issue_number": envelope["issue_number"],
                "issue_title": envelope["title"],
                "body": envelope["body"],
                "actor": envelope["actor"],
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    issue_number = int(envelope["issue_number"])
    repository_name = str(envelope["repository"])
    conversation_ref = section("conversation_ref") or (
        f"conversation:github:{repository_name}:{issue_number}"
    )
    context_refs = list(_lines_as_refs(section("context_refs")))
    implicit_context_ref = f"context:github:{repository_name}:issue:{issue_number}"
    if implicit_context_ref not in context_refs:
        context_refs.append(implicit_context_ref)

    authority_text = section("authority_boundary", required=True)
    boundary_acknowledged = any(
        "décision opérateur reste locale" in match.group("label").casefold()
        for line in authority_text.splitlines()
        if (match := _CHECKED_RE.match(line.strip())) is not None
    )
    copilot_text = section("copilot")
    copilot_requested = any(
        "copilot" in match.group("label").casefold()
        for line in copilot_text.splitlines()
        if (match := _CHECKED_RE.match(line.strip())) is not None
    )

    return GitHubSpecialistCapabilityGrowthIssueRequest(
        schema=GITHUB_SPECIALIST_CAPABILITY_GROWTH_ISSUE_REQUEST_SCHEMA,
        request_ref=(
            "github-capability-growth-request:"
            f"{repository_name}:{issue_number}:{issue_digest[:20]}"
        ),
        repository=repository_name,
        issue_number=issue_number,
        issue_url=str(envelope["issue_url"]),
        issue_title=str(envelope["title"]).strip(),
        requester_ref=f"actor:{envelope['actor']}",
        specialist_ref=section("specialist_ref", required=True),
        base_specialist_version=section(
            "base_specialist_version", required=True
        ),
        action=_normalize_action(section("action", required=True)),
        capability=section("capability", required=True),
        proposed_description=section("proposed_description", required=True),
        evidence_refs=_lines_as_refs(section("evidence_refs")),
        evidence_expectation=section("evidence_expectation", required=True),
        requested_input_contract_refs=_lines_as_refs(
            section("requested_input_contract_refs")
        ),
        requested_output_contract_refs=_lines_as_refs(
            section("requested_output_contract_refs")
        ),
        requested_laboratory_capability_refs=_lines_as_refs(
            section("requested_laboratory_capability_refs")
        ),
        conversation_ref=conversation_ref,
        context_refs=tuple(context_refs),
        copilot_advisory_requested=copilot_requested,
        authority_boundary_acknowledged=boundary_acknowledged,
        issue_revision_digest_sha256=issue_digest,
        metadata=(("source", "github_issue_form"), ("form_version", "0286.r3")),
    )


def _extract_issue_envelope(
    source: Mapping[str, object],
    *,
    repository: str | None,
    actor: str | None,
) -> dict[str, object]:
    if not isinstance(source, Mapping):
        raise GitHubSpecialistCapabilityGrowthIssueContractError(
            "source must be a mapping"
        )
    if source.get("schema") == "missipy.github.authoritative_request.v1":
        issue = source
        repository_name = str(repository or source.get("repository") or "").strip()
        actor_name = str(actor or source.get("actor") or "").strip()
        number = int(source.get("issue_number") or 0)
        url = str(source.get("issue_url") or "")
    elif isinstance(source.get("issue"), Mapping):
        issue = source["issue"]
        repository_block = source.get("repository")
        sender_block = source.get("sender")
        repository_name = str(
            repository
            or (
                repository_block.get("full_name")
                if isinstance(repository_block, Mapping)
                else ""
            )
            or ""
        ).strip()
        actor_name = str(
            actor
            or (
                sender_block.get("login")
                if isinstance(sender_block, Mapping)
                else ""
            )
            or ""
        ).strip()
        number = int(issue.get("number") or 0)
        url = str(issue.get("html_url") or "")
    else:
        issue = source
        repository_name = str(repository or "").strip()
        actor_name = str(actor or "").strip()
        number = int(issue.get("number") or 0)
        url = str(issue.get("html_url") or "")

    if not _REPOSITORY_RE.fullmatch(repository_name):
        raise GitHubSpecialistCapabilityGrowthIssueContractError(
            "repository must use owner/name form"
        )
    if number <= 0:
        raise GitHubSpecialistCapabilityGrowthIssueContractError(
            "GitHub Issue number must be positive"
        )
    if not actor_name or any(char.isspace() for char in actor_name):
        raise GitHubSpecialistCapabilityGrowthIssueContractError(
            "GitHub actor is required"
        )
    title = str(issue.get("title") or "").strip()
    body = str(issue.get("body") or "")
    if not title:
        raise GitHubSpecialistCapabilityGrowthIssueContractError(
            "GitHub Issue title is required"
        )
    if not body.strip():
        raise GitHubSpecialistCapabilityGrowthIssueContractError(
            "GitHub Issue body is required"
        )
    return {
        "repository": repository_name,
        "issue_number": number,
        "issue_url": url,
        "title": title,
        "body": body,
        "actor": actor_name,
    }


def _normalize_action(value: str) -> SpecialistCapabilityGrowthRequestedAction:
    normalized = value.strip().casefold()
    action = _ACTION_ALIASES.get(normalized)
    if action is None:
        raise GitHubSpecialistCapabilityGrowthIssueContractError(
            "unsupported specialist capability-growth action"
        )
    return action  # type: ignore[return-value]


def _lines_as_refs(value: str) -> tuple[str, ...]:
    if value in _NO_RESPONSE_VALUES:
        return ()
    refs: list[str] = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line or line in _NO_RESPONSE_VALUES:
            continue
        line = re.sub(r"^[-*+]\s+", "", line).strip()
        if line:
            refs.append(line)
    return tuple(refs)


def _normalize_refs(
    name: str,
    values: tuple[str, ...],
    prefixes: tuple[str, ...],
) -> tuple[str, ...]:
    normalized = tuple(sorted({str(value).strip() for value in values if str(value).strip()}))
    for value in normalized:
        _require_ref(name, value, prefixes)
    return normalized


def _normalize_metadata(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    keys: set[str] = set()
    for key, value in values:
        key_text = str(key).strip()
        value_text = str(value).strip()
        if not key_text or not value_text or key_text in keys:
            raise GitHubSpecialistCapabilityGrowthIssueContractError(
                "metadata must contain unique non-empty key/value pairs"
            )
        keys.add(key_text)
        normalized.append((key_text, value_text))
    return tuple(sorted(normalized))


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise GitHubSpecialistCapabilityGrowthIssueContractError(
            f"{name} must be non-empty"
        )


def _require_ref(name: str, value: str, prefixes: tuple[str, ...]) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or any(char.isspace() for char in value)
        or not value.startswith(prefixes)
    ):
        raise GitHubSpecialistCapabilityGrowthIssueContractError(
            f"{name} must use one of the required typed-reference prefixes"
        )


__all__ = (
    "GITHUB_SPECIALIST_CAPABILITY_GROWTH_ISSUE_CONTRACT_VERSION",
    "GITHUB_SPECIALIST_CAPABILITY_GROWTH_ISSUE_REQUEST_SCHEMA",
    "GitHubSpecialistCapabilityGrowthIssueContractError",
    "GitHubSpecialistCapabilityGrowthIssueRequest",
    "SpecialistCapabilityGrowthRequestedAction",
    "build_github_specialist_capability_growth_issue_request",
    "parse_github_issue_form_sections",
)
