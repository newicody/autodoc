#!/usr/bin/env python3
"""Run one canonical GitHub Actions artifact fetch without Issue publication.

The Projects repository owns production and publication of the initial Copilot
advisory.  This local entrypoint only reuses the existing read-only scan/fetch
tool and persists a bounded execution report.  It performs no Issue mutation,
ProjectV2 mutation, SQL write, Qdrant write, Scheduler dispatch, or laboratory
execution.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterator, Mapping, Sequence, TextIO

_REPO_ROOT = Path(__file__).resolve().parents[1]

SCHEMA = "missipy.github_actions.artifact_fetch_cycle_once.v1"
_SCAN_SCHEMA = "missipy.github_actions.artifact_scan_once_live.v1"
_DEFAULT_SCAN_TOOL = Path("tools/run_github_actions_artifact_scan_once_live_0272.py")
_DEFAULT_REPORT_ROOT = Path(".var/reports/github_actions_artifact_fetch_cycle")
_DEFAULT_LOCK_PATH = Path(".var/locks/github_actions_artifact_fetch_cycle.lock")


class FetchCycleLockedError(RuntimeError):
    """Raised when another canonical fetch cycle owns the local lock."""


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch and correlate GitHub Actions artifacts locally without "
            "republishing the Projects-owned initial Copilot advisory."
        )
    )
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--fetch-config", type=Path, required=True)
    parser.add_argument("--report-root", type=Path, default=_DEFAULT_REPORT_ROOT)
    parser.add_argument("--lock-path", type=Path, default=_DEFAULT_LOCK_PATH)
    parser.add_argument("--scan-tool", type=Path, default=_DEFAULT_SCAN_TOOL)
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument("--max-runs", type=int, default=10)
    parser.add_argument("--max-artifacts", type=int, default=30)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    _normalize_paths(args)

    cycle_id = _cycle_id()
    cycle_dir = args.report_root / cycle_id
    scan_report_path = cycle_dir / "artifact_scan.json"
    cycle_report_path = cycle_dir / "fetch_cycle.json"

    issues = _validate_args(args)
    if issues:
        payload = _base_payload(
            args,
            cycle_id=cycle_id,
            cycle_report_path=cycle_report_path,
            scan_report_path=scan_report_path,
        )
        payload.update({"valid": False, "status": "rejected", "issues": issues})
        _write_json_atomic(cycle_report_path, payload)
        _emit(payload, args.format)
        return 2

    try:
        with _exclusive_cycle_lock(args.lock_path):
            payload = _run_cycle(
                args,
                cycle_id=cycle_id,
                cycle_report_path=cycle_report_path,
                scan_report_path=scan_report_path,
            )
    except FetchCycleLockedError as exc:
        payload = _base_payload(
            args,
            cycle_id=cycle_id,
            cycle_report_path=cycle_report_path,
            scan_report_path=scan_report_path,
        )
        payload.update(
            {
                "valid": True,
                "status": "overlap-skipped",
                "issues": [],
                "skip_reason": str(exc),
                "boundaries": _boundaries(
                    scan_called=False,
                    overlap_prevented=True,
                ),
            }
        )
        _write_json_atomic(cycle_report_path, payload)

    _emit(payload, args.format)
    return 0 if payload.get("valid") is True else 2


def _run_cycle(
    args: argparse.Namespace,
    *,
    cycle_id: str,
    cycle_report_path: Path,
    scan_report_path: Path,
) -> dict[str, Any]:
    command = _scan_command(args)
    child = _run_child_json(command, scan_report_path)
    scan_report = _mapping(child.get("payload"))
    valid = (
        child.get("returncode") == 0
        and scan_report.get("schema") == _SCAN_SCHEMA
        and scan_report.get("valid") is True
    )

    if not valid:
        status = "scan-failed"
    elif args.execute:
        status = "artifacts-fetched"
    else:
        status = "plan-complete"

    payload = _base_payload(
        args,
        cycle_id=cycle_id,
        cycle_report_path=cycle_report_path,
        scan_report_path=scan_report_path,
    )
    payload.update(
        {
            "valid": valid,
            "status": status,
            "issues": _child_issues(child),
            "children": {"artifact_scan": _child_summary(child)},
            "counts": dict(_mapping(scan_report.get("counts"))),
            "ready_runs": list(scan_report.get("ready_runs", [])),
            "boundaries": _boundaries(
                scan_called=True,
                overlap_prevented=False,
            ),
        }
    )
    _write_json_atomic(cycle_report_path, payload)
    return payload


def _scan_command(args: argparse.Namespace) -> tuple[str, ...]:
    command = [
        sys.executable,
        str(_absolute(args.scan_tool)),
        "--project-config",
        str(args.project_config),
        "--fetch-config",
        str(args.fetch_config),
        "--policy-decision-id",
        f"{args.policy_decision_id}:artifact-scan",
        "--max-runs",
        str(args.max_runs),
        "--max-artifacts",
        str(args.max_artifacts),
        "--format",
        "json",
    ]
    if args.execute:
        command.append("--execute")
    return tuple(command)


def _run_child_json(command: Sequence[str], report_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        list(command),
        cwd=_REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    payload: dict[str, Any] = {}
    decode_error = ""
    if completed.stdout.strip():
        try:
            decoded = json.loads(completed.stdout)
            if isinstance(decoded, Mapping):
                payload = dict(decoded)
            else:
                decode_error = "child stdout must contain a JSON object"
        except json.JSONDecodeError as exc:
            decode_error = f"child stdout is not valid JSON: {exc}"
    else:
        decode_error = "child produced no JSON stdout"

    persisted: Mapping[str, Any]
    if payload:
        persisted = payload
    else:
        persisted = {
            "schema": "missipy.child_process_failure.v1",
            "valid": False,
            "returncode": completed.returncode,
            "decode_error": decode_error,
            "stderr": completed.stderr,
        }
    _write_json_atomic(report_path, persisted)
    return {
        "command": list(command),
        "returncode": completed.returncode,
        "stderr": completed.stderr,
        "decode_error": decode_error,
        "payload": payload,
        "report_path": str(report_path),
    }


def _child_summary(child: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(child.get("payload"))
    return {
        "called": True,
        "returncode": child.get("returncode"),
        "valid": payload.get("valid"),
        "status": payload.get("status") or payload.get("child_status"),
        "schema": payload.get("schema"),
        "report_path": child.get("report_path", ""),
        "decode_error": child.get("decode_error", ""),
    }


def _child_issues(child: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if child.get("decode_error"):
        issues.append(f"artifact scan: {child['decode_error']}")
    payload = _mapping(child.get("payload"))
    for issue in payload.get("issues", []):
        issues.append(f"artifact scan: {issue}")
    if child.get("returncode") not in (0, None) and not payload.get("issues"):
        detail = str(child.get("stderr", "")).strip()
        issues.append(
            f"artifact scan child failed with return code {child.get('returncode')}"
            + (f": {detail[-500:]}" if detail else "")
        )
    return issues


def _base_payload(
    args: argparse.Namespace,
    *,
    cycle_id: str,
    cycle_report_path: Path,
    scan_report_path: Path,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "cycle_id": cycle_id,
        "mode": "execute" if args.execute else "plan",
        "policy_decision_id": args.policy_decision_id,
        "project_config": str(args.project_config),
        "fetch_config": str(args.fetch_config),
        "reports": {
            "cycle": str(cycle_report_path),
            "artifact_scan": str(scan_report_path),
        },
    }


def _boundaries(*, scan_called: bool, overlap_prevented: bool) -> dict[str, Any]:
    return {
        "one_shot": True,
        "polling_loop_added": False,
        "daemon_added": False,
        "fcron_remains_external_process_authority": True,
        "overlap_lock_non_blocking": True,
        "overlap_prevented": overlap_prevented,
        "existing_artifact_scan_reused": True,
        "scan_called": scan_called,
        "projects_repository_owns_initial_copilot_comment": True,
        "local_initial_copilot_comment_publication": False,
        "remote_issue_mutation_allowed": False,
        "project_v2_mutation_allowed": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_dispatch_started": False,
        "laboratory_execution_started": False,
    }


def _normalize_paths(args: argparse.Namespace) -> None:
    for name in ("project_config", "fetch_config", "report_root", "lock_path"):
        setattr(args, name, _absolute(Path(getattr(args, name))))


def _validate_args(args: argparse.Namespace) -> list[str]:
    issues: list[str] = []
    if not args.policy_decision_id.startswith("policy:"):
        issues.append("policy-decision-id must start with policy:")
    for name in ("max_runs", "max_artifacts"):
        if int(getattr(args, name)) <= 0:
            issues.append(name.replace("_", "-") + " must be > 0")
    if not args.project_config.is_file():
        issues.append(f"project config not found: {args.project_config}")
    if not args.fetch_config.is_file():
        issues.append(f"fetch config not found: {args.fetch_config}")
    scan_tool = _absolute(args.scan_tool)
    if not scan_tool.is_file():
        issues.append(f"scan tool not found: {scan_tool}")
    return issues


@contextmanager
def _exclusive_cycle_lock(path: Path) -> Iterator[TextIO]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise FetchCycleLockedError(
                "another canonical artifact fetch cycle is already running"
            ) from exc
        handle.seek(0)
        handle.truncate()
        handle.write(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "acquired_at": datetime.now(timezone.utc).isoformat(),
                },
                sort_keys=True,
            )
            + "\n"
        )
        handle.flush()
        yield handle
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _cycle_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + f"-{os.getpid()}"


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else _REPO_ROOT / path


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _emit(payload: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return
    counts = _mapping(payload.get("counts"))
    print(
        " ".join(
            (
                f"valid={payload.get('valid')}",
                f"status={payload.get('status')}",
                f"mode={payload.get('mode')}",
                f"ready={counts.get('ready_run_count', 0)}",
                "initial_copilot_comment_owner=projects",
                "local_issue_publication=false",
            )
        )
    )
    for issue in payload.get("issues", []):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
