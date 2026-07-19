#!/usr/bin/env python3
"""Create and verify one clean GitHub Issue-triggered research cycle.

The Projects workflow already owns the `issues: opened` trigger and resolves
that event to `requested_status=Recherche` and `request_mode=initial`.
This operator surface therefore creates one conforming Issue, attaches it to
the configured ProjectV2, discovers the unique new `issues` workflow run, waits
for successful completion, and verifies one exact three-role artifact triplet.

No workflow_dispatch is emitted, so this tool cannot create the duplicate run
pattern produced by combining Issue opening and manual dispatch.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from context.human_readable_artifact_identity_0287 import (  # noqa: E402
    matches_actions_artifact_name,
)

SCHEMA = "missipy.github.clean_research_cycle_start.v1"
PLAN_SCHEMA = "missipy.github.clean_research_cycle_plan.v1"
_REQUIRED_HEADINGS = (
    "### Question ou objectif",
    "### Résultat attendu",
)
_ROLE_NAMES = {
    "authoritative_request": "autodoc-authoritative-request",
    "copilot_advisory": "autodoc-copilot-advisory",
    "run_manifest": "autodoc-dual-artifact-manifest",
}
_REMOTE_GATE = "AUTODOC_REMOTE_MUTATION_ALLOWED"
_ISSUE_GATE = "AUTODOC_ISSUE_CREATION_ALLOWED"
_PROJECT_GATE = "AUTODOC_PROJECT_PROJECTION_ALLOWED"


class CleanResearchCycleError(RuntimeError):
    """Fail-closed error retaining already-observed remote identities."""

    def __init__(
        self,
        message: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.context = dict(context or {})


@dataclass(frozen=True, slots=True)
class CyclePlan:
    repository: str
    project_owner: str
    project_number: int
    workflow: str
    ref: str
    title: str
    body: str
    cycle_ref: str
    token_env: str
    wait_seconds: int
    poll_seconds: int
    plan_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if "/" not in self.repository:
            raise CleanResearchCycleError(
                "repository must be OWNER/REPO"
            )
        if self.project_number <= 0:
            raise CleanResearchCycleError(
                "project-number must be > 0"
            )
        if not self.title.startswith("[Recherche] "):
            raise CleanResearchCycleError(
                "title must start with '[Recherche] '"
            )
        for heading in _REQUIRED_HEADINGS:
            if heading not in self.body:
                raise CleanResearchCycleError(
                    f"issue body must contain heading {heading!r}"
                )
        if not self.cycle_ref.strip():
            raise CleanResearchCycleError(
                "cycle-ref must not be empty"
            )
        if self.wait_seconds <= 0 or self.poll_seconds <= 0:
            raise CleanResearchCycleError(
                "wait-seconds and poll-seconds must be > 0"
            )
        if self.poll_seconds > self.wait_seconds:
            raise CleanResearchCycleError(
                "poll-seconds cannot exceed wait-seconds"
            )
        object.__setattr__(
            self,
            "plan_digest",
            _digest(self.to_plan_mapping(include_digest=False)),
        )

    @property
    def marked_body(self) -> str:
        marker = f"<!-- autodoc-cycle-ref:{self.cycle_ref} -->"
        return self.body.rstrip() + "\n\n" + marker + "\n"

    def to_plan_mapping(
        self,
        *,
        include_digest: bool = True,
    ) -> dict[str, Any]:
        payload = {
            "schema": PLAN_SCHEMA,
            "repository": self.repository,
            "project_owner": self.project_owner,
            "project_number": self.project_number,
            "workflow": self.workflow,
            "ref": self.ref,
            "title": self.title,
            "body_sha256": hashlib.sha256(
                self.marked_body.encode("utf-8")
            ).hexdigest(),
            "cycle_ref": self.cycle_ref,
            "token_env": self.token_env,
            "wait_seconds": self.wait_seconds,
            "poll_seconds": self.poll_seconds,
            "trigger": "issues:opened",
            "requested_status": "Recherche",
            "request_mode": "initial",
            "workflow_dispatch_emitted": False,
        }
        if include_digest:
            payload["plan_digest"] = self.plan_digest
        return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        default="newicody/projects",
    )
    parser.add_argument("--project-owner", required=True)
    parser.add_argument("--project-number", type=int, required=True)
    parser.add_argument(
        "--workflow",
        default="autodoc-controlled-research.yml",
    )
    parser.add_argument("--ref", default="master")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body-file", type=Path, required=True)
    parser.add_argument("--cycle-ref", required=True)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--wait-seconds", type=int, default=900)
    parser.add_argument("--poll-seconds", type=int, default=5)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-plan-digest", default="")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(
        tuple(sys.argv[1:] if argv is None else argv)
    )
    output = _absolute_output(args.output)
    try:
        plan = _build_plan(args)
        if not args.execute:
            payload = _plan_report(plan)
        else:
            payload = execute_clean_cycle(
                plan,
                gh_command=str(args.gh_command),
                confirm_plan_digest=str(
                    args.confirm_plan_digest
                ),
            )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        context = (
            dict(exc.context)
            if isinstance(exc, CleanResearchCycleError)
            else {}
        )
        payload = {
            "schema": SCHEMA,
            "valid": False,
            "mode": "execute" if args.execute else "plan",
            "status": "failed",
            "issues": [f"{type(exc).__name__}: {exc}"],
            "context": context,
            "boundaries": _boundaries(
                execute=bool(args.execute),
                issue_created=bool(context.get("issue")),
                project_item_added=bool(
                    context.get("project_item")
                ),
                run_discovered=bool(context.get("run")),
                artifacts_verified=False,
            ),
        }

    _write_json_atomic(output, payload)
    _emit(payload, str(args.format))
    return 0 if payload.get("valid") is True else 2


def _build_plan(args: argparse.Namespace) -> CyclePlan:
    body_path = _absolute_input(args.body_file)
    if not body_path.is_file():
        raise CleanResearchCycleError(
            f"body-file not found: {body_path}"
        )
    return CyclePlan(
        repository=str(args.repository).strip(),
        project_owner=str(args.project_owner).strip(),
        project_number=int(args.project_number),
        workflow=str(args.workflow).strip(),
        ref=str(args.ref).strip(),
        title=str(args.title).strip(),
        body=body_path.read_text(encoding="utf-8"),
        cycle_ref=str(args.cycle_ref).strip(),
        token_env=str(args.token_env).strip(),
        wait_seconds=int(args.wait_seconds),
        poll_seconds=int(args.poll_seconds),
    )


def _plan_report(plan: CyclePlan) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "valid": True,
        "mode": "plan",
        "status": "confirmation-required",
        "issues": [],
        "plan": plan.to_plan_mapping(),
        "plan_digest": plan.plan_digest,
        "next_action": (
            "rerun with --execute and --confirm-plan-digest"
        ),
        "boundaries": _boundaries(
            execute=False,
            issue_created=False,
            project_item_added=False,
            run_discovered=False,
            artifacts_verified=False,
        ),
    }


def execute_clean_cycle(
    plan: CyclePlan,
    *,
    gh_command: str,
    confirm_plan_digest: str,
    command_runner: Callable[..., Mapping[str, Any]] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    if confirm_plan_digest.strip() != plan.plan_digest:
        raise CleanResearchCycleError(
            "confirm-plan-digest mismatch"
        )
    for gate in (_REMOTE_GATE, _ISSUE_GATE, _PROJECT_GATE):
        _require_gate(gate)

    token = os.environ.get(plan.token_env, "").strip()
    if not token:
        raise CleanResearchCycleError(
            f"missing token environment {plan.token_env}"
        )

    runner = command_runner or _run_gh_json
    environment = dict(os.environ)
    environment["GH_TOKEN"] = token
    context: dict[str, Any] = {}

    before_runs = _list_issue_runs(
        runner,
        gh_command=gh_command,
        plan=plan,
        environment=environment,
    )
    before_ids = {
        int(value["databaseId"])
        for value in before_runs
        if isinstance(value.get("databaseId"), int)
    }

    issue = _create_issue(
        runner,
        gh_command=gh_command,
        plan=plan,
        environment=environment,
    )
    context["issue"] = issue

    try:
        project_item = _add_issue_to_project(
            runner,
            gh_command=gh_command,
            plan=plan,
            issue_url=_required_text(issue, "html_url"),
            environment=environment,
        )
        context["project_item"] = project_item

        run = _wait_for_unique_new_run(
            runner,
            gh_command=gh_command,
            plan=plan,
            before_ids=before_ids,
            environment=environment,
            sleeper=sleeper,
            monotonic=monotonic,
        )
        context["run"] = run

        completed = _wait_for_success(
            runner,
            gh_command=gh_command,
            plan=plan,
            run_id=int(run["databaseId"]),
            environment=environment,
            sleeper=sleeper,
            monotonic=monotonic,
        )
        context["run"] = completed

        artifacts = _verify_artifact_triplet(
            runner,
            gh_command=gh_command,
            plan=plan,
            run_id=int(run["databaseId"]),
            environment=environment,
        )
    except CleanResearchCycleError as exc:
        merged = dict(context)
        merged.update(exc.context)
        raise CleanResearchCycleError(
            str(exc),
            context=merged,
        ) from exc

    return {
        "schema": SCHEMA,
        "valid": True,
        "mode": "execute",
        "status": "clean-cycle-ready-for-local-fetch",
        "issues": [],
        "plan": plan.to_plan_mapping(),
        "plan_digest": plan.plan_digest,
        "issue": issue,
        "project_item": project_item,
        "run": completed,
        "run_id": int(completed["databaseId"]),
        "artifact_triplet": artifacts,
        "counts": {
            "issue_count": 1,
            "project_item_count": 1,
            "workflow_run_count": 1,
            "artifact_count": 3,
        },
        "next_action": (
            "run the canonical local artifact fetch for this run"
        ),
        "boundaries": _boundaries(
            execute=True,
            issue_created=True,
            project_item_added=True,
            run_discovered=True,
            artifacts_verified=True,
        ),
    }


def _create_issue(
    runner: Callable[..., Mapping[str, Any]],
    *,
    gh_command: str,
    plan: CyclePlan,
    environment: Mapping[str, str],
) -> dict[str, Any]:
    payload = runner(
        (
            gh_command,
            "api",
            "-X",
            "POST",
            f"repos/{plan.repository}/issues",
            "--input",
            "-",
        ),
        environment=environment,
        stdin_payload={
            "title": plan.title,
            "body": plan.marked_body,
        },
        label="create issue",
    )
    number = payload.get("number")
    if not isinstance(number, int) or number <= 0:
        raise CleanResearchCycleError(
            "created Issue has no valid number"
        )
    if payload.get("state") != "open":
        raise CleanResearchCycleError(
            "created Issue is not open"
        )
    return {
        "number": number,
        "title": _required_text(payload, "title"),
        "url": _required_text(payload, "html_url"),
        "html_url": _required_text(payload, "html_url"),
        "node_id": _required_text(payload, "node_id"),
        "state": "open",
        "cycle_ref": plan.cycle_ref,
    }


def _add_issue_to_project(
    runner: Callable[..., Mapping[str, Any]],
    *,
    gh_command: str,
    plan: CyclePlan,
    issue_url: str,
    environment: Mapping[str, str],
) -> dict[str, Any]:
    payload = runner(
        (
            gh_command,
            "project",
            "item-add",
            str(plan.project_number),
            "--owner",
            plan.project_owner,
            "--url",
            issue_url,
            "--format",
            "json",
        ),
        environment=environment,
        label="add Issue to ProjectV2",
    )
    item_id = str(
        payload.get("id")
        or payload.get("item", {}).get("id")
        if isinstance(payload.get("item"), Mapping)
        else payload.get("id")
        or ""
    ).strip()
    if not item_id:
        raise CleanResearchCycleError(
            "ProjectV2 item-add returned no item id"
        )
    return {
        "id": item_id,
        "project_owner": plan.project_owner,
        "project_number": plan.project_number,
        "issue_url": issue_url,
    }


def _list_issue_runs(
    runner: Callable[..., Mapping[str, Any]],
    *,
    gh_command: str,
    plan: CyclePlan,
    environment: Mapping[str, str],
) -> list[dict[str, Any]]:
    payload = runner(
        (
            gh_command,
            "run",
            "list",
            "--repo",
            plan.repository,
            "--workflow",
            plan.workflow,
            "--event",
            "issues",
            "--limit",
            "100",
            "--json",
            (
                "databaseId,displayTitle,event,status,conclusion,"
                "createdAt,updatedAt,url,workflowName,headBranch"
            ),
        ),
        environment=environment,
        label="list Issue workflow runs",
    )
    values = payload.get("items")
    if not isinstance(values, list):
        raise CleanResearchCycleError(
            "run list payload must expose items"
        )
    return [
        dict(value)
        for value in values
        if isinstance(value, Mapping)
    ]


def _wait_for_unique_new_run(
    runner: Callable[..., Mapping[str, Any]],
    *,
    gh_command: str,
    plan: CyclePlan,
    before_ids: set[int],
    environment: Mapping[str, str],
    sleeper: Callable[[float], None],
    monotonic: Callable[[], float],
) -> dict[str, Any]:
    deadline = monotonic() + plan.wait_seconds
    while True:
        runs = _list_issue_runs(
            runner,
            gh_command=gh_command,
            plan=plan,
            environment=environment,
        )
        matches = [
            run
            for run in runs
            if isinstance(run.get("databaseId"), int)
            and int(run["databaseId"]) not in before_ids
            and run.get("event") == "issues"
            and run.get("displayTitle") == plan.title
            and run.get("workflowName")
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CleanResearchCycleError(
                "more than one new Issue-triggered workflow run "
                "matches the created Issue",
                context={"matching_runs": matches},
            )
        if monotonic() >= deadline:
            raise CleanResearchCycleError(
                "timed out waiting for the Issue-triggered workflow run"
            )
        sleeper(float(plan.poll_seconds))


def _wait_for_success(
    runner: Callable[..., Mapping[str, Any]],
    *,
    gh_command: str,
    plan: CyclePlan,
    run_id: int,
    environment: Mapping[str, str],
    sleeper: Callable[[float], None],
    monotonic: Callable[[], float],
) -> dict[str, Any]:
    deadline = monotonic() + plan.wait_seconds
    while True:
        payload = runner(
            (
                gh_command,
                "run",
                "view",
                str(run_id),
                "--repo",
                plan.repository,
                "--json",
                (
                    "databaseId,displayTitle,event,status,conclusion,"
                    "createdAt,updatedAt,url,workflowName,headBranch"
                ),
            ),
            environment=environment,
            label="view workflow run",
        )
        status = str(payload.get("status", "")).strip()
        conclusion = str(payload.get("conclusion", "")).strip()
        if status == "completed":
            if conclusion != "success":
                raise CleanResearchCycleError(
                    "Issue-triggered workflow did not complete successfully",
                    context={"run": dict(payload)},
                )
            return dict(payload)
        if monotonic() >= deadline:
            raise CleanResearchCycleError(
                "timed out waiting for workflow completion",
                context={"run": dict(payload)},
            )
        sleeper(float(plan.poll_seconds))


def _verify_artifact_triplet(
    runner: Callable[..., Mapping[str, Any]],
    *,
    gh_command: str,
    plan: CyclePlan,
    run_id: int,
    environment: Mapping[str, str],
) -> dict[str, Any]:
    payload = runner(
        (
            gh_command,
            "api",
            "-X",
            "GET",
            f"repos/{plan.repository}/actions/runs/{run_id}/artifacts",
            "-f",
            "per_page=100",
        ),
        environment=environment,
        label="list workflow artifacts",
    )
    values = payload.get("artifacts")
    if not isinstance(values, list):
        raise CleanResearchCycleError(
            "artifact API response must expose artifacts"
        )

    selected: dict[str, dict[str, Any]] = {}
    for role, legacy_name in _ROLE_NAMES.items():
        matches = [
            value
            for value in values
            if isinstance(value, Mapping)
            and matches_actions_artifact_name(
                str(value.get("name", "")),
                legacy_name,
            )
        ]
        if len(matches) != 1:
            raise CleanResearchCycleError(
                f"role {role} must have exactly one artifact, "
                f"found {len(matches)}",
                context={
                    "artifact_role_counts": {
                        role: len(matches),
                    }
                },
            )
        value = matches[0]
        if value.get("expired") is True:
            raise CleanResearchCycleError(
                f"artifact for role {role} is expired"
            )
        artifact_id = value.get("id")
        if not isinstance(artifact_id, int) or artifact_id <= 0:
            raise CleanResearchCycleError(
                f"artifact for role {role} has no valid id"
            )
        selected[role] = {
            "artifact_id": artifact_id,
            "artifact_name": _required_text(value, "name"),
            "expired": False,
        }

    if len(values) != 3:
        raise CleanResearchCycleError(
            "clean workflow run must expose exactly three artifacts",
            context={
                "artifact_total_count": len(values),
                "selected_artifacts": selected,
            },
        )
    return selected


def _run_gh_json(
    command: Sequence[str],
    *,
    environment: Mapping[str, str],
    label: str,
    stdin_payload: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    completed = subprocess.run(
        list(command),
        cwd=_REPO_ROOT,
        env=dict(environment),
        input=(
            None
            if stdin_payload is None
            else json.dumps(stdin_payload, ensure_ascii=False)
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise CleanResearchCycleError(
            f"{label} failed with return code "
            f"{completed.returncode}: {detail[-800:]}"
        )
    try:
        decoded = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise CleanResearchCycleError(
            f"{label} did not return valid JSON"
        ) from exc
    if isinstance(decoded, list):
        return {"items": decoded}
    if not isinstance(decoded, Mapping):
        raise CleanResearchCycleError(
            f"{label} JSON must be an object or list"
        )
    return decoded


def _require_gate(name: str) -> None:
    value = os.environ.get(name, "").strip().casefold()
    if value not in {"1", "true", "yes", "on"}:
        raise CleanResearchCycleError(
            f"missing explicit mutation gate {name}"
        )


def _required_text(
    value: Mapping[str, Any],
    name: str,
) -> str:
    candidate = value.get(name)
    if not isinstance(candidate, str) or not candidate.strip():
        raise CleanResearchCycleError(
            f"{name} must not be empty"
        )
    return candidate.strip()


def _digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _absolute_input(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (
        _REPO_ROOT / path
    ).resolve()


def _absolute_output(path: Path) -> Path:
    return path if path.is_absolute() else _REPO_ROOT / path


def _write_json_atomic(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _boundaries(
    *,
    execute: bool,
    issue_created: bool,
    project_item_added: bool,
    run_discovered: bool,
    artifacts_verified: bool,
) -> dict[str, object]:
    return {
        "operator_entrypoint_only": True,
        "issue_opened_trigger_reused": True,
        "workflow_dispatch_emitted": False,
        "requested_status_resolved_by_workflow": "Recherche",
        "request_mode_resolved_by_workflow": "initial",
        "remote_mutation_requested": execute,
        "issue_created": issue_created,
        "project_item_added": project_item_added,
        "run_discovered": run_discovered,
        "artifact_triplet_verified": artifacts_verified,
        "exact_one_workflow_run_required": True,
        "exact_one_artifact_per_role_required": True,
        "local_artifact_fetch_started": False,
        "sql_write_performed": False,
        "qdrant_write_performed": False,
        "scheduler_dispatch_started": False,
        "laboratory_execution_started": False,
        "secret_value_serialized": False,
    }


def _emit(payload: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return
    print(
        " ".join(
            (
                f"valid={str(payload.get('valid')).lower()}",
                f"mode={payload.get('mode', '')}",
                f"status={payload.get('status', '')}",
                f"plan_digest={payload.get('plan_digest', '')}",
                f"run_id={payload.get('run_id', '')}",
            )
        )
    )
    for issue in payload.get("issues", ()):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
