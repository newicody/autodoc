from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from .source_candidate import (
    SourceCandidate,
    SourceCandidateDecision,
    SourceCandidateOrigin,
)

_STORE_SCHEMA = "missipy.source_candidate.store.v1"
_WRITE_SCHEMA = "missipy.source_candidate.store_write.v1"
_REPORT_SCHEMA = "missipy.source_candidate.store_report.v1"


@dataclass(frozen=True, slots=True)
class SourceCandidateStorePolicy:
    """Politique d'IO locale pour un store JSON SourceCandidate.

    Le store reste une bordure explicite : un chemin de fichier est fourni par
    l'appelant, l'écriture est atomique et aucun service externe n'est contacté.
    """

    path: Path | str
    repository: str | None = "newicody/autodoc"
    encoding: str = "utf-8"
    create_parent_dirs: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        if not str(self.path).strip():
            raise ValueError("store path must not be empty")
        if not self.path.name:
            raise ValueError("store path must target a filename")
        if self.repository is not None and not self.repository.strip():
            raise ValueError("repository must not be empty")
        if not self.encoding.strip():
            raise ValueError("encoding must not be empty")


@dataclass(frozen=True, slots=True)
class SourceCandidateReportPolicy:
    """Politique d'écriture optionnelle d'un rapport de store SourceCandidate."""

    path: Path | str | None = None
    encoding: str = "utf-8"
    create_parent_dirs: bool = True

    def __post_init__(self) -> None:
        if self.path is not None:
            object.__setattr__(self, "path", Path(self.path))
        if self.path is not None and not self.path.name:
            raise ValueError("report path must target a filename")
        if not self.encoding.strip():
            raise ValueError("encoding must not be empty")


@dataclass(frozen=True, slots=True)
class SourceCandidateStoreSnapshot:
    """Snapshot sérialisable du store local SourceCandidate."""

    candidates: tuple[SourceCandidate, ...] = ()
    repository: str | None = "newicody/autodoc"
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.candidates, tuple):
            object.__setattr__(self, "candidates", tuple(self.candidates))
        if self.repository is not None and not self.repository.strip():
            raise ValueError("repository must not be empty")
        _validate_unique_candidate_ids(self.candidates)

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    def find(self, candidate_id: str) -> SourceCandidate | None:
        for candidate in self.candidates:
            if candidate.candidate_id == candidate_id:
                return candidate
        return None

    def with_candidate(self, candidate: SourceCandidate) -> tuple[SourceCandidateStoreSnapshot, bool, bool]:
        """Retourne un snapshot avec candidate insérée ou remplacée.

        Returns:
            (snapshot, inserted, replaced)
        """
        next_candidates: list[SourceCandidate] = []
        replaced = False
        for existing in self.candidates:
            if existing.candidate_id == candidate.candidate_id:
                next_candidates.append(candidate)
                replaced = True
            else:
                next_candidates.append(existing)
        if not replaced:
            next_candidates.append(candidate)
        return (
            replace(self, candidates=tuple(next_candidates)),
            not replaced,
            replaced,
        )

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "schema": _STORE_SCHEMA,
            "repository": self.repository,
            "candidate_count": self.candidate_count,
            "candidate_ids": [candidate.candidate_id for candidate in self.candidates],
            "metadata": dict(self.metadata),
            "candidates": [candidate.to_json_dict() for candidate in self.candidates],
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateStoreWriteResult:
    """Résultat stable d'une écriture locale SourceCandidate."""

    path: Path
    snapshot: SourceCandidateStoreSnapshot
    candidate: SourceCandidate
    inserted: bool
    replaced: bool

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _WRITE_SCHEMA,
            "path": str(self.path),
            "candidate_id": self.candidate.candidate_id,
            "inserted": self.inserted,
            "replaced": self.replaced,
            "candidate_count": self.snapshot.candidate_count,
            "snapshot": self.snapshot.to_json_dict(),
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateStoreReport:
    """Rapport optionnel écrit après opération sur le store local."""

    write_result: SourceCandidateStoreWriteResult

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _REPORT_SCHEMA,
            "operation": "upsert_source_candidate",
            "write_result": self.write_result.to_json_dict(),
        }


def load_source_candidate_store(policy: SourceCandidateStorePolicy) -> SourceCandidateStoreSnapshot:
    """Charge un store JSON local ou retourne un snapshot vide si le fichier manque."""
    if not policy.path.exists():
        return SourceCandidateStoreSnapshot(repository=policy.repository)
    payload = json.loads(policy.path.read_text(encoding=policy.encoding))
    if not isinstance(payload, dict):
        raise ValueError("source candidate store payload must be an object")
    return source_candidate_store_snapshot_from_json_dict(payload)


