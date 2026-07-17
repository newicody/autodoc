"""Pure local ownership and drift audit for the Projects repository bundle."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

PROJECTS_BUNDLE_MANIFEST_SCHEMA = "missipy.projects_bundle_manifest.v1"
PROJECTS_BUNDLE_DRIFT_RESULT_SCHEMA = (
    "missipy.projects_bundle_drift_audit_result.v1"
)
TRANSIENT_PYTHON_DIRECTORY_NAMES = frozenset({"__pycache__"})
TRANSIENT_PYTHON_FILE_SUFFIXES = frozenset({".pyc", ".pyo"})


class ProjectsBundleManifestError(ValueError):
    """Raised when a bundle ownership manifest is invalid."""


@dataclass(frozen=True, slots=True)
class ManagedBundleEntry:
    """One active source-to-destination file owned by Autodoc."""

    source_path: str
    destination_path: str
    role: str
    managed_by: str

    def __post_init__(self) -> None:
        _validate_relative_path(self.source_path, "source_path")
        _validate_relative_path(self.destination_path, "destination_path")
        if not self.role.strip():
            raise ProjectsBundleManifestError("entry role must be non-empty")
        if self.managed_by != "newicody/autodoc":
            raise ProjectsBundleManifestError(
                "active entry must be managed by newicody/autodoc"
            )


@dataclass(frozen=True, slots=True)
class RetiredBundleEntry:
    """One previously managed destination path safe to propose for deletion."""

    destination_path: str
    role: str
    managed_by: str
    reason: str

    def __post_init__(self) -> None:
        _validate_relative_path(self.destination_path, "destination_path")
        if self.managed_by != "newicody/autodoc":
            raise ProjectsBundleManifestError(
                "retired entry must be managed by newicody/autodoc"
            )
        if not self.reason.strip():
            raise ProjectsBundleManifestError(
                "retired entry reason must be non-empty"
            )


@dataclass(frozen=True, slots=True)
class ProjectsBundleManifest:
    """Versioned ownership boundary for files copied into newicody/projects."""

    schema: str
    bundle_ref: str
    bundle_version: str
    source_repository: str
    destination_repository: str
    managed_roots: tuple[str, ...]
    entries: tuple[ManagedBundleEntry, ...]
    retired_entries: tuple[RetiredBundleEntry, ...]
    ownership_policy: Mapping[str, object]

    def __post_init__(self) -> None:
        if self.schema != PROJECTS_BUNDLE_MANIFEST_SCHEMA:
            raise ProjectsBundleManifestError("unsupported manifest schema")
        if not self.bundle_ref.startswith("projects-bundle:"):
            raise ProjectsBundleManifestError(
                "bundle_ref must be a typed projects-bundle reference"
            )
        if self.source_repository != "newicody/autodoc":
            raise ProjectsBundleManifestError(
                "source repository must remain newicody/autodoc"
            )
        if self.destination_repository != "newicody/projects":
            raise ProjectsBundleManifestError(
                "destination repository must remain newicody/projects"
            )
        for root in self.managed_roots:
            _validate_relative_path(root, "managed_root")
        sources = tuple(item.source_path for item in self.entries)
        destinations = tuple(item.destination_path for item in self.entries)
        retired = tuple(item.destination_path for item in self.retired_entries)
        if len(set(sources)) != len(sources):
            raise ProjectsBundleManifestError(
                "active source paths must be unique"
            )
        if len(set(destinations)) != len(destinations):
            raise ProjectsBundleManifestError(
                "active destination paths must be unique"
            )
        if len(set(retired)) != len(retired):
            raise ProjectsBundleManifestError(
                "retired destination paths must be unique"
            )
        overlap = sorted(set(destinations).intersection(retired))
        if overlap:
            raise ProjectsBundleManifestError(
                f"active and retired paths overlap: {overlap}"
            )
        if self.ownership_policy.get("safe_delete_scope") != (
            "retired_entries-only"
        ):
            raise ProjectsBundleManifestError(
                "safe deletion must remain limited to retired entries"
            )
        if self.ownership_policy.get("rsync_delete_allowed") is not False:
            raise ProjectsBundleManifestError(
                "rsync --delete must remain forbidden"
            )


@dataclass(frozen=True, slots=True)
class ProjectsBundleDriftAuditCommand:
    """Typed local filesystem audit request."""

    source_root: Path
    destination_root: Path
    manifest_path: Path

    def __post_init__(self) -> None:
        if not self.source_root.is_dir():
            raise ProjectsBundleManifestError(
                f"source root is absent: {self.source_root}"
            )
        if not self.destination_root.is_dir():
            raise ProjectsBundleManifestError(
                f"destination root is absent: {self.destination_root}"
            )
        if not self.manifest_path.is_file():
            raise ProjectsBundleManifestError(
                f"manifest is absent: {self.manifest_path}"
            )


@dataclass(frozen=True, slots=True)
class ProjectsBundleDriftAuditPolicy:
    """Explicit bounds and non-destructive audit policy."""

    max_manifest_entries: int = 256
    max_unknown_files: int = 1024
    scan_unknown_extras: bool = True
    allow_mutation: bool = False

    def __post_init__(self) -> None:
        if self.max_manifest_entries <= 0:
            raise ProjectsBundleManifestError(
                "max_manifest_entries must be positive"
            )
        if self.max_unknown_files <= 0:
            raise ProjectsBundleManifestError(
                "max_unknown_files must be positive"
            )
        if self.allow_mutation:
            raise ProjectsBundleManifestError(
                "bundle drift audit is read-only"
            )


@dataclass(frozen=True, slots=True)
class BundleFileAudit:
    """One immutable active file comparison."""

    source_path: str
    destination_path: str
    role: str
    status: str
    source_sha256: str | None
    destination_sha256: str | None

    def to_mapping(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "role": self.role,
            "status": self.status,
            "source_sha256": self.source_sha256,
            "destination_sha256": self.destination_sha256,
        }


@dataclass(frozen=True, slots=True)
class RetiredFileAudit:
    """One immutable retired file readback."""

    destination_path: str
    role: str
    reason: str
    status: str
    destination_sha256: str | None

    def to_mapping(self) -> dict[str, object]:
        return {
            "destination_path": self.destination_path,
            "role": self.role,
            "reason": self.reason,
            "status": self.status,
            "destination_sha256": self.destination_sha256,
            "safe_delete_candidate": self.status == "obsolete_managed",
        }


@dataclass(frozen=True, slots=True)
class ProjectsBundleDriftAuditResult:
    """Stable read-only drift report and operator review plan."""

    schema: str
    bundle_ref: str
    bundle_version: str
    manifest_digest: str
    plan_digest: str
    active_files: tuple[BundleFileAudit, ...]
    retired_files: tuple[RetiredFileAudit, ...]
    unknown_extra_files: tuple[str, ...]
    ignored_transient_files: tuple[str, ...]
    copy_candidates: tuple[str, ...]
    safe_delete_candidates: tuple[str, ...]
    source_valid: bool
    managed_exact: bool
    review_required: bool
    mutation_performed: bool = False
    remote_access_performed: bool = False

    def __post_init__(self) -> None:
        if self.schema != PROJECTS_BUNDLE_DRIFT_RESULT_SCHEMA:
            raise ProjectsBundleManifestError(
                "unsupported audit result schema"
            )
        if self.mutation_performed or self.remote_access_performed:
            raise ProjectsBundleManifestError(
                "drift audit must remain local and read-only"
            )
        safe_status_paths = {
            item.destination_path
            for item in self.retired_files
            if item.status == "obsolete_managed"
        }
        if set(self.safe_delete_candidates) != safe_status_paths:
            raise ProjectsBundleManifestError(
                "safe delete candidates must be retired managed paths only"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "bundle_ref": self.bundle_ref,
            "bundle_version": self.bundle_version,
            "manifest_digest": self.manifest_digest,
            "plan_digest": self.plan_digest,
            "active_files": [
                item.to_mapping() for item in self.active_files
            ],
            "retired_files": [
                item.to_mapping() for item in self.retired_files
            ],
            "unknown_extra_files": list(self.unknown_extra_files),
            "ignored_transient_files": list(
                self.ignored_transient_files
            ),
            "copy_candidates": list(self.copy_candidates),
            "safe_delete_candidates": list(
                self.safe_delete_candidates
            ),
            "source_valid": self.source_valid,
            "managed_exact": self.managed_exact,
            "review_required": self.review_required,
            "boundaries": {
                "mutation_performed": self.mutation_performed,
                "remote_access_performed": self.remote_access_performed,
                "unknown_extra_files_are_delete_candidates": False,
                "transient_python_artifacts_ignored": True,
                "transient_python_directory_names": sorted(
                    TRANSIENT_PYTHON_DIRECTORY_NAMES
                ),
                "transient_python_file_suffixes": sorted(
                    TRANSIENT_PYTHON_FILE_SUFFIXES
                ),
                "safe_delete_scope": "retired_entries-only",
                "rsync_delete_allowed": False,
            },
        }

    def to_summary(self) -> str:
        counts: dict[str, int] = {}
        for item in self.active_files:
            counts[item.status] = counts.get(item.status, 0) + 1
        for item in self.retired_files:
            counts[item.status] = counts.get(item.status, 0) + 1
        rendered = ", ".join(
            f"{name}={counts[name]}" for name in sorted(counts)
        )
        return "\n".join(
            (
                f"bundle: {self.bundle_ref}",
                f"version: {self.bundle_version}",
                f"managed_exact: {str(self.managed_exact).lower()}",
                f"review_required: {str(self.review_required).lower()}",
                f"states: {rendered or 'none'}",
                (
                    "unknown_extra_files: "
                    f"{len(self.unknown_extra_files)}"
                ),
                (
                    "ignored_transient_files: "
                    f"{len(self.ignored_transient_files)}"
                ),
                (
                    "safe_delete_candidates: "
                    f"{len(self.safe_delete_candidates)}"
                ),
                f"plan_digest: {self.plan_digest}",
            )
        )


def load_projects_bundle_manifest(path: Path) -> ProjectsBundleManifest:
    """Load and validate one versioned bundle ownership manifest."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ProjectsBundleManifestError(
            "manifest root must be a JSON object"
        )
    entries_raw = raw.get("entries")
    retired_raw = raw.get("retired_entries")
    if not isinstance(entries_raw, Sequence) or isinstance(
        entries_raw, (str, bytes)
    ):
        raise ProjectsBundleManifestError(
            "manifest entries must be a sequence"
        )
    if not isinstance(retired_raw, Sequence) or isinstance(
        retired_raw, (str, bytes)
    ):
        raise ProjectsBundleManifestError(
            "retired_entries must be a sequence"
        )
    ownership = raw.get("ownership_policy")
    if not isinstance(ownership, Mapping):
        raise ProjectsBundleManifestError(
            "ownership_policy must be an object"
        )
    roots = raw.get("managed_roots")
    if not isinstance(roots, Sequence) or isinstance(
        roots, (str, bytes)
    ):
        raise ProjectsBundleManifestError(
            "managed_roots must be a sequence"
        )

    entries = tuple(
        ManagedBundleEntry(
            source_path=_required_text(item, "source_path"),
            destination_path=_required_text(
                item, "destination_path"
            ),
            role=_required_text(item, "role"),
            managed_by=_required_text(item, "managed_by"),
        )
        for item in entries_raw
        if isinstance(item, Mapping)
    )
    if len(entries) != len(entries_raw):
        raise ProjectsBundleManifestError(
            "every active entry must be an object"
        )
    retired = tuple(
        RetiredBundleEntry(
            destination_path=_required_text(
                item, "destination_path"
            ),
            role=_required_text(item, "role"),
            managed_by=_required_text(item, "managed_by"),
            reason=_required_text(item, "reason"),
        )
        for item in retired_raw
        if isinstance(item, Mapping)
    )
    if len(retired) != len(retired_raw):
        raise ProjectsBundleManifestError(
            "every retired entry must be an object"
        )

    return ProjectsBundleManifest(
        schema=_required_text(raw, "schema"),
        bundle_ref=_required_text(raw, "bundle_ref"),
        bundle_version=_required_text(raw, "bundle_version"),
        source_repository=_required_text(raw, "source_repository"),
        destination_repository=_required_text(
            raw, "destination_repository"
        ),
        managed_roots=tuple(str(value) for value in roots),
        entries=entries,
        retired_entries=retired,
        ownership_policy=MappingProxyType(dict(ownership)),
    )


