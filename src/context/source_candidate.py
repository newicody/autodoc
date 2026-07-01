from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any

_ALLOWED_ORIGIN_KINDS = frozenset({"local", "file", "artifact_dir", "github", "manual"})
_ALLOWED_STATUSES = frozenset({"new", "analyzed", "rejected", "archived", "promoted", "merged"})
_ALLOWED_DECISIONS = frozenset({"inspect", "relaunch", "reject", "archive", "promote", "merge"})
_DECISION_STATUS = {
    "inspect": "analyzed",
    "relaunch": "analyzed",
    "reject": "rejected",
    "archive": "archived",
    "promote": "promoted",
    "merge": "merged",
}


@dataclass(frozen=True, slots=True)
class SourceCandidateOrigin:
    """Origine sérialisable d'une entrée candidate.

    L'origine ne lit rien et ne contacte aucun service. Elle décrit seulement
    d'où provient la matière brute : dossier local, fichier, saisie manuelle ou
    future projection GitHub.
    """

    kind: str = "local"
    reference: str = ""
    repository: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in _ALLOWED_ORIGIN_KINDS:
            raise ValueError("origin kind must be local, file, artifact_dir, github or manual")
        if self.repository is not None and not self.repository.strip():
            raise ValueError("repository must not be empty")

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "kind": self.kind,
            "reference": self.reference,
            "repository": self.repository,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateInput:
    """Entrée brute normalisée avant création d'une SourceCandidate.

    Ce contrat est local et immuable. Il ne persiste rien et ne décide pas si la
    candidate doit être promue, rejetée ou fusionnée.
    """

    title: str
    body: str
    origin: SourceCandidateOrigin = SourceCandidateOrigin()
    labels: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not isinstance(self.labels, tuple):
            object.__setattr__(self, "labels", tuple(self.labels))
        _validate_labels(self.labels)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class SourceCandidatePolicy:
    """Politique locale de création de SourceCandidate.

    default_repository prépare la projection future GitHub sans ouvrir de réseau
    ni dépendre de l'API GitHub. La valeur par défaut suit le namespace projet
    actuellement ciblé : newicody/autodoc.
    """

    default_status: str = "new"
    default_repository: str | None = "newicody/autodoc"
    id_prefix: str = "sc"

    def __post_init__(self) -> None:
        if self.default_status not in _ALLOWED_STATUSES:
            raise ValueError("default_status must be new, analyzed, rejected, archived, promoted or merged")
        if self.default_repository is not None and not self.default_repository.strip():
            raise ValueError("default_repository must not be empty")
        if not self.id_prefix.strip():
            raise ValueError("id_prefix must not be empty")


@dataclass(frozen=True, slots=True)
class SourceCandidateDecision:
    """Décision opérateur immuable appliquée à une SourceCandidate.

    La décision est un contrat local : elle ne modifie aucun fichier, ne crée
    aucune issue GitHub et ne déclenche aucun Scheduler.
    """

    action: str
    reason: str = ""
    target_context_id: str | None = None

    def __post_init__(self) -> None:
        if self.action not in _ALLOWED_DECISIONS:
            raise ValueError("action must be inspect, relaunch, reject, archive, promote or merge")
        if self.target_context_id is not None and not self.target_context_id.strip():
            raise ValueError("target_context_id must not be empty")

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "action": self.action,
            "reason": self.reason,
            "target_context_id": self.target_context_id,
            "resulting_status": _DECISION_STATUS[self.action],
        }


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    """Candidate locale de contexte avant stockage, promotion ou projection GitHub."""

    candidate_id: str
    title: str
    body: str
    origin: SourceCandidateOrigin
    status: str = "new"
    labels: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)
    decision: SourceCandidateDecision | None = None

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must not be empty")
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if self.status not in _ALLOWED_STATUSES:
            raise ValueError("status must be new, analyzed, rejected, archived, promoted or merged")
        if not isinstance(self.labels, tuple):
            object.__setattr__(self, "labels", tuple(self.labels))
        _validate_labels(self.labels)
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def terminal(self) -> bool:
        return self.status in {"rejected", "archived", "promoted", "merged"}

    @property
    def actionable(self) -> bool:
        return not self.terminal

    def with_status(self, status: str) -> SourceCandidate:
        if status not in _ALLOWED_STATUSES:
            raise ValueError("status must be new, analyzed, rejected, archived, promoted or merged")
        return replace(self, status=status)

    def with_decision(self, decision: SourceCandidateDecision) -> SourceCandidate:
        return replace(self, decision=decision, status=_DECISION_STATUS[decision.action])

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "schema": "missipy.source_candidate.v1",
            "candidate_id": self.candidate_id,
            "title": self.title,
            "body": self.body,
            "origin": self.origin.to_json_dict(),
            "status": self.status,
            "terminal": self.terminal,
            "actionable": self.actionable,
            "labels": list(self.labels),
            "metadata": dict(self.metadata),
            "decision": self.decision.to_json_dict() if self.decision is not None else None,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateCreationResult:
    """Résultat stable de création locale d'une SourceCandidate."""

    candidate: SourceCandidate
    policy: SourceCandidatePolicy

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "schema": "missipy.source_candidate.creation.v1",
            "candidate": self.candidate.to_json_dict(),
            "policy": {
                "default_status": self.policy.default_status,
                "default_repository": self.policy.default_repository,
                "id_prefix": self.policy.id_prefix,
            },
        }


