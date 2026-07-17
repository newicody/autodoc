#!/usr/bin/env python3
"""Publish Copilot v2 Issue comments from locally fetched ready runs.

This is a bounded local connector.  It never downloads from GitHub Actions and
never changes the Projects workflow.  It reuses the existing v2 preview builder
and controlled Issue-comment publisher, and writes a local completion receipt
only after successful GitHub readback (including idempotent replay).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_actions_ready_run_copilot_issue_publication_once_0287 import (  # noqa: E402
    RESULT_SCHEMA,
    STATE_SCHEMA,
    completed_publication_keys,
    durable_raw_member_paths,
    select_ready_run_publication_candidates,
)

_DEFAULT_DATASET_ROOT = Path(".var/server_datasets/github_artifacts")
_DEFAULT_STATE_PATH = _DEFAULT_DATASET_ROOT / "index/copilot_issue_publication_state.json"
_DEFAULT_WORK_ROOT = Path(".var/reports/github_actions_ready_run_copilot_issue_publication")
_DEFAULT_BUILDER = Path(
    "templates/github/projects-repository/scripts/"
    "build_copilot_advisory_v2_publication_preview.py"
)
_DEFAULT_PUBLISHER = Path("tools/publish_github_copilot_advisory_v2_issue_comment_0287.py")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Publish bounded Copilot v2 Issue comments from ready_runs already "
            "present in the durable local GitHub artifact dataset."
        )
    )
    parser.add_argument("--scan-report", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, default=_DEFAULT_DATASET_ROOT)
    parser.add_argument("--state-path", type=Path, default=_DEFAULT_STATE_PATH)
    parser.add_argument("--work-root", type=Path, default=_DEFAULT_WORK_ROOT)
    parser.add_argument("--preview-builder", type=Path, default=_DEFAULT_BUILDER)
    parser.add_argument("--publisher-tool", type=Path, default=_DEFAULT_PUBLISHER)
    parser.add_argument("--run-id", action="append", default=[])
    parser.add_argument("--max-runs", type=int, default=10)
    parser.add_argument("--include-completed", action="store_true")
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument("--operator-decision", choices=("approve",), required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    issues: list[str] = []
    if not args.policy_decision_id.startswith("policy:"):
        issues.append("policy-decision-id must start with policy:")
    if args.max_runs <= 0:
        issues.append("max-runs must be > 0")

    scan_report = _read_mapping(args.scan_report)
    state = _read_optional_state(args.state_path)
    candidates = ()
    if not issues:
        try:
            candidates = select_ready_run_publication_candidates(
                scan_report,
                completed_keys=completed_publication_keys(state),
                requested_run_ids=tuple(args.run_id),
                max_runs=args.max_runs,
                include_completed=args.include_completed,
            )
        except (TypeError, ValueError) as exc:
            issues.append(str(exc))

    if args.execute:
        for name in (
            "AUTODOC_REMOTE_MUTATION_ALLOWED",
            "AUTODOC_ISSUE_PUBLICATION_ALLOWED",
        ):
            if not _enabled(name):
                issues.append(f"{name} is not enabled")

    results: list[dict[str, Any]] = []
    completed = dict(state.get("completed", {})) if state else {}
    if not issues:
        for candidate in candidates:
            result = _process_candidate(args, candidate.to_mapping())
            results.append(result)
            if result.get("completed") is True:
                completed[candidate.publication_key] = {
                    "repository": candidate.repository,
                    "run_id": candidate.run_id,
                    "handoff_ref": candidate.handoff_ref,
                    "publication_key": candidate.publication_key,
                    "response_digest": result.get("response_digest", ""),
                    "marker": result.get("marker", ""),
                    "mutation_action": result.get("mutation_action", ""),
                    "readback_verified": True,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }
                _write_json_atomic(
                    args.state_path,
                    {"schema": STATE_SCHEMA, "completed": completed},
                )

    failed = sum(1 for item in results if item.get("status") == "failed")
    created = sum(1 for item in results if item.get("mutation_action") == "created")
    replayed = sum(1 for item in results if item.get("mutation_action") == "replay-noop")
    planned = sum(1 for item in results if item.get("status") == "planned")
    payload = {
        "schema": RESULT_SCHEMA,
        "valid": not issues and failed == 0,
        "issues": issues,
        "mode": "execute" if args.execute else "preview",
        "policy_decision_id": args.policy_decision_id,
        "operator_decision": args.operator_decision,
        "scan_report": str(args.scan_report),
        "dataset_root": str(args.dataset_root),
        "state_path": str(args.state_path),
        "counts": {
            "candidate_count": len(candidates),
            "planned_count": planned,
            "created_count": created,
            "replayed_count": replayed,
            "failed_count": failed,
        },
        "results": results,
        "boundaries": {
            "local_connector_only": True,
            "github_actions_redownload": False,
            "projects_workflow_modified": False,
            "workflow_issue_write_permission": False,
            "ready_runs_only": True,
            "durable_raw_dataset_read": True,
            "remote_mutation_allowed": args.execute,
            "remote_mutation_performed": created > 0,
            "operator_decision_required": True,
            "plan_digest_confirmed": args.execute,
            "readback_required": True,
            "state_written_after_readback_only": True,
            "sql_write_allowed": False,
            "qdrant_write_allowed": False,
            "scheduler_modified": False,
            "laboratory_execution_started": False,
        },
    }
    _emit(payload, args.format)
    return 0 if payload["valid"] else 2


def _process_candidate(args: argparse.Namespace, candidate: Mapping[str, Any]) -> dict[str, Any]:
    repository = str(candidate["repository"])
    run_id = str(candidate["run_id"])
    result: dict[str, Any] = {
        "repository": repository,
        "run_id": run_id,
        "handoff_ref": candidate["handoff_ref"],
        "publication_key": candidate["publication_key"],
        "status": "failed",
        "completed": False,
        "mutation_action": "none",
        "readback_verified": False,
    }
    try:
        from context.github_actions_ready_run_copilot_issue_publication_once_0287 import (
            ReadyRunPublicationCandidate,
        )

        typed_candidate = ReadyRunPublicationCandidate(
            repository=repository,
            run_id=run_id,
            handoff_ref=str(candidate["handoff_ref"]),
            artifact_ids=dict(candidate["artifact_ids"]),
            publication_key=str(candidate["publication_key"]),
        )
        members = durable_raw_member_paths(args.dataset_root, typed_candidate)
        for role, path in members.items():
            _require_regular_file(role, path)

        request = _read_mapping(members["authoritative_request"])
        if request.get("schema") != "missipy.github.authoritative_request.v1":
            raise ValueError("unexpected authoritative request schema")
        if request.get("repository") != repository:
            raise ValueError("authoritative request repository mismatch")
        issue_number = int(request.get("issue_number") or 0)
        if issue_number <= 0:
            raise ValueError("authoritative request issue_number must be positive")

        run_work = args.work_root / repository.replace("/", "__") / run_id
        preview_path = run_work / "copilot_advisory_v2_publication_preview.json"
        plan_path = run_work / "issue_comment_plan.json"
        execute_path = run_work / "issue_comment_execute.json"
        _run_json_command(
            (
                sys.executable,
                str(_absolute(args.preview_builder)),
                "--advisory",
                str(members["copilot_advisory"]),
                "--request",
                str(members["authoritative_request"]),
                "--manifest",
                str(members["run_manifest"]),
                "--run-id",
                run_id,
                "--repository",
                repository,
                "--issue-number",
                str(issue_number),
                "--output",
                str(preview_path),
            ),
            output_path=None,
            parse_json=False,
        )
        preview = _read_mapping(preview_path)
        result["issue_number"] = issue_number
        result["preview_path"] = str(preview_path)
        result["response_digest"] = str(preview.get("response_digest", ""))

        plan = _run_json_command(
            _publisher_command(
                args,
                repository=repository,
                issue_number=issue_number,
                preview_path=preview_path,
                execute=False,
                plan_digest="",
            ),
            output_path=plan_path,
        )
        plan_payload = _mapping(plan.get("plan"))
        if plan_payload.get("valid") is not True:
            raise ValueError("Issue publication plan is invalid")
        plan_digest = str(plan_payload.get("plan_digest", ""))
        if not plan_digest:
            raise ValueError("Issue publication plan digest is missing")
        result["plan_path"] = str(plan_path)
        result["plan_digest"] = plan_digest
        result["marker"] = str(plan_payload.get("marker", ""))

        if not args.execute:
            result["status"] = "planned"
            return result

        execution = _run_json_command(
            _publisher_command(
                args,
                repository=repository,
                issue_number=issue_number,
                preview_path=preview_path,
                execute=True,
                plan_digest=plan_digest,
            ),
            output_path=execute_path,
        )
        result["execute_path"] = str(execute_path)
        result["mutation_action"] = str(execution.get("mutation_action", "none"))
        result["readback_verified"] = execution.get("readback_verified") is True
        if not result["readback_verified"]:
            raise ValueError("Issue publication readback was not verified")
        if result["mutation_action"] not in {"created", "replay-noop"}:
            raise ValueError("Issue publication did not create or replay")
        result["published_comment"] = dict(_mapping(execution.get("published_comment")))
        result["status"] = "completed"
        result["completed"] = True
        return result
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        result["error"] = str(exc)
        return result


def _publisher_command(
    args: argparse.Namespace,
    *,
    repository: str,
    issue_number: int,
    preview_path: Path,
    execute: bool,
    plan_digest: str,
) -> tuple[str, ...]:
    command = [
        sys.executable,
        str(_absolute(args.publisher_tool)),
        "--repository",
        repository,
        "--issue-number",
        str(issue_number),
        "--preview",
        str(preview_path),
        "--policy-decision-id",
        args.policy_decision_id,
        "--operator-decision",
        args.operator_decision,
        "--gh-command",
        args.gh_command,
        "--format",
        "json",
    ]
    if execute:
        command.extend(("--execute", "--confirm-plan-digest", plan_digest))
    return tuple(command)


def _run_json_command(
    command: Sequence[str],
    *,
    output_path: Path | None,
    parse_json: bool = True,
) -> dict[str, Any]:
    completed = subprocess.run(
        list(command),
        cwd=_REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown failure"
        raise RuntimeError(f"child command failed ({completed.returncode}): {detail[-2000:]}")
    payload: dict[str, Any] = {}
    if parse_json and completed.stdout.strip():
        decoded = json.loads(completed.stdout)
        if isinstance(decoded, Mapping):
            payload = dict(decoded)
    if output_path is not None:
        _write_json_atomic(output_path, payload)
    return payload


def _read_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return dict(payload)


def _read_optional_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _read_mapping(path)


def _require_regular_file(role: str, path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"missing durable raw member for {role}: {path}")


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else _REPO_ROOT / path


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


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
                f"mode={payload.get('mode')}",
                f"candidates={counts.get('candidate_count', 0)}",
                f"planned={counts.get('planned_count', 0)}",
                f"created={counts.get('created_count', 0)}",
                f"replayed={counts.get('replayed_count', 0)}",
                f"failed={counts.get('failed_count', 0)}",
            )
        )
    )
    for issue in payload.get("issues", []):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
