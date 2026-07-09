"""Bind the existing DbApiSqlContextStore to Scheduler-managed SQL usage.

0260 replaces the 0259 demo store with discovery and binding for the existing
DbApiSqlContextStore surface.  It does not create a new SQL store, does not
start PostgreSQL, and does not turn a component smoke tool into the runtime API.

The Scheduler-owned bootstrap still routes through the capability
``sql.context.write``.  This module only discovers and constructs an existing
store object, then passes it into the 0259 Scheduler-managed usage function.

PostgreSQL lifecycle is external.  Scheduler does not start PostgreSQL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import importlib.util
import inspect
import re
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Mapping, Sequence

from context.scheduler_managed_sql_context_store_usage_0259 import (
    run_scheduler_managed_sql_context_store_usage,
)


EXCLUDED_DIR_NAMES: frozenset[str] = frozenset(
    {".git", ".var", ".mypy_cache", ".pytest_cache", "__pycache__", "patch", "build", "dist"}
)

DB_API_STORE_SYMBOL = "DbApiSqlContextStore"
DB_API_STORE_CLASS_RE = re.compile(r"^class\s+DbApiSqlContextStore\s*(?:\(|:)")


@dataclass(frozen=True)
class DbApiSqlContextStoreBindingCandidate:
    """Candidate existing DbApiSqlContextStore binding surface."""

    path: str
    module_name: str
    symbol: str = DB_API_STORE_SYMBOL
    source_kind: str = "class_definition"
    line: int = 0
    snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "module_name": self.module_name,
            "symbol": self.symbol,
            "source_kind": self.source_kind,
            "line": self.line,
            "snippet": self.snippet,
        }


@dataclass(frozen=True)
class DbApiSqlContextStoreBindingReport:
    """Discovery/binding report for existing DbApiSqlContextStore."""

    candidates: tuple[DbApiSqlContextStoreBindingCandidate, ...]
    selected_candidate: DbApiSqlContextStoreBindingCandidate | None = None
    bindable: bool = False
    constructed: bool = False
    construction_strategy: str = ""
    issues: tuple[str, ...] = field(default_factory=tuple)
    scheduler_owned: bool = True
    uses_existing_store_object: bool = True
    creates_sql_store: bool = False
    starts_postgresql: bool = False
    creates_runtime_manager: bool = False
    modifies_scheduler_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "db_api_sql_context_store_binding": True,
            "valid": not self.issues,
            "issues": list(self.issues),
            "candidate_count": len(self.candidates),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "selected_candidate": self.selected_candidate.to_dict() if self.selected_candidate else None,
            "bindable": self.bindable,
            "constructed": self.constructed,
            "construction_strategy": self.construction_strategy,
            "scheduler_owned": self.scheduler_owned,
            "uses_existing_store_object": self.uses_existing_store_object,
            "creates_sql_store": self.creates_sql_store,
            "starts_postgresql": self.starts_postgresql,
            "creates_runtime_manager": self.creates_runtime_manager,
            "modifies_scheduler_run": self.modifies_scheduler_run,
        }


@dataclass(frozen=True)
class SchedulerManagedDbApiSqlContextStoreBindingResult:
    """Result of running Scheduler-managed SQL usage with existing DbApi store."""

    binding: DbApiSqlContextStoreBindingReport
    usage: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheduler_managed_db_api_sql_context_store_binding": True,
            "valid": bool(self.binding.to_dict()["valid"]) and bool(self.usage.get("valid", False)),
            "binding": self.binding.to_dict(),
            "usage": dict(self.usage),
        }


def _is_noise_path(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return True
    if path.suffix == ".pyc":
        return True
    return False


def _module_name_for_python_file(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    if relative.parts and relative.parts[0] == "src":
        relative = Path(*relative.parts[1:])
    module_parts = relative.with_suffix("").parts
    return ".".join(module_parts)


def iter_candidate_python_files(root: Path) -> Sequence[Path]:
    """Return source Python files eligible for existing-store discovery."""

    files: list[Path] = []
    for prefix in ("src", "tools"):
        base = root / prefix
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if not _is_noise_path(path, root):
                files.append(path)
    return tuple(sorted(files))


def discover_db_api_sql_context_store_candidates(root: Path) -> tuple[DbApiSqlContextStoreBindingCandidate, ...]:
    """Discover existing DbApiSqlContextStore candidates without importing them."""

    root = root.resolve()
    candidates: list[DbApiSqlContextStoreBindingCandidate] = []
    seen: set[tuple[str, str, str]] = set()

    for path in iter_candidate_python_files(root):
        relative = str(path.relative_to(root)).replace("\\", "/")
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        for line_no, line in enumerate(lines, 1):
            stripped = line.strip()
            if DB_API_STORE_CLASS_RE.match(stripped):
                module_name = _module_name_for_python_file(path, root)
                key = (relative, module_name, "class_definition")
                if key not in seen:
                    seen.add(key)
                    candidates.append(
                        DbApiSqlContextStoreBindingCandidate(
                            path=relative,
                            module_name=module_name,
                            source_kind="class_definition",
                            line=line_no,
                            snippet=stripped[:220],
                        )
                    )
            if "import" in stripped and DB_API_STORE_SYMBOL in stripped and stripped.startswith("from "):
                module_name = stripped.split(" import ", 1)[0].replace("from ", "").strip()
                key = (relative, module_name, "import_reference")
                if key not in seen:
                    seen.add(key)
                    candidates.append(
                        DbApiSqlContextStoreBindingCandidate(
                            path=relative,
                            module_name=module_name,
                            source_kind="import_reference",
                            line=line_no,
                            snippet=stripped[:220],
                        )
                    )

    return tuple(candidates)


def _ensure_import_paths(root: Path) -> None:
    for candidate in (root / "src", root):
        text = str(candidate)
        if text not in sys.path:
            sys.path.insert(0, text)


def _load_module_from_candidate_path(
    root: Path,
    candidate: DbApiSqlContextStoreBindingCandidate,
) -> Any:
    """Load a candidate module from its file path to avoid package cache collisions."""

    module_path = root / candidate.path
    if not module_path.exists():
        raise FileNotFoundError(str(module_path))
    module_name = "_autodoc_0260_db_api_store_" + str(abs(hash((candidate.path, candidate.line))))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot build import spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def load_existing_db_api_sql_context_store_symbol(
    root: Path,
    candidate: DbApiSqlContextStoreBindingCandidate,
) -> type[Any]:
    """Import the existing DbApiSqlContextStore symbol from a selected candidate.

    Class-definition candidates are loaded by file path instead of ordinary
    import-module resolution.  This avoids collisions with an already-loaded
    ``context`` package when tests create a temporary ``src/context`` tree.
    Import-reference candidates keep the module-name fallback because the
    referenced module may be the reusable surface selected by the repository.
    """

    _ensure_import_paths(root.resolve())
    if candidate.source_kind == "class_definition":
        module = _load_module_from_candidate_path(root.resolve(), candidate)
    else:
        module = importlib.import_module(candidate.module_name)
    symbol = getattr(module, candidate.symbol)
    if not inspect.isclass(symbol):
        raise TypeError(f"{candidate.module_name}.{candidate.symbol} is not a class")
    return symbol


def select_db_api_sql_context_store_candidate(
    candidates: Sequence[DbApiSqlContextStoreBindingCandidate],
) -> DbApiSqlContextStoreBindingCandidate | None:
    """Select the best candidate, preferring class definitions under src/."""

    if not candidates:
        return None
    preferred = sorted(
        candidates,
        key=lambda item: (
            item.source_kind != "class_definition",
            not item.path.startswith("src/"),
            "test" in item.path,
            item.path,
            item.line,
        ),
    )
    return preferred[0]


def construct_existing_db_api_sql_context_store(
    store_class: type[Any],
    *,
    db_path: Path | None = None,
    connection: Any | None = None,
) -> tuple[Any, str]:
    """Construct an existing DbApiSqlContextStore using conservative strategies.

    The strategies are intentionally generic because the existing class owns its
    constructor contract.  0260 does not alter that contract.
    """

    errors: list[str] = []
    if connection is not None:
        for strategy, kwargs in (
            ("keyword_connection", {"connection": connection}),
            ("keyword_db", {"db": connection}),
        ):
            try:
                return store_class(**kwargs), strategy
            except TypeError as exc:
                errors.append(f"{strategy}: {exc}")
        try:
            return store_class(connection), "positional_connection"
        except TypeError as exc:
            errors.append(f"positional_connection: {exc}")

    if db_path is not None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(db_path))
        for strategy, kwargs in (
            ("keyword_connection_sqlite", {"connection": connection}),
            ("keyword_db_sqlite", {"db": connection}),
        ):
            try:
                return store_class(**kwargs), strategy
            except TypeError as exc:
                errors.append(f"{strategy}: {exc}")
        try:
            return store_class(connection), "positional_sqlite_connection"
        except TypeError as exc:
            errors.append(f"positional_sqlite_connection: {exc}")
        for strategy, kwargs in (
            ("keyword_db_path", {"db_path": str(db_path)}),
            ("keyword_path", {"path": str(db_path)}),
        ):
            try:
                return store_class(**kwargs), strategy
            except TypeError as exc:
                errors.append(f"{strategy}: {exc}")

    try:
        return store_class(), "no_arg_constructor"
    except TypeError as exc:
        errors.append(f"no_arg_constructor: {exc}")

    raise TypeError("; ".join(errors))


def build_db_api_sql_context_store_binding_report(
    root: Path,
    *,
    db_path: Path | None = None,
    construct: bool = False,
) -> tuple[DbApiSqlContextStoreBindingReport, object | None]:
    """Discover and optionally construct the existing DbApiSqlContextStore."""

    candidates = discover_db_api_sql_context_store_candidates(root)
    selected = select_db_api_sql_context_store_candidate(candidates)
    if selected is None:
        return (
            DbApiSqlContextStoreBindingReport(
                candidates=candidates,
                issues=("existing DbApiSqlContextStore candidate not found",),
            ),
            None,
        )

    try:
        store_class = load_existing_db_api_sql_context_store_symbol(root, selected)
    except Exception as exc:  # noqa: BLE001
        return (
            DbApiSqlContextStoreBindingReport(
                candidates=candidates,
                selected_candidate=selected,
                bindable=False,
                issues=(f"failed to import existing DbApiSqlContextStore: {exc}",),
            ),
            None,
        )

    if not construct:
        return (
            DbApiSqlContextStoreBindingReport(
                candidates=candidates,
                selected_candidate=selected,
                bindable=True,
                constructed=False,
            ),
            None,
        )

    try:
        store, strategy = construct_existing_db_api_sql_context_store(store_class, db_path=db_path)
    except Exception as exc:  # noqa: BLE001
        return (
            DbApiSqlContextStoreBindingReport(
                candidates=candidates,
                selected_candidate=selected,
                bindable=True,
                constructed=False,
                issues=(f"failed to construct existing DbApiSqlContextStore: {exc}",),
            ),
            None,
        )

    return (
        DbApiSqlContextStoreBindingReport(
            candidates=candidates,
            selected_candidate=selected,
            bindable=True,
            constructed=True,
            construction_strategy=strategy,
        ),
        store,
    )


def run_scheduler_managed_db_api_sql_context_store_binding(
    root: Path,
    bootstrap_payload: Mapping[str, Any],
    *,
    text: str,
    execute: bool = False,
    policy_decision_id: str = "",
    db_path: Path | None = None,
) -> SchedulerManagedDbApiSqlContextStoreBindingResult:
    """Run Scheduler-managed SQL usage through the existing DbApiSqlContextStore."""

    binding, store = build_db_api_sql_context_store_binding_report(
        root,
        db_path=db_path,
        construct=execute,
    )
    if binding.issues:
        usage = {
            "valid": False,
            "issues": list(binding.issues),
            "execute": execute,
            "dry_run": not execute,
        }
        return SchedulerManagedDbApiSqlContextStoreBindingResult(binding=binding, usage=usage)

    usage_result = run_scheduler_managed_sql_context_store_usage(
        bootstrap_payload,
        text=text,
        execute=execute,
        policy_decision_id=policy_decision_id,
        store=store,
        metadata={"binding_candidate": binding.selected_candidate.to_dict() if binding.selected_candidate else {}},
    )
    return SchedulerManagedDbApiSqlContextStoreBindingResult(
        binding=binding,
        usage=usage_result.to_dict(),
    )


def load_json_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_scheduler_managed_db_api_sql_context_store_binding_report(
    output: Path,
    root: Path,
    bootstrap_payload: Mapping[str, Any],
    *,
    text: str,
    execute: bool = False,
    policy_decision_id: str = "",
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Write a Scheduler-managed DbApiSqlContextStore binding report."""

    result = run_scheduler_managed_db_api_sql_context_store_binding(
        root,
        bootstrap_payload,
        text=text,
        execute=execute,
        policy_decision_id=policy_decision_id,
        db_path=db_path,
    )
    payload = result.to_dict()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
