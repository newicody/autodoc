#!/usr/bin/env python3
"""Resolve real route handler surfaces without executing them.

0183 is a resolver/audit tool only.

It reads existing route-related Python files as text/AST and reports the actual
available handoff surfaces:

- scheduler adapter request surface
- scheduler route command handler surface
- optional route command readback surface
- single-frame command builder surface
- ControlProxy compatibility wrapper surface

It does not import runtime handler modules.
It does not call handle_scheduler_route_request.
It does not call handle_scheduler_route_command.
It does not modify Scheduler.run.
It does not instantiate Scheduler.
It does not instantiate EventBus.
It does not write RouteProxy or ControlProxy frames.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


ROUTE_HANDLER_SURFACE_RESOLVER_SCHEMA = "missipy.route_handler.surface_resolver.v1"

SURFACE_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "surface_ref": "scheduler-adapter-request",
        "path": "src/runtime/scheduler_route_adapter.py",
        "symbols": ("SchedulerRouteRequest", "handle_scheduler_route_request", "scheduler_route_request_mapping"),
        "surface_role": "authorized_scheduler_request_to_route_reply",
        "execution_allowed_by_0183": False,
    },
    {
        "surface_ref": "minimal-command-handler",
        "path": "src/runtime/scheduler_route_handler_minimal.py",
        "symbols": ("SchedulerRouteHandlerCommand", "handle_scheduler_route_command"),
        "surface_role": "scheduler_command_to_routeproxy_frames",
        "execution_allowed_by_0183": False,
    },
    {
        "surface_ref": "minimal-command-readback-handler",
        "path": "src/runtime/scheduler_route_handler_minimal.py",
        "symbols": ("SchedulerRouteHandlerReadbackResult", "handle_scheduler_route_command_with_readback"),
        "surface_role": "scheduler_command_to_routeproxy_frames_with_readback",
        "execution_allowed_by_0183": False,
    },
    {
        "surface_ref": "minimal-single-frame-command-builder",
        "path": "src/runtime/scheduler_route_handler_minimal.py",
        "symbols": ("SchedulerRouteFrameRequest", "build_single_frame_route_command"),
        "surface_role": "route_request_to_scheduler_route_handler_command_candidate",
        "execution_allowed_by_0183": False,
    },
    {
        "surface_ref": "controlproxy-compatibility-wrapper",
        "path": "src/runtime/controlproxy_scheduler_handler.py",
        "symbols": ("handle_scheduler_route_request", "ControlProxySchedulerRouteRequestHandler"),
        "surface_role": "controlproxy_event_to_scheduler_route_request_wrapper",
        "execution_allowed_by_0183": False,
    },
    {
        "surface_ref": "scheduler-handshake",
        "path": "src/runtime/scheduler_route_handshake.py",
        "symbols": ("prepare_route_for_scheduler",),
        "surface_role": "authorized_scheduler_request_to_route_lease_handshake",
        "execution_allowed_by_0183": False,
    },
)


class RouteHandlerSurfaceResolverError(ValueError):
    """Raised when resolver inputs are unsafe."""


def resolve_route_handler_surfaces(repo_root: Path | str) -> dict[str, Any]:
    """Resolve available route handler surfaces using text/AST only."""

    root = Path(repo_root)
    surfaces = [_resolve_candidate(root, candidate) for candidate in SURFACE_CANDIDATES]
    available = [item for item in surfaces if item["available"]]
    missing = [item for item in surfaces if not item["available"]]
    recommended = _recommend_surface(surfaces)
    return {
        "schema": ROUTE_HANDLER_SURFACE_RESOLVER_SCHEMA,
        "repo_root": str(root),
        "surface_count": len(surfaces),
        "available_count": len(available),
        "missing_count": len(missing),
        "surfaces": surfaces,
        "recommended_next_surface": recommended,
        "dry_run_only": True,
        "runtime_imports_executed": False,
        "handler_called": False,
        "scheduler_modified": False,
        "frames_written": False,
    }


def _resolve_candidate(repo_root: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    relative = str(candidate["path"])
    path = _safe_repo_file(repo_root, relative)
    expected_symbols = tuple(str(symbol) for symbol in candidate["symbols"])
    if not path.exists():
        return _candidate_result(candidate, exists=False, ast_parse_ok=False, sha256=None, symbols={})

    text = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return _candidate_result(candidate, exists=True, ast_parse_ok=False, sha256=digest, symbols={})

    symbol_data = _symbols_from_ast(tree, expected_symbols)
    # Text fallback keeps constants / compatibility names visible without executing.
    for symbol in expected_symbols:
        if symbol in text and symbol not in symbol_data:
            symbol_data[symbol] = {"kind": "text", "signature": None}

    return _candidate_result(candidate, exists=True, ast_parse_ok=True, sha256=digest, symbols=symbol_data)


def _candidate_result(
    candidate: dict[str, Any],
    *,
    exists: bool,
    ast_parse_ok: bool,
    sha256: str | None,
    symbols: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    expected_symbols = tuple(str(symbol) for symbol in candidate["symbols"])
    found = [symbol for symbol in expected_symbols if symbol in symbols]
    missing = [symbol for symbol in expected_symbols if symbol not in symbols]
    return {
        "surface_ref": candidate["surface_ref"],
        "path": candidate["path"],
        "surface_role": candidate["surface_role"],
        "exists": exists,
        "ast_parse_ok": ast_parse_ok,
        "sha256": sha256,
        "symbols_found": found,
        "symbols_missing": missing,
        "symbol_details": {symbol: symbols[symbol] for symbol in found},
        "available": exists and ast_parse_ok and not missing,
        "execution_allowed_by_0183": False,
    }


def _symbols_from_ast(tree: ast.AST, expected_symbols: Iterable[str]) -> dict[str, dict[str, Any]]:
    expected = set(expected_symbols)
    found: dict[str, dict[str, Any]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in expected:
            found[node.name] = {"kind": "class", "signature": None}
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in expected:
            found[node.name] = {"kind": "function", "signature": _function_signature(node)}
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in expected:
                    found[target.id] = {"kind": "constant", "signature": None}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id in expected:
            found[node.target.id] = {"kind": "constant", "signature": None}
    return found


def _function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    args = node.args
    positional = [arg.arg for arg in args.posonlyargs + args.args]
    keyword_only = [arg.arg for arg in args.kwonlyargs]
    return {
        "name": node.name,
        "positional": positional,
        "keyword_only": keyword_only,
        "vararg": args.vararg.arg if args.vararg else None,
        "kwarg": args.kwarg.arg if args.kwarg else None,
        "arg_count": len(positional) + len(keyword_only),
    }


def _recommend_surface(surfaces: list[dict[str, Any]]) -> dict[str, Any] | None:
    by_ref = {surface["surface_ref"]: surface for surface in surfaces}
    for ref in (
        "minimal-command-handler",
        "minimal-command-readback-handler",
        "scheduler-adapter-request",
        "controlproxy-compatibility-wrapper",
    ):
        surface = by_ref.get(ref)
        if surface and surface["available"]:
            return {
                "surface_ref": surface["surface_ref"],
                "path": surface["path"],
                "surface_role": surface["surface_role"],
                "reason": "first available existing surface in command-handler-first order",
            }
    return None


def _safe_repo_file(repo_root: Path, relative: str) -> Path:
    if not relative or relative.startswith("/") or "\\" in relative or ".." in relative.split("/"):
        raise RouteHandlerSurfaceResolverError("path must be a safe repo-relative path")
    return repo_root / relative


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve route handler surfaces without executing them.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = resolve_route_handler_surfaces(Path(args.repo_root))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"surface_count: {report['surface_count']}")
        print(f"available_count: {report['available_count']}")
        print(f"missing_count: {report['missing_count']}")
        print(f"recommended_next_surface: {None if report['recommended_next_surface'] is None else report['recommended_next_surface']['surface_ref']}")
        print("dry_run_only: True")
        print("handler_called: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
