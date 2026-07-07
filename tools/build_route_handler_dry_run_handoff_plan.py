#!/usr/bin/env python3
"""Build a dry-run route handler handoff plan.

0182 is a planning tool only.

It reads scheduler.route_requests.jsonl, validates queued items through the
existing queue reader, inspects the existing route handler file as text/AST, and
optionally writes route_handler_dry_run_plan.jsonl.

It does not import runtime handler modules.
It does not call handle_scheduler_route_request.
It does not modify Scheduler.run.
It does not instantiate Scheduler.
It does not instantiate EventBus.
It does not write RouteProxy or ControlProxy frames.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.authorized_route_request_queue import iter_authorized_route_request_queue  # noqa: E402


ROUTE_HANDLER_DRY_RUN_HANDOFF_PLAN_SCHEMA = "missipy.route_handler.dry_run_handoff_plan.v1"
DEFAULT_HANDLER_FILE = "src/runtime/scheduler_route_handler_minimal.py"
DEFAULT_HANDLER_SYMBOL = "handle_scheduler_route_request"
DEFAULT_OUTPUT_NAME = "route_handler_dry_run_plan.jsonl"


class RouteHandlerDryRunHandoffPlanError(ValueError):
    """Raised when the dry-run handoff plan cannot be built safely."""


def build_route_handler_dry_run_handoff_plan(
    *,
    queue_path: Path | str,
    repo_root: Path | str,
    output_path: Path | str | None = None,
    handler_file: str = DEFAULT_HANDLER_FILE,
    handler_symbol: str = DEFAULT_HANDLER_SYMBOL,
) -> dict[str, Any]:
    """Build a dry-run handoff plan without executing route handling."""

    root = Path(repo_root)
    queue = Path(queue_path)
    handler = _inspect_handler_signature(root, handler_file, handler_symbol)
    requests = list(iter_authorized_route_request_queue(queue))

    items: list[dict[str, Any]] = []
    for index, request in enumerate(requests, start=1):
        issues: list[str] = []
        if not request.authorized:
            issues.append("request is not authorized")
        if not request.policy_decision_id:
            issues.append("missing policy_decision_id")
        if not handler["function_found"]:
            issues.append("handler function not found")
        if not handler["ast_parse_ok"]:
            issues.append("handler file does not parse")
        if not handler["exists"]:
            issues.append("handler file missing")

        items.append(
            {
                "index": index,
                "request_id": request.request_id,
                "route_id": request.route_id,
                "task_id": request.task_id,
                "authorized": request.authorized,
                "policy_decision_id": request.policy_decision_id,
                "handler_file": handler_file,
                "handler_symbol": handler_symbol,
                "handler_signature": handler["signature"],
                "ready_for_later_handler_call": not issues,
                "issues": issues,
            }
        )

    if output_path is not None:
        _write_plan_jsonl(Path(output_path), items)

    ready_count = sum(1 for item in items if item["ready_for_later_handler_call"])
    return {
        "schema": ROUTE_HANDLER_DRY_RUN_HANDOFF_PLAN_SCHEMA,
        "queue_path": str(queue),
        "output_path": str(output_path) if output_path is not None else None,
        "handler": handler,
        "item_count": len(items),
        "ready_count": ready_count,
        "blocked_count": len(items) - ready_count,
        "items": items,
        "dry_run_only": True,
        "runtime_imports_executed": False,
        "handler_called": False,
        "scheduler_modified": False,
        "frames_written": False,
    }


def _inspect_handler_signature(repo_root: Path, handler_file: str, handler_symbol: str) -> dict[str, Any]:
    path = _safe_repo_file(repo_root, handler_file)
    if not path.exists():
        return {
            "path": handler_file,
            "exists": False,
            "ast_parse_ok": False,
            "function_found": False,
            "signature": None,
            "imports_detected": [],
        }

    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return {
            "path": handler_file,
            "exists": True,
            "ast_parse_ok": False,
            "function_found": False,
            "signature": None,
            "imports_detected": [],
        }

    signature = None
    function_found = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == handler_symbol:
            function_found = True
            signature = _function_signature(node)
            break

    return {
        "path": handler_file,
        "exists": True,
        "ast_parse_ok": True,
        "function_found": function_found,
        "signature": signature,
        "imports_detected": sorted(_ast_imports(tree)),
    }


def _function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    args = node.args
    positional = [arg.arg for arg in args.posonlyargs + args.args]
    keyword_only = [arg.arg for arg in args.kwonlyargs]
    vararg = args.vararg.arg if args.vararg else None
    kwarg = args.kwarg.arg if args.kwarg else None
    return {
        "name": node.name,
        "positional": positional,
        "keyword_only": keyword_only,
        "vararg": vararg,
        "kwarg": kwarg,
        "arg_count": len(positional) + len(keyword_only),
    }


def _ast_imports(tree: ast.AST) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
    return imports


def _write_plan_jsonl(path: Path, items: list[Mapping[str, Any]]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise RouteHandlerDryRunHandoffPlanError("output filename must be route_handler_dry_run_plan.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(dict(item), sort_keys=True, separators=(",", ":")) + "\n")


def _safe_repo_file(repo_root: Path, relative: str) -> Path:
    if not relative or relative.startswith("/") or "\\" in relative or ".." in relative.split("/"):
        raise RouteHandlerDryRunHandoffPlanError("handler_file must be a safe repo-relative path")
    return repo_root / relative


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a dry-run route handler handoff plan.")
    parser.add_argument("--queue", required=True, help="Path to scheduler.route_requests.jsonl.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--output", help="Optional route_handler_dry_run_plan.jsonl output path.")
    parser.add_argument("--handler-file", default=DEFAULT_HANDLER_FILE)
    parser.add_argument("--handler-symbol", default=DEFAULT_HANDLER_SYMBOL)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = build_route_handler_dry_run_handoff_plan(
        queue_path=Path(args.queue),
        repo_root=Path(args.repo_root),
        output_path=Path(args.output) if args.output else None,
        handler_file=args.handler_file,
        handler_symbol=args.handler_symbol,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"item_count: {report['item_count']}")
        print(f"ready_count: {report['ready_count']}")
        print(f"blocked_count: {report['blocked_count']}")
        print("dry_run_only: True")
        print("handler_called: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
