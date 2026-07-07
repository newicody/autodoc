#!/usr/bin/env python3
"""Read back isolated Scheduler route handler smoke frames.

0188 is a controlled isolated readback smoke.

It reads isolated_scheduler_route_handler_smoke.jsonl from 0187, prepares
RouteProxyRuntime only inside the recorded isolated runtime root, reads back each
written route frame through read_route_frame, verifies the route_ref and path
boundaries, and writes isolated_scheduler_route_handler_readback_smoke.jsonl.

It must not call handle_scheduler_route_command.
It must not call handle_scheduler_route_request.
It must not request writer permits.
It must not call write_route_frame.
It must not modify Scheduler.run.
It must not instantiate Scheduler.
It must not instantiate EventBus.
It must not write ControlProxy frames.
It must not call GitHub API or use network.
"""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime.route_proxy_runtime_minimal import (  # noqa: E402
    RouteProxyRuntimePolicy,
    prepare_route_proxy_runtime,
    read_route_frame,
)


ISOLATED_SCHEDULER_ROUTE_HANDLER_READBACK_SMOKE_SCHEMA = "missipy.scheduler.route_handler.isolated_readback_smoke.v1"
DEFAULT_INPUT_NAME = "isolated_scheduler_route_handler_smoke.jsonl"
DEFAULT_OUTPUT_NAME = "isolated_scheduler_route_handler_readback_smoke.jsonl"


class IsolatedSchedulerRouteHandlerReadbackSmokeError(ValueError):
    """Raised when isolated readback smoke cannot run safely."""


