#!/usr/bin/env python3
"""Build an isolated handler execution plan without executing the handler.

0186 is a planning/audit tool only.

It reads scheduler_route_handler_command_smoke.jsonl from 0185, inspects the
existing route_proxy_runtime_minimal.py file as text/AST, resolves the
RouteProxyRuntimePolicy shape, and writes a reviewable isolated execution plan.

It does not import runtime handler modules.
It does not import route_proxy_runtime_minimal.
It does not call handle_scheduler_route_command.
It does not call prepare_route_proxy_runtime.
It does not request writer permits.
It does not write RouteProxy or ControlProxy frames.
It does not modify Scheduler.run.
It does not instantiate Scheduler.
It does not instantiate EventBus.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


ISOLATED_HANDLER_EXECUTION_PLAN_SCHEMA = "missipy.route_handler.isolated_execution_plan.v1"
DEFAULT_INPUT_NAME = "scheduler_route_handler_command_smoke.jsonl"
DEFAULT_OUTPUT_NAME = "isolated_handler_execution_plan.jsonl"
DEFAULT_ROUTE_PROXY_RUNTIME_PATH = "src/runtime/route_proxy_runtime_minimal.py"

POLICY_ROOT_FIELD_PREFERENCE = (
    "runtime_root",
    "route_root",
    "root",
    "shm_root",
    "base_dir",
    "runtime_dir",
)


class IsolatedHandlerExecutionPlanError(ValueError):
    """Raised when isolated handler execution planning is unsafe."""


def build_isolated_handler_execution_plan(
    *,
    smoke_path: Path | str,
    repo_root: Path | str,
    isolated_runtime_root: Path | str,
    output_path: Path | str | None = None,
    route_proxy_runtime_path: str = DEFAULT_ROUTE_PROXY_RUNTIME_PATH,
) -> dict[str, Any]:
    """Build an isolated execution plan from command-builder smoke output."""

    smoke = Path(smoke_path)
    root = Path(repo_root)
    isolated_root = Path(isolated_runtime_root)
    runtime_surface = _inspect_route_proxy_runtime_surface(root, route_proxy_runtime_path)
    items = [
        _build_item(index, item, runtime_surface=runtime_surface, isolated_runtime_root=isolated_root)
        for index, item in enumerate(_read_smoke_items(smoke), start=1)
    ]

    if output_path is not None:
        _write_plan_jsonl(Path(output_path), items)

    ready_count = sum(1 for item in items if item["ready_for_later_isolated_handler_call"])
    return {
        "schema": ISOLATED_HANDLER_EXECUTION_PLAN_SCHEMA,
        "smoke_path": str(smoke),
        "repo_root": str(root),
        "isolated_runtime_root": str(isolated_root),
        "output_path": str(output_path) if output_path is not None else None,
        "route_proxy_runtime_surface": runtime_surface,
        "item_count": len(items),
        "ready_count": ready_count,
        "blocked_count": len(items) - ready_count,
        "items": items,
        "dry_run_only": True,
        "runtime_imports_executed": False,
        "handler_called": False,
        "routeproxy_prepared": False,
        "writer_permits_requested": False,
        "frames_written": False,
        "scheduler_modified": False,
    }


def _build_item(
    index: int,
    smoke_item: Mapping[str, Any],
    *,
    runtime_surface: Mapping[str, Any],
    isolated_runtime_root: Path,
) -> dict[str, Any]:
    issues: list[str] = []
    if not smoke_item.get("command_built"):
        issues.append("command smoke item was not built")
    if not smoke_item.get("ready_for_later_handler_call"):
        issues.append("command smoke item is not ready for handler call")
    command_mapping = smoke_item.get("command_mapping")
    if not isinstance(command_mapping, Mapping):
        issues.append("command_mapping must be an object")
        command_mapping = {}

    if not runtime_surface.get("route_proxy_runtime_policy_available"):
        issues.append("RouteProxyRuntimePolicy is not available")
    if not runtime_surface.get("prepare_route_proxy_runtime_available"):
        issues.append("prepare_route_proxy_runtime is not available")

    selected_root_field = runtime_surface.get("selected_policy_root_field")
    runtime_policy_kwargs: dict[str, Any] | None = None
    if selected_root_field is None:
        issues.append("no isolated runtime root field found on RouteProxyRuntimePolicy")
    else:
        runtime_policy_kwargs = {str(selected_root_field): str(isolated_runtime_root)}

    return {
        "index": index,
        "source_request_id": smoke_item.get("source_request_id"),
        "source_route_id": smoke_item.get("source_route_id"),
        "source_task_id": smoke_item.get("source_task_id"),
        "policy_decision_id": smoke_item.get("policy_decision_id"),
        "command_ref": command_mapping.get("command_ref"),
        "handler_surface": smoke_item.get("handler_surface"),
        "handler_call_allowed_by_0186": False,
        "planned_handler_surface": "handle_scheduler_route_command",
        "planned_runtime_surface": "prepare_route_proxy_runtime",
        "isolated_runtime_root": str(isolated_runtime_root),
        "runtime_policy_kwargs": runtime_policy_kwargs,
        "command_mapping": dict(command_mapping),
        "ready_for_later_isolated_handler_call": not issues,
        "issues": issues,
    }


def _inspect_route_proxy_runtime_surface(repo_root: Path, relative_path: str) -> dict[str, Any]:
    path = _safe_repo_file(repo_root, relative_path)
    if not path.exists():
        return {
            "path": relative_path,
            "exists": False,
            "ast_parse_ok": False,
            "route_proxy_runtime_policy_available": False,
            "prepare_route_proxy_runtime_available": False,
            "request_writer_permit_available": False,
            "write_route_frame_available": False,
            "read_route_frame_available": False,
            "policy_fields": [],
            "policy_required_fields": [],
            "policy_root_field_candidates": [],
            "selected_policy_root_field": None,
        }

    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return {
            "path": relative_path,
            "exists": True,
            "ast_parse_ok": False,
            "route_proxy_runtime_policy_available": False,
            "prepare_route_proxy_runtime_available": False,
            "request_writer_permit_available": False,
            "write_route_frame_available": False,
            "read_route_frame_available": False,
            "policy_fields": [],
            "policy_required_fields": [],
            "policy_root_field_candidates": [],
            "selected_policy_root_field": None,
        }

    functions = _top_level_functions(tree)
    classes = _top_level_classes(tree)
    policy_fields, required_fields = _dataclass_like_fields(classes.get("RouteProxyRuntimePolicy"))
    root_candidates = _root_field_candidates(policy_fields)
    selected = _select_root_field(root_candidates)

    return {
        "path": relative_path,
        "exists": True,
        "ast_parse_ok": True,
        "route_proxy_runtime_policy_available": "RouteProxyRuntimePolicy" in classes,
        "prepare_route_proxy_runtime_available": "prepare_route_proxy_runtime" in functions,
        "request_writer_permit_available": "request_writer_permit" in functions,
        "write_route_frame_available": "write_route_frame" in functions,
        "read_route_frame_available": "read_route_frame" in functions,
        "policy_fields": policy_fields,
        "policy_required_fields": required_fields,
        "policy_root_field_candidates": root_candidates,
        "selected_policy_root_field": selected,
    }


def _top_level_functions(tree: ast.AST) -> set[str]:
    return {
        node.name
        for node in getattr(tree, "body", [])
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _top_level_classes(tree: ast.AST) -> dict[str, ast.ClassDef]:
    return {
        node.name: node
        for node in getattr(tree, "body", [])
        if isinstance(node, ast.ClassDef)
    }


def _dataclass_like_fields(node: ast.ClassDef | None) -> tuple[list[str], list[str]]:
    if node is None:
        return [], []
    fields: list[str] = []
    required: list[str] = []
    for child in node.body:
        if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            name = child.target.id
            fields.append(name)
            if child.value is None:
                required.append(name)
        elif isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    fields.append(target.id)
    return fields, required


def _root_field_candidates(fields: Iterable[str]) -> list[str]:
    candidates: list[str] = []
    for field in fields:
        lowered = field.lower()
        if "root" in lowered or lowered.endswith("_dir") or lowered.endswith("_path"):
            candidates.append(field)
    return candidates


def _select_root_field(candidates: Iterable[str]) -> str | None:
    candidate_list = list(candidates)
    for preferred in POLICY_ROOT_FIELD_PREFERENCE:
        if preferred in candidate_list:
            return preferred
    return candidate_list[0] if candidate_list else None


def _read_smoke_items(path: Path) -> Iterable[dict[str, Any]]:
    if path.name != DEFAULT_INPUT_NAME:
        raise IsolatedHandlerExecutionPlanError("input filename must be scheduler_route_handler_command_smoke.jsonl")
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise IsolatedHandlerExecutionPlanError(f"invalid smoke JSON at {path}:{line_number}") from exc
            if not isinstance(item, dict):
                raise IsolatedHandlerExecutionPlanError(f"smoke line must be an object at {path}:{line_number}")
            yield item


def _write_plan_jsonl(path: Path, items: list[Mapping[str, Any]]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise IsolatedHandlerExecutionPlanError("output filename must be isolated_handler_execution_plan.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(dict(item), sort_keys=True, separators=(",", ":")) + "\n")


def _safe_repo_file(repo_root: Path, relative: str) -> Path:
    if not relative or relative.startswith("/") or "\\" in relative or ".." in relative.split("/"):
        raise IsolatedHandlerExecutionPlanError("path must be a safe repo-relative path")
    return repo_root / relative


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build isolated handler execution plan without executing the handler.")
    parser.add_argument("--smoke", required=True, help="Path to scheduler_route_handler_command_smoke.jsonl.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]), help="Repository root.")
    parser.add_argument("--isolated-runtime-root", required=True, help="Explicit isolated runtime root for a later smoke.")
    parser.add_argument("--output", help="Optional isolated_handler_execution_plan.jsonl output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = build_isolated_handler_execution_plan(
        smoke_path=Path(args.smoke),
        repo_root=Path(args.repo_root),
        isolated_runtime_root=Path(args.isolated_runtime_root),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"item_count: {report['item_count']}")
        print(f"ready_count: {report['ready_count']}")
        print(f"blocked_count: {report['blocked_count']}")
        print("dry_run_only: True")
        print("handler_called: False")
        print("routeproxy_prepared: False")
        print("frames_written: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