def audit_projects_bundle_drift(
    command: ProjectsBundleDriftAuditCommand,
    *,
    policy: ProjectsBundleDriftAuditPolicy | None = None,
) -> ProjectsBundleDriftAuditResult:
    """Compare managed files without changing either repository."""

    effective = policy or ProjectsBundleDriftAuditPolicy()
    manifest = load_projects_bundle_manifest(command.manifest_path)
    if len(manifest.entries) > effective.max_manifest_entries:
        raise ProjectsBundleManifestError(
            "manifest entry count exceeds the explicit audit bound"
        )

    active_audits = tuple(
        _audit_active_entry(
            command.source_root,
            command.destination_root,
            entry,
        )
        for entry in manifest.entries
    )
    retired_audits = tuple(
        _audit_retired_entry(command.destination_root, entry)
        for entry in manifest.retired_entries
    )
    known_destinations = {
        item.destination_path for item in manifest.entries
    }.union(
        item.destination_path for item in manifest.retired_entries
    )
    if effective.scan_unknown_extras:
        unknown, ignored_transient = _scan_unknown_extra_files(
            command.destination_root,
            manifest.managed_roots,
            known_destinations,
            effective.max_unknown_files,
        )
    else:
        unknown, ignored_transient = (), ()

    copy_candidates = tuple(
        item.destination_path
        for item in active_audits
        if item.status in {"destination_missing", "modified"}
    )
    safe_delete_candidates = tuple(
        item.destination_path
        for item in retired_audits
        if item.status == "obsolete_managed"
    )
    source_valid = all(
        item.status != "source_missing" for item in active_audits
    )
    managed_exact = (
        source_valid
        and all(item.status == "identical" for item in active_audits)
        and not safe_delete_candidates
    )
    review_required = bool(
        copy_candidates or safe_delete_candidates or unknown
    )

    manifest_digest = _sha256(command.manifest_path)
    plan_payload = {
        "bundle_ref": manifest.bundle_ref,
        "bundle_version": manifest.bundle_version,
        "copy_candidates": list(copy_candidates),
        "safe_delete_candidates": list(safe_delete_candidates),
        "unknown_extra_files": list(unknown),
    }
    plan_digest = "sha256:" + hashlib.sha256(
        json.dumps(
            plan_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()

    return ProjectsBundleDriftAuditResult(
        schema=PROJECTS_BUNDLE_DRIFT_RESULT_SCHEMA,
        bundle_ref=manifest.bundle_ref,
        bundle_version=manifest.bundle_version,
        manifest_digest=manifest_digest,
        plan_digest=plan_digest,
        active_files=active_audits,
        retired_files=retired_audits,
        unknown_extra_files=unknown,
        ignored_transient_files=ignored_transient,
        copy_candidates=copy_candidates,
        safe_delete_candidates=safe_delete_candidates,
        source_valid=source_valid,
        managed_exact=managed_exact,
        review_required=review_required,
    )


def _audit_active_entry(
    source_root: Path,
    destination_root: Path,
    entry: ManagedBundleEntry,
) -> BundleFileAudit:
    source = _resolve_child(source_root, entry.source_path)
    destination = _resolve_child(
        destination_root, entry.destination_path
    )
    if not source.is_file():
        return BundleFileAudit(
            source_path=entry.source_path,
            destination_path=entry.destination_path,
            role=entry.role,
            status="source_missing",
            source_sha256=None,
            destination_sha256=(
                _sha256(destination) if destination.is_file() else None
            ),
        )
    source_digest = _sha256(source)
    if not destination.is_file():
        return BundleFileAudit(
            source_path=entry.source_path,
            destination_path=entry.destination_path,
            role=entry.role,
            status="destination_missing",
            source_sha256=source_digest,
            destination_sha256=None,
        )
    destination_digest = _sha256(destination)
    return BundleFileAudit(
        source_path=entry.source_path,
        destination_path=entry.destination_path,
        role=entry.role,
        status=(
            "identical"
            if source_digest == destination_digest
            else "modified"
        ),
        source_sha256=source_digest,
        destination_sha256=destination_digest,
    )


def _audit_retired_entry(
    destination_root: Path,
    entry: RetiredBundleEntry,
) -> RetiredFileAudit:
    destination = _resolve_child(
        destination_root, entry.destination_path
    )
    if destination.is_file():
        return RetiredFileAudit(
            destination_path=entry.destination_path,
            role=entry.role,
            reason=entry.reason,
            status="obsolete_managed",
            destination_sha256=_sha256(destination),
        )
    return RetiredFileAudit(
        destination_path=entry.destination_path,
        role=entry.role,
        reason=entry.reason,
        status="retired_absent",
        destination_sha256=None,
    )


def _scan_unknown_extra_files(
    destination_root: Path,
    managed_roots: tuple[str, ...],
    known_destinations: set[str],
    maximum: int,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    extras: list[str] = []
    ignored_transient: list[str] = []
    for root_text in managed_roots:
        root = _resolve_child(destination_root, root_text)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(destination_root).as_posix()
            if relative in known_destinations:
                continue
            if _is_transient_python_artifact(path):
                ignored_transient.append(relative)
                continue
            extras.append(relative)
            if len(extras) > maximum:
                raise ProjectsBundleManifestError(
                    "unknown file count exceeds the explicit audit bound"
                )
    return tuple(extras), tuple(ignored_transient)


def _is_transient_python_artifact(path: Path) -> bool:
    return (
        bool(
            TRANSIENT_PYTHON_DIRECTORY_NAMES.intersection(
                path.parts
            )
        )
        or path.suffix.casefold() in TRANSIENT_PYTHON_FILE_SUFFIXES
    )


def _required_text(
    mapping: Mapping[str, Any],
    key: str,
) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProjectsBundleManifestError(
            f"{key} must be a non-empty string"
        )
    return value.strip()


def _validate_relative_path(value: str, field_name: str) -> None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or value.strip() != value:
        raise ProjectsBundleManifestError(
            f"{field_name} must be a normalized relative path"
        )
    if value in {"", "."}:
        raise ProjectsBundleManifestError(
            f"{field_name} must identify a file or managed directory"
        )


def _resolve_child(root: Path, relative: str) -> Path:
    _validate_relative_path(relative, "relative_path")
    root_resolved = root.resolve()
    candidate = (root_resolved / relative).resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ProjectsBundleManifestError(
            "resolved path escaped the declared repository root"
        )
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


__all__ = (
    "PROJECTS_BUNDLE_DRIFT_RESULT_SCHEMA",
    "PROJECTS_BUNDLE_MANIFEST_SCHEMA",
    "TRANSIENT_PYTHON_DIRECTORY_NAMES",
    "TRANSIENT_PYTHON_FILE_SUFFIXES",
    "BundleFileAudit",
    "ManagedBundleEntry",
    "ProjectsBundleDriftAuditCommand",
    "ProjectsBundleDriftAuditPolicy",
    "ProjectsBundleDriftAuditResult",
    "ProjectsBundleManifest",
    "ProjectsBundleManifestError",
    "RetiredBundleEntry",
    "RetiredFileAudit",
    "audit_projects_bundle_drift",
    "load_projects_bundle_manifest",
)