def run_isolated_scheduler_route_handler_readback_smoke(
    *,
    smoke_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Read frames written by 0187 from the explicit isolated runtime root."""

    smoke = Path(smoke_path)
    items = [_readback_item(index, item) for index, item in enumerate(_read_smoke_items(smoke), start=1)]

    if output_path is not None:
        _write_readback_jsonl(Path(output_path), items)

    readback_count = sum(len(item["readback_frames"]) for item in items)
    blocked_count = sum(1 for item in items if item["issues"])
    return {
        "schema": ISOLATED_SCHEDULER_ROUTE_HANDLER_READBACK_SMOKE_SCHEMA,
        "smoke_path": str(smoke),
        "output_path": str(output_path) if output_path is not None else None,
        "item_count": len(items),
        "readback_count": readback_count,
        "blocked_count": blocked_count,
        "items": items,
        "routeproxy_prepared": readback_count > 0,
        "read_route_frame_called": readback_count > 0,
        "handler_called": False,
        "writer_permits_requested": False,
        "frames_written": False,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "eventbus_instantiated": False,
        "network_used": False,
    }


def _readback_item(index: int, item: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not item.get("handler_called"):
        issues.append("0187 smoke item did not call handler")
    isolated_root = Path(str(item.get("isolated_runtime_root") or ""))
    if not _safe_isolated_root(isolated_root):
        issues.append("isolated_runtime_root is unsafe")
    written_route_refs = item.get("written_route_refs")
    if not isinstance(written_route_refs, list) or not all(isinstance(value, str) for value in written_route_refs):
        issues.append("written_route_refs must be a list of strings")
        written_route_refs = []
    frame_paths = item.get("frame_paths")
    if not isinstance(frame_paths, list) or not all(isinstance(value, str) for value in frame_paths):
        issues.append("frame_paths must be a list of strings")
        frame_paths = []

    for frame_path in frame_paths:
        path = Path(frame_path)
        if not _is_within(path, isolated_root):
            issues.append("frame_path escaped isolated_runtime_root")
        if not path.exists():
            issues.append("frame_path does not exist")

    if issues:
        return _blocked_item(index, item, issues)

    before_files = _frame_file_set(isolated_root)
    policy = _build_runtime_policy(isolated_root)
    state = prepare_route_proxy_runtime(policy)
    readback_frames: list[dict[str, Any]] = []
    for route_ref in written_route_refs:
        frame = read_route_frame(state, route_ref)
        mapping = _json_ready(frame.to_mapping())
        if mapping.get("route_ref") != route_ref:
            raise IsolatedSchedulerRouteHandlerReadbackSmokeError("readback route_ref mismatch")
        readback_frames.append(mapping)

    after_files = _frame_file_set(isolated_root)
    if after_files != before_files:
        raise IsolatedSchedulerRouteHandlerReadbackSmokeError("readback changed isolated frame files")

    return {
        "index": index,
        "source_request_id": item.get("source_request_id"),
        "source_route_id": item.get("source_route_id"),
        "source_task_id": item.get("source_task_id"),
        "policy_decision_id": item.get("policy_decision_id"),
        "command_ref": item.get("command_ref"),
        "isolated_runtime_root": str(isolated_root),
        "written_route_refs": list(written_route_refs),
        "frame_paths": list(frame_paths),
        "readback_frames": readback_frames,
        "readback_count": len(readback_frames),
        "routeproxy_prepared": True,
        "read_route_frame_called": True,
        "handler_called": False,
        "writer_permits_requested": False,
        "frames_written": False,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "issues": [],
    }


def _blocked_item(index: int, item: Mapping[str, Any], issues: list[str]) -> dict[str, Any]:
    return {
        "index": index,
        "source_request_id": item.get("source_request_id"),
        "source_route_id": item.get("source_route_id"),
        "source_task_id": item.get("source_task_id"),
        "policy_decision_id": item.get("policy_decision_id"),
        "command_ref": item.get("command_ref"),
        "isolated_runtime_root": str(item.get("isolated_runtime_root")),
        "written_route_refs": [],
        "frame_paths": [],
        "readback_frames": [],
        "readback_count": 0,
        "routeproxy_prepared": False,
        "read_route_frame_called": False,
        "handler_called": False,
        "writer_permits_requested": False,
        "frames_written": False,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "issues": issues,
    }


def _build_runtime_policy(isolated_root: Path) -> RouteProxyRuntimePolicy:
    signature = inspect.signature(RouteProxyRuntimePolicy)
    accepted = set(signature.parameters)
    kwargs: dict[str, Any] = {}
    if "route_root" in accepted:
        kwargs["route_root"] = isolated_root
    if "runtime_root" in accepted:
        kwargs["runtime_root"] = isolated_root
    if "allow_test_root" in accepted:
        kwargs["allow_test_root"] = True
    if "require_dev_shm" in accepted:
        kwargs["require_dev_shm"] = False
    if "proxy_ref" in accepted:
        kwargs["proxy_ref"] = "proxy:0188-isolated-readback-smoke"
    if "namespace" in accepted:
        kwargs["namespace"] = "0188-isolated-readback-smoke"
    return RouteProxyRuntimePolicy(**kwargs)


def _read_smoke_items(path: Path) -> Iterable[dict[str, Any]]:
    if path.name != DEFAULT_INPUT_NAME:
        raise IsolatedSchedulerRouteHandlerReadbackSmokeError("input filename must be isolated_scheduler_route_handler_smoke.jsonl")
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise IsolatedSchedulerRouteHandlerReadbackSmokeError(f"invalid smoke JSON at {path}:{line_number}") from exc
            if not isinstance(item, dict):
                raise IsolatedSchedulerRouteHandlerReadbackSmokeError(f"smoke line must be an object at {path}:{line_number}")
            yield item


def _write_readback_jsonl(path: Path, items: list[Mapping[str, Any]]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise IsolatedSchedulerRouteHandlerReadbackSmokeError("output filename must be isolated_scheduler_route_handler_readback_smoke.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(dict(item), sort_keys=True, separators=(",", ":")) + "\n")


def _frame_file_set(root: Path) -> set[Path]:
    frames = root / "frames"
    if not frames.exists():
        return set()
    return {path.resolve() for path in frames.glob("*.json") if path.is_file()}


def _safe_isolated_root(path: Path) -> bool:
    if not path.is_absolute():
        return False
    resolved = path.resolve()
    if resolved == Path("/"):
        return False
    forbidden = {Path("/dev"), Path("/dev/shm"), Path("/proc"), Path("/sys"), Path("/run")}
    return all(resolved != forbidden_path for forbidden_path in forbidden)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read back isolated Scheduler route handler smoke frames.")
    parser.add_argument("--smoke", required=True, help="Path to isolated_scheduler_route_handler_smoke.jsonl.")
    parser.add_argument("--output", help="Optional isolated_scheduler_route_handler_readback_smoke.jsonl output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = run_isolated_scheduler_route_handler_readback_smoke(
        smoke_path=Path(args.smoke),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"item_count: {report['item_count']}")
        print(f"readback_count: {report['readback_count']}")
        print(f"blocked_count: {report['blocked_count']}")
        print(f"routeproxy_prepared: {report['routeproxy_prepared']}")
        print(f"read_route_frame_called: {report['read_route_frame_called']}")
        print("handler_called: False")
        print("frames_written: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
