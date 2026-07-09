"""Scheduler-owned runtime reuse source map.

0255 proved that all required surfaces exist, but the first audit intentionally
searched broadly and therefore included reports, docs, and chat history.  This
module builds a narrower source map that points at reusable implementation
surfaces before Scheduler-owned runtime adaptation starts.

The map is read-only and stdlib-only.  It does not import target modules,
instantiate components, call Scheduler.run, connect to PostgreSQL, run OpenVINO,
call Qdrant, call GitHub, or publish EventBus messages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


EXCLUDED_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".var",
        ".mypy_cache",
        ".pytest_cache",
        "__pycache__",
        "patch",
        "build",
        "dist",
    }
)

EXCLUDED_FILE_PREFIXES: tuple[str, ...] = (
    "PHASE",
)

EXCLUDED_FILE_NAMES: frozenset[str] = frozenset(
    {
        ".aider.chat.history.md",
    }
)

SOURCE_ROOT_PREFIXES: tuple[str, ...] = (
    "src/",
    "tools/",
    "tests/",
)

SURFACE_DEFINITIONS: dict[str, dict[str, tuple[str, ...]]] = {
    "scheduler": {
        "preferred_paths": (
            "src/kernel/scheduler.py",
            "src/contracts/scheduler.py",
        ),
        "markers": (
            "class Scheduler",
            "Scheduler",
            "scheduler",
        ),
    },
    "eventbus": {
        "preferred_paths": (
            "src/kernel/event_bus.py",
        ),
        "markers": (
            "EventBus",
            "event_bus",
            "publish",
            "subscribe",
        ),
    },
    "passive_supervisor": {
        "preferred_paths": (
            "src/context/passive_supervisor",
            "tools/run_passive_supervisor",
        ),
        "markers": (
            "PassiveSupervisorSink",
            "passive_supervisor",
            "CellularState",
            "cellular_snapshot",
        ),
    },
    "sql_context_store": {
        "preferred_paths": (
            "src/context/db_api_sql_context_store.py",
            "tools/run_sql_context_store_controlled_write_smoke.py",
        ),
        "markers": (
            "DbApiSqlContextStore",
            "controlled_write",
            "context_records",
            "sql_ref",
        ),
    },
    "openvino_embedding": {
        "preferred_paths": (
            "tools/embed_e5.py",
            "tools/run_openvino",
            "src/context/openvino",
        ),
        "markers": (
            "OpenVINO",
            "openvino",
            "multilingual-e5-small",
            "embed_query",
            "embed_passage",
        ),
    },
    "qdrant_projection": {
        "preferred_paths": (
            "tools/run_qdrant",
            "tools/run_qdrant_projection",
            "src/context/qdrant",
        ),
        "markers": (
            "Qdrant",
            "qdrant",
            "sql_ref",
            "qdrant_ref",
        ),
    },
    "github_artifact_exchange": {
        "preferred_paths": (
            "src/context/github",
            "tools/run_github",
            "tools/build_github",
        ),
        "markers": (
            "ProjectPushFrame",
            "GitHubArtifact",
            "github_artifact",
            "GITHUB_TOKEN",
        ),
    },
}


@dataclass(frozen=True)
class SourceSurfaceHit:
    """One implementation-source hit for a reusable runtime surface."""

    path: str
    line: int
    marker: str
    snippet: str
    preferred: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "line": self.line,
            "marker": self.marker,
            "snippet": self.snippet,
            "preferred": self.preferred,
        }


@dataclass(frozen=True)
class SourceSurfaceSelection:
    """Selected reusable source files for one surface."""

    surface: str
    primary_paths: tuple[str, ...] = field(default_factory=tuple)
    hits: tuple[SourceSurfaceHit, ...] = field(default_factory=tuple)
    missing: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "primary_paths": list(self.primary_paths),
            "hit_count": len(self.hits),
            "missing": self.missing,
            "hits": [hit.to_dict() for hit in self.hits],
        }


@dataclass(frozen=True)
class SchedulerOwnedRuntimeReuseSourceMap:
    """Filtered source map used before Scheduler-owned runtime adaptation."""

    selections: tuple[SourceSurfaceSelection, ...]
    excluded_noise: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        missing = tuple(selection.surface for selection in self.selections if selection.missing)
        return {
            "scheduler_owned_runtime_reuse_source_map": True,
            "read_only": self.read_only,
            "audit_first_adapt_second": True,
            "scheduler_owns_runtime_components": True,
            "no_cli_per_component": True,
            "selection_count": len(self.selections),
            "missing_surfaces": list(missing),
            "complete": not missing,
            "excluded_noise": dict(self.excluded_noise),
            "selections": [selection.to_dict() for selection in self.selections],
        }


def _is_noise_path(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    parts = relative.parts
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return True
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    if any(path.name.startswith(prefix) for prefix in EXCLUDED_FILE_PREFIXES):
        return True
    if path.suffix == ".pyc":
        return True
    return False


def _is_source_path(path: Path, root: Path) -> bool:
    relative_text = str(path.relative_to(root)).replace("\\", "/")
    return relative_text.startswith(SOURCE_ROOT_PREFIXES)


def iter_runtime_source_files(root: Path) -> Iterable[Path]:
    """Yield implementation source files only, excluding reports/docs/history."""

    suffixes = {".py", ".pyi", ".toml", ".ini", ".json"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if _is_noise_path(path, root):
            continue
        if not _is_source_path(path, root):
            continue
        if path.suffix.lower() in suffixes:
            yield path


def _preferred_match(relative_path: str, preferred_paths: Sequence[str]) -> bool:
    normalized = relative_path.replace("\\", "/")
    return any(normalized == preferred or normalized.startswith(preferred.rstrip("/") + "/") or normalized.startswith(preferred) for preferred in preferred_paths)


def _scan_surface(
    root: Path,
    surface: str,
    definition: Mapping[str, Sequence[str]],
) -> SourceSurfaceSelection:
    markers = tuple(definition.get("markers", ()))
    preferred_paths = tuple(definition.get("preferred_paths", ()))
    hits: list[SourceSurfaceHit] = []
    primary_paths: set[str] = set()

    for path in iter_runtime_source_files(root):
        relative = str(path.relative_to(root)).replace("\\", "/")
        preferred = _preferred_match(relative, preferred_paths)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for marker in markers:
                if marker and marker in line:
                    hits.append(
                        SourceSurfaceHit(
                            path=relative,
                            line=line_no,
                            marker=marker,
                            snippet=line.strip()[:220],
                            preferred=preferred,
                        )
                    )
                    primary_paths.add(relative)
                    break

    sorted_hits = tuple(
        sorted(
            hits,
            key=lambda hit: (not hit.preferred, hit.path, hit.line, hit.marker),
        )[:25]
    )
    primary = tuple(
        sorted(
            primary_paths,
            key=lambda item: (not _preferred_match(item, preferred_paths), item),
        )[:8]
    )
    return SourceSurfaceSelection(
        surface=surface,
        primary_paths=primary,
        hits=sorted_hits,
        missing=not bool(primary),
    )


def build_scheduler_owned_runtime_reuse_source_map(root: Path) -> SchedulerOwnedRuntimeReuseSourceMap:
    """Build a filtered map of existing source surfaces to reuse."""

    root = root.resolve()
    selections = tuple(
        _scan_surface(root, surface, definition)
        for surface, definition in SURFACE_DEFINITIONS.items()
    )
    excluded_noise = {
        "excluded_dirs": sorted(EXCLUDED_DIR_NAMES),
        "excluded_file_names": sorted(EXCLUDED_FILE_NAMES),
        "excluded_file_prefixes": list(EXCLUDED_FILE_PREFIXES),
        "source_root_prefixes": list(SOURCE_ROOT_PREFIXES),
        "phase_reports_excluded": True,
        "docs_excluded_from_source_selection": True,
        "aider_history_excluded": True,
    }
    return SchedulerOwnedRuntimeReuseSourceMap(
        selections=selections,
        excluded_noise=excluded_noise,
    )


def write_scheduler_owned_runtime_reuse_source_map_report(root: Path, output: Path) -> dict[str, Any]:
    """Write the source map report."""

    source_map = build_scheduler_owned_runtime_reuse_source_map(root)
    payload = source_map.to_dict()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