def write_source_candidate_store(
    policy: SourceCandidateStorePolicy,
    snapshot: SourceCandidateStoreSnapshot,
) -> SourceCandidateStoreSnapshot:
    """Écrit atomiquement un snapshot SourceCandidate local."""
    _write_json_atomic(
        path=policy.path,
        payload=snapshot.to_json_dict(),
        encoding=policy.encoding,
        create_parent_dirs=policy.create_parent_dirs,
    )
    return snapshot


def upsert_source_candidate(
    policy: SourceCandidateStorePolicy,
    candidate: SourceCandidate,
    *,
    report: SourceCandidateReportPolicy | None = None,
) -> SourceCandidateStoreWriteResult:
    """Insère ou remplace une SourceCandidate dans un store JSON local."""
    snapshot = load_source_candidate_store(policy)
    next_snapshot, inserted, replaced_candidate = snapshot.with_candidate(candidate)
    write_source_candidate_store(policy, next_snapshot)
    result = SourceCandidateStoreWriteResult(
        path=policy.path,
        snapshot=next_snapshot,
        candidate=candidate,
        inserted=inserted,
        replaced=replaced_candidate,
    )
    if report is not None:
        write_source_candidate_store_report(report, SourceCandidateStoreReport(result))
    return result


def write_source_candidate_store_report(
    policy: SourceCandidateReportPolicy,
    report: SourceCandidateStoreReport,
) -> SourceCandidateStoreReport:
    """Écrit atomiquement le rapport optionnel d'une opération SourceCandidate."""
    if policy.path is None:
        return report
    _write_json_atomic(
        path=policy.path,
        payload=report.to_json_dict(),
        encoding=policy.encoding,
        create_parent_dirs=policy.create_parent_dirs,
    )
    return report


def source_candidate_store_snapshot_from_json_dict(
    payload: dict[str, object],
) -> SourceCandidateStoreSnapshot:
    """Reconstruit un snapshot SourceCandidate depuis son JSON stable."""
    if payload.get("schema") != _STORE_SCHEMA:
        raise ValueError("source candidate store schema must be missipy.source_candidate.store.v1")
    raw_candidates = payload.get("candidates", [])
    if not isinstance(raw_candidates, list):
        raise ValueError("source candidate store candidates must be a list")
    repository = payload.get("repository")
    if repository is not None and not isinstance(repository, str):
        raise ValueError("source candidate store repository must be a string or null")
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("source candidate store metadata must be an object")
    return SourceCandidateStoreSnapshot(
        candidates=tuple(_source_candidate_from_json_dict(candidate) for candidate in raw_candidates),
        repository=repository,
        metadata=dict(metadata),
    )


def _source_candidate_from_json_dict(payload: object) -> SourceCandidate:
    if not isinstance(payload, dict):
        raise ValueError("source candidate payload must be an object")
    if payload.get("schema") != "missipy.source_candidate.v1":
        raise ValueError("source candidate schema must be missipy.source_candidate.v1")

    origin_payload = payload.get("origin")
    if not isinstance(origin_payload, dict):
        raise ValueError("source candidate origin must be an object")
    origin = SourceCandidateOrigin(
        kind=_required_str(origin_payload, "kind"),
        reference=_optional_str(origin_payload, "reference") or "",
        repository=_optional_str(origin_payload, "repository"),
    )

    decision_payload = payload.get("decision")
    decision = None
    if decision_payload is not None:
        if not isinstance(decision_payload, dict):
            raise ValueError("source candidate decision must be an object or null")
        decision = SourceCandidateDecision(
            action=_required_str(decision_payload, "action"),
            reason=_optional_str(decision_payload, "reason") or "",
            target_context_id=_optional_str(decision_payload, "target_context_id"),
        )

    labels_payload = payload.get("labels", [])
    if not isinstance(labels_payload, list):
        raise ValueError("source candidate labels must be a list")
    metadata_payload = payload.get("metadata", {})
    if not isinstance(metadata_payload, dict):
        raise ValueError("source candidate metadata must be an object")

    return SourceCandidate(
        candidate_id=_required_str(payload, "candidate_id"),
        title=_required_str(payload, "title"),
        body=_required_str(payload, "body"),
        origin=origin,
        status=_required_str(payload, "status"),
        labels=tuple(_require_str_value(label, "source candidate label") for label in labels_payload),
        metadata=metadata_payload,
        decision=decision,
    )


def _validate_unique_candidate_ids(candidates: tuple[SourceCandidate, ...]) -> None:
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.candidate_id in seen:
            raise ValueError("candidate ids must be unique")
        seen.add(candidate.candidate_id)


def _write_json_atomic(
    *,
    path: Path,
    payload: dict[str, object],
    encoding: str,
    create_parent_dirs: bool,
) -> None:
    if create_parent_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding=encoding,
        )
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _required_str(payload: dict[str, object], key: str) -> str:
    return _require_str_value(payload.get(key), key)


def _optional_str(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    return _require_str_value(value, key)


def _require_str_value(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    return value
