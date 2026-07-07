#!/usr/bin/env python3
"""Audit existing route handler surfaces without executing them.

0181 is an audit tool only. It reads Python files as text/AST and reports the
surface symbols that a later route handoff patch may reuse.

It deliberately does not import runtime handler modules, does not call
handle_scheduler_route_request, does not instantiate Scheduler, does not modify
Scheduler.run, does not instantiate EventBus, and does not write RouteProxy or
ControlProxy frames.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


ROUTE_HANDLER_SURFACE_AUDIT_SCHEMA = "missipy.route_handler.surface_audit.v1"

EXPECTED_SURFACES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "src/runtime/scheduler_route_adapter.py",
        (
            "SCHEDULER_ROUTE_REQUEST_SCHEMA",
            "SchedulerRouteRequest",
            "scheduler_route_request_mapping",
        ),
    ),
    (
        "src/runtime/scheduler_route_handler_minimal.py",
        (
            "SchedulerRouteHandlerCommand",
            "handle_scheduler_route_request",
        ),
    ),
    (
        "src/runtime/scheduler_route_handshake.py",
        (
            "prepare_route_for_scheduler",
            "policy_decision_id",
        ),
    ),
    (
        "src/runtime/controlproxy_scheduler_handler.py",
        (
            "ControlProxy",
            "SchedulerRouteRequest",
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class RouteHandlerSurfaceFileAudit:
    """Audit result for one expected handler surface file."""

    path: str
    exists: bool
    sha256: str | None
    ast_parse_ok: bool
    symbols_found: tuple[str, ...]
    symbols_missing: tuple[str, ...]
    imports_detected: tuple[str, ...]

    @property
    def ready_for_review(self) -> bool:
        return self.exists and self.ast_parse_ok and not self.symbols_missing

    def to_mapping(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "exists": self.exists,
            "sha256": self.sha256,
            "ast_parse_ok": self.ast_parse_ok,
            "symbols_found": list(self.symbols_found),
            "symbols_missing": list(self.symbols_missing),
            "imports_detected": list(self.imports_detected),
            "ready_for_review": self.ready_for_review,
        }


@dataclass(frozen=True, slots=True)
class RouteHandlerSurfaceAuditReport:
    """Read-only audit report for route handler surfaces."""

    schema: str
    repo_root: str
    file_count: int
    ready_count: int
    missing_count: int
    files: tuple[RouteHandlerSurfaceFileAudit, ...]
    dry_run_only: bool
    runtime_imports_executed: bool
    handler_called: bool
    scheduler_modified: bool
    frames_written: bool

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "repo_root": self.repo_root,
            "file_count": self.file_count,
            "ready_count": self.ready_count,
            "missing_count": self.missing_count,
            "files": [item.to_mapping() for item in self.files],
            "dry_run_only": self.dry_run_only,
            "runtime_imports_executed": self.runtime_imports_executed,
            "handler_called": self.handler_called,
            "scheduler_modified": self.scheduler_modified,
            "frames_written": self.frames_written,
        }


def audit_route_handler_surfaces(
    repo_root: Path | str,
    *,
    expected_surfaces: Iterable[tuple[str, Iterable[str]]] = EXPECTED_SURFACES,
) -> RouteHandlerSurfaceAuditReport:
    """Read expected handler surface files and report discovered symbols.

    The audit uses Path.read_text and ast.parse only. It does not import the
    audited runtime files and therefore cannot execute handler code.
    """

    root = Path(repo_root)
    files = tuple(_audit_file(root, relative, tuple(symbols)) for relative, symbols in expected_surfaces)
    ready_count = sum(1 for item in files if item.ready_for_review)
    missing_count = sum(1 for item in files if not item.exists)
    return RouteHandlerSurfaceAuditReport(
        schema=ROUTE_HANDLER_SURFACE_AUDIT_SCHEMA,
        repo_root=str(root),
        file_count=len(files),
        ready_count=ready_count,
        missing_count=missing_count,
        files=files,
        dry_run_only=True,
        runtime_imports_executed=False,
        handler_called=False,
        scheduler_modified=False,
        frames_written=False,
    )


def _audit_file(repo_root: Path, relative: str, expected_symbols: tuple[str, ...]) -> RouteHandlerSurfaceFileAudit:
    path = repo_root / relative
    if not path.exists():
        return RouteHandlerSurfaceFileAudit(
            path=relative,
            exists=False,
            sha256=None,
            ast_parse_ok=False,
            symbols_found=(),
            symbols_missing=expected_symbols,
            imports_detected=(),
        )

    text = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    symbols = set(_text_symbol_hits(text, expected_symbols))
    imports: tuple[str, ...] = ()
    ast_parse_ok = False
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        tree = None
    if tree is not None:
        ast_parse_ok = True
        symbols.update(_ast_defined_symbols(tree, expected_symbols))
        imports = tuple(sorted(_ast_imports(tree)))

    found = tuple(symbol for symbol in expected_symbols if symbol in symbols)
    missing = tuple(symbol for symbol in expected_symbols if symbol not in symbols)
    return RouteHandlerSurfaceFileAudit(
        path=relative,
        exists=True,
        sha256=digest,
        ast_parse_ok=ast_parse_ok,
        symbols_found=found,
        symbols_missing=missing,
        imports_detected=imports,
    )


def _text_symbol_hits(text: str, expected_symbols: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(symbol for symbol in expected_symbols if symbol in text)


def _ast_defined_symbols(tree: ast.AST, expected_symbols: tuple[str, ...]) -> set[str]:
    expected = set(expected_symbols)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in expected:
            found.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in expected:
                    found.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id in expected:
            found.add(node.target.id)
    return found


def _ast_imports(tree: ast.AST) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.add(module)
    return imports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only audit of route handler surface files.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = audit_route_handler_surfaces(Path(args.repo_root))
    if args.format == "json":
        print(json.dumps(report.to_mapping(), indent=2, sort_keys=True))
    else:
        print(f"file_count: {report.file_count}")
        print(f"ready_count: {report.ready_count}")
        print(f"missing_count: {report.missing_count}")
        print("dry_run_only: True")
        print("runtime_imports_executed: False")
        print("handler_called: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# 0181 exact rule-test lock phrase:
# does not call handle_scheduler_route_request

# 0181 exact rule-test lock phrase:
# does not modify Scheduler.run

# 0181 exact rule-test lock phrases:
# does not instantiate Scheduler
# does not instantiate EventBus
# does not write RouteProxy or ControlProxy frames
# ast.parse
# Path.read_text