def build_source_candidate(
    candidate_input: SourceCandidateInput,
    policy: SourceCandidatePolicy | None = None,
) -> SourceCandidateCreationResult:
    """Crée une SourceCandidate locale déterministe sans IO ni stockage."""
    effective = policy or SourceCandidatePolicy()
    origin = candidate_input.origin
    if origin.repository is None and effective.default_repository is not None:
        origin = replace(origin, repository=effective.default_repository)
    candidate = SourceCandidate(
        candidate_id=_candidate_id(candidate_input, origin, effective),
        title=candidate_input.title.strip(),
        body=candidate_input.body,
        origin=origin,
        status=effective.default_status,
        labels=candidate_input.labels,
        metadata=candidate_input.metadata,
    )
    return SourceCandidateCreationResult(candidate=candidate, policy=effective)


def apply_source_candidate_decision(
    candidate: SourceCandidate,
    decision: SourceCandidateDecision,
) -> SourceCandidate:
    """Retourne une nouvelle candidate avec décision et statut dérivé."""
    return candidate.with_decision(decision)


def allowed_source_candidate_statuses() -> tuple[str, ...]:
    return tuple(sorted(_ALLOWED_STATUSES))


def allowed_source_candidate_decisions() -> tuple[str, ...]:
    return tuple(sorted(_ALLOWED_DECISIONS))


def _candidate_id(
    candidate_input: SourceCandidateInput,
    origin: SourceCandidateOrigin,
    policy: SourceCandidatePolicy,
) -> str:
    digest = hashlib.sha256()
    digest.update(policy.id_prefix.encode("utf-8"))
    digest.update(b"\0")
    digest.update(origin.kind.encode("utf-8"))
    digest.update(b"\0")
    digest.update(origin.reference.encode("utf-8"))
    digest.update(b"\0")
    digest.update((origin.repository or "").encode("utf-8"))
    digest.update(b"\0")
    digest.update(candidate_input.title.strip().encode("utf-8"))
    digest.update(b"\0")
    digest.update(candidate_input.body.encode("utf-8"))
    return f"{policy.id_prefix}-{digest.hexdigest()[:16]}"


def _validate_labels(labels: Sequence[str]) -> None:
    for label in labels:
        if not isinstance(label, str) or not label.strip():
            raise ValueError("labels must be non-empty strings")


def _freeze_metadata(metadata: Mapping[str, object]) -> Mapping[str, object]:
    frozen: dict[str, object] = {}
    for key, value in metadata.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("metadata keys must be non-empty strings")
        frozen[key] = _json_safe_value(value)
    return MappingProxyType(frozen)


def _json_safe_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe_value(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe_value(item) for item in value]
    return str(value)
