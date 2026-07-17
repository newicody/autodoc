#!/usr/bin/env python3
"""Run one bounded local artifact-fetch and Copilot Issue-publication cycle.

This command composes two existing one-shot tools:

1. the read-only GitHub Actions artifact scan/fetch;
2. the local ready-run Copilot v2 Issue-comment publisher.

It does not add a polling loop, daemon, Scheduler integration, laboratory
manager, artifact downloader, or GitHub publication adapter.
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

SCHEMA = "missipy.github_actions.artifact_copilot_publication_cycle_once.v1"
_DEFAULT_SCAN_TOOL = Path("tools/run_github_actions_artifact_scan_once_live_0272.py")
_DEFAULT_PUBLICATION_TOOL = Path(
    "tools/run_github_actions_ready_run_copilot_issue_publication_once_0287.py"
)
_DEFAULT_DATASET_ROOT = Path(".var/server_datasets/github_artifacts")
_DEFAULT_PUBLICATION_STATE = (
    _DEFAULT_DATASET_ROOT / "index/copilot_issue_publication_state.json"
)
_DEFAULT_REPORT_ROOT = Path(
    ".var/reports/github_actions_artifact_copilot_publication_cycle"
)
_DEFAULT_LOCK_PATH = Path(
    ".var/locks/github_actions_artifact_copilot_publication_cycle.lock"
)


class CycleLockedError(RuntimeError):
    """Raised when another one-shot cycle currently owns the local lock."""


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compose one read-only Actions artifact fetch with one controlled "
            "local Copilot advisory Issue-publication pass."
        )
    )
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--fetch-config", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, default=_DEFAULT_DATASET_ROOT)
    parser.add_argument(
        "--publication-state-path", type=Path, default=_DEFAULT_PUBLICATION_STATE
    )
    parser.add_argument("--report-root", type=Path, default=_DEFAULT_REPORT_ROOT)
    parser.add_argument("--lock-path", type=Path, default=_DEFAULT_LOCK_PATH)
    parser.add_argument("--scan-tool", type=Path, default=_DEFAULT_SCAN_TOOL)
    parser.add_argument(
        "--publication-tool", type=Path, default=_DEFAULT_PUBLICATION_TOOL
    )
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument("--operator-decision", choices=("approve",), required=True)
    parser.add_argument("--max-runs", type=int, default=10)
    parser.add_argument("--max-artifacts", type=int, default=30)
    parser.add_argument("--max-publications", type=int, default=10)
    parser.add_argument("--run-id", action="append", default=[])
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    _normalize_paths(args)
    issues = _validate_args(args)
    if args.execute:
        issues.extend(_execute_gate_issues())

    cycle_id = _cycle_id()
    cycle_dir = args.report_root / cycle_id
    scan_report_path = cycle_dir / "artifact_scan.json"
    publication_report_path = cycle_dir / "copilot_issue_publication.json"
    cycle_report_path = cycle_dir / "cycle.json"

    if issues:
        payload = _base_payload(
            args,
            cycle_id=cycle_id,
            cycle_report_path=cycle_report_path,
            scan_report_path=scan_report_path,
            publication_report_path=publication_report_path,
        )
        payload.update(
            {
                "valid": False,
                "status": "rejected",
                "issues": issues,
            }
        )
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
                publication_report_path=publication_report_path,
            )
    except CycleLockedError as exc:
        payload = _base_payload(
            args,
            cycle_id=cycle_id,
            cycle_report_path=cycle_report_path,
            scan_report_path=scan_report_path,
            publication_report_path=publication_report_path,
        )
        payload.update(
            {
                "valid": True,
                "status": "overlap-skipped",
                "issues": [],
                "skip_reason": str(exc),
                "boundaries": _boundaries(
                    args,
                    scan_called=False,
                    publication_called=False,
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
    publication_report_path: Path,
) -> dict[str, Any]:
    scan_command = _scan_command(args)
    scan_child = _run_child_json(scan_command, scan_report_path)
    scan_report = scan_child["payload"]
    scan_valid = (
        scan_child["returncode"] == 0
        and scan_report.get("schema")
        == "missipy.github_actions.artifact_scan_once_live.v1"
        and scan_report.get("valid") is True
    )

    publication_child: dict[str, Any] | None = None
    publication_called = False
    if scan_valid and args.execute:
        publication_called = True
        publication_child = _run_child_json(
            _publication_command(args, scan_report_path),
            publication_report_path,
        )

    publication_valid = True
    if publication_child is not None:
        publication_report = publication_child["payload"]
        publication_valid = (
            publication_child["returncode"] == 0
            and publication_report.get("schema")
            == "missipy.github_actions.ready_run_copilot_issue_publication_once.v1"
            and publication_report.get("valid") is True
        )

    valid = scan_valid and publication_valid
    if not scan_valid:
        status = "scan-failed"
    elif not args.execute:
        status = "plan-complete"
    elif not publication_valid:
        status = "publication-failed"
    else:
        status = "completed"

    payload = _base_payload(
        args,
        cycle_id=cycle_id,
        cycle_report_path=cycle_report_path,
        scan_report_path=scan_report_path,
        publication_report_path=publication_report_path,
    )
    payload.update(
        {
            "valid": valid,
            "status": status,
            "issues": _child_issues(scan_child, publication_child),
            "children": {
                "artifact_scan": _child_summary(scan_child),
                "copilot_issue_publication": (
                    _child_summary(publication_child)
                    if publication_child is not None
                    else {
                        "called": False,
                        "reason": (
                            "plan_only" if scan_valid and not args.execute
                            else "scan_invalid"
                        ),
                    }
                ),
            },
            "counts": _combined_counts(scan_report, publication_child),
            "boundaries": _boundaries(
                args,
                scan_called=True,
                publication_called=publication_called,
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


def _publication_command(
    args: argparse.Namespace,
    scan_report_path: Path,
) -> tuple[str, ...]:
    command = [
        sys.executable,
        str(_absolute(args.publication_tool)),
        "--scan-report",
        str(scan_report_path),
        "--dataset-root",
        str(args.dataset_root),
        "--state-path",
        str(args.publication_state_path),
        "--policy-decision-id",
        f"{args.policy_decision_id}:issue-publication",
        "--operator-decision",
        args.operator_decision,
        "--max-runs",
        str(args.max_publications),
        "--format",
        "json",
        "--execute",
    ]
    for run_id in args.run_id:
        command.extend(("--run-id", str(run_id)))
    return tuple(command)


def _run_child_json(
    command: Sequence[str],
    report_path: Path,
) -> dict[str, Any]:
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

    persisted_payload: Mapping[str, Any]
    if payload:
        persisted_payload = payload
    else:
        persisted_payload = {
            "schema": "missipy.child_process_failure.v1",
            "valid": False,
            "returncode": completed.returncode,
            "decode_error": decode_error,
            "stderr": completed.stderr,
        }
    _write_json_atomic(report_path, persisted_payload)
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
        "report_path": "",
        "decode_error": child.get("decode_error", ""),
    }


def _child_issues(
    scan_child: Mapping[str, Any],
    publication_child: Mapping[str, Any] | None,
) -> list[str]:
    issues: list[str] = []
    for label, child in (
        ("artifact scan", scan_child),
        ("Issue publication", publication_child),
    ):
        if child is None:
            continue
        if child.get("decode_error"):
            issues.append(f"{label}: {child['decode_error']}")
        payload = _mapping(child.get("payload"))
        for issue in payload.get("issues", []):
            issues.append(f"{label}: {issue}")
        if child.get("returncode") not in (0, None) and not payload.get("issues"):
            detail = str(child.get("stderr", "")).strip()
            issues.append(
                f"{label} child failed with return code {child.get('returncode')}"
                + (f": {detail[-500:]}" if detail else "")
            )
    return issues


def _combined_counts(
    scan_report: Mapping[str, Any],
    publication_child: Mapping[str, Any] | None,
) -> dict[str, Any]:
    scan_counts = dict(_mapping(scan_report.get("counts")))
    publication_counts: dict[str, Any] = {}
    if publication_child is not None:
        publication_counts = dict(
            _mapping(_mapping(publication_child.get("payload")).get("counts"))
        )
    return {
        "artifact_scan": scan_counts,
        "copilot_issue_publication": publication_counts,
    }


def _base_payload(
    args: argparse.Namespace,
    *,
    cycle_id: str,
    cycle_report_path: Path,
    scan_report_path: Path,
    publication_report_path: Path,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "cycle_id": cycle_id,
        "mode": "execute" if args.execute else "plan",
        "policy_decision_id": args.policy_decision_id,
        "operator_decision": args.operator_decision,
        "project_config": str(args.project_config),
        "fetch_config": str(args.fetch_config),
        "dataset_root": str(args.dataset_root),
        "publication_state_path": str(args.publication_state_path),
        "reports": {
            "cycle": str(cycle_report_path),
            "artifact_scan": str(scan_report_path),
            "copilot_issue_publication": str(publication_report_path),
        },
    }


def _boundaries(
    args: argparse.Namespace,
    *,
    scan_called: bool,
    publication_called: bool,
    overlap_prevented: bool,
) -> dict[str, Any]:
    return {
        "one_shot": True,
        "polling_loop_added": False,
        "daemon_added": False,
        "fcron_remains_external_process_authority": True,
        "overlap_lock_non_blocking": True,
        "overlap_prevented": overlap_prevented,
        "existing_artifact_scan_reused": True,
        "existing_issue_publication_reused": True,
        "scan_called": scan_called,
        "publication_called": publication_called,
        "github_actions_workflow_modified": False,
        "github_actions_issue_write_permission": False,
        "remote_issue_mutation_allowed": args.execute,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
        "laboratory_execution_started": False,
    }


def _normalize_paths(args: argparse.Namespace) -> None:
    for name in (
        "project_config",
        "fetch_config",
        "dataset_root",
        "publication_state_path",
        "report_root",
        "lock_path",
    ):
        setattr(args, name, _absolute(Path(getattr(args, name))))


def _validate_args(args: argparse.Namespace) -> list[str]:
    issues: list[str] = []
    if not args.policy_decision_id.startswith("policy:"):
        issues.append("policy-decision-id must start with policy:")
    for name in ("max_runs", "max_artifacts", "max_publications"):
        if int(getattr(args, name)) <= 0:
            issues.append(name.replace("_", "-") + " must be > 0")
    if not args.project_config.is_file():
        issues.append(f"project config not found: {args.project_config}")
    if not args.fetch_config.is_file():
        issues.append(f"fetch config not found: {args.fetch_config}")
    for label, path in (
        ("scan tool", _absolute(args.scan_tool)),
        ("publication tool", _absolute(args.publication_tool)),
    ):
        if not path.is_file():
            issues.append(f"{label} not found: {path}")
    return issues


def _execute_gate_issues() -> list[str]:
    issues: list[str] = []
    for name in (
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_ISSUE_PUBLICATION_ALLOWED",
    ):
        if not _enabled(name):
            issues.append(f"{name} is not enabled")
    return issues


@contextmanager
def _exclusive_cycle_lock(path: Path) -> Iterator[TextIO]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CycleLockedError("another local cycle is already running") from exc
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


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


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
    scan_counts = _mapping(counts.get("artifact_scan"))
    publication_counts = _mapping(counts.get("copilot_issue_publication"))
    print(
        " ".join(
            (
                f"valid={payload.get('valid')}",
                f"status={payload.get('status')}",
                f"mode={payload.get('mode')}",
                f"ready={scan_counts.get('ready_run_count', 0)}",
                f"created={publication_counts.get('created_count', 0)}",
                f"replayed={publication_counts.get('replayed_count', 0)}",
                f"failed={publication_counts.get('failed_count', 0)}",
            )
        )
    )
    for issue in payload.get("issues", []):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
