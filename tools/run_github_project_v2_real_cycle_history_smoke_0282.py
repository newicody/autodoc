#!/usr/bin/env python3
"""Run the real ProjectV2 cycle-history smoke for phase 0282-r8.

Preview is the default. Execution requires:

* ``--operator-decision approve``;
* ``--execute``;
* an exact ``--confirm-smoke-digest`` obtained from an earlier preview.

The tool reuses the existing 0282-r7 adapter rather than adding a second
GitHub mutation transport.
"""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
from typing import Any, Callable, Mapping, Sequence

from context.github_project_v2_append_only_cycle_history_0282 import (
    CYCLE_HISTORY_RESULT_SCHEMA,
    GitHubProjectV2AppendOnlyCycleHistoryResult,
    GitHubProjectV2CycleHistoryEntry,
)
from context.github_project_v2_parent_sub_ticket_mutation_plan_0282 import (
    GitHubProjectV2IssueSnapshot,
)
from context.github_project_v2_real_cycle_history_smoke_0282 import (
    GitHubProjectV2RealCycleHistorySmokeCommand,
    build_github_project_v2_real_cycle_history_smoke,
)
from context.github_project_v2_theme_grouping_deployment_plan_0282 import (
    GitHubProjectV2ThemeAssignmentSpec,
    GitHubProjectV2ThemeFieldSnapshot,
    GitHubProjectV2ThemeGroupingDeploymentCommand,
    GitHubProjectV2ThemeOptionSnapshot,
    GitHubProjectV2ThemeOptionSpec,
    GitHubProjectV2ViewGroupingSnapshot,
)
from tools.apply_github_project_v2_operator_authorized_mutations_0282 import (
    main as run_operator_authorized_adapter,
)


TOOL_SCHEMA = (
    "missipy.github.project_v2_real_cycle_history_smoke_tool.v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    ".var/reports/github_project_v2_real_cycle_history_0282"
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build deterministic r5/r6 plans from an r4 history and "
            "preview or execute them through the existing r7 adapter."
        )
    )
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--issues", type=Path, required=True)
    parser.add_argument("--theme-command", type=Path)
    parser.add_argument("--next-cycle-title", required=True)
    parser.add_argument("--next-cycle-summary", required=True)
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument(
        "--operator-decision",
        choices=("approve",),
        required=True,
    )
    parser.add_argument(
        "--source-artifact-ref",
        action="append",
        default=[],
    )
    parser.add_argument(
        "--decision-ref",
        action="append",
        default=[],
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-smoke-digest", default="")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    return run(
        args,
        adapter_main=run_operator_authorized_adapter,
    )


def run(
    args: argparse.Namespace,
    *,
    adapter_main: Callable[[Sequence[str] | None], int],
) -> int:
    history = _load_history(args.history)
    issues = _load_issue_snapshots(args.issues)
    theme_command = (
        _load_theme_command(args.theme_command)
        if args.theme_command is not None
        else None
    )

    smoke = build_github_project_v2_real_cycle_history_smoke(
        GitHubProjectV2RealCycleHistorySmokeCommand(
            history=history,
            existing_issues=issues,
            next_cycle_title=args.next_cycle_title,
            next_cycle_summary=args.next_cycle_summary,
            policy_decision_id=args.policy_decision_id,
            operator_decision=args.operator_decision,
            theme_command=theme_command,
            source_artifact_refs=tuple(args.source_artifact_ref),
            decision_refs=tuple(args.decision_ref),
        )
    )

    run_dir = (
        args.output_root
        / (smoke.smoke_digest[:16] or "invalid")
    )
    run_dir.mkdir(parents=True, exist_ok=True)

    parent_plan_path = run_dir / "parent_sub_ticket_plan.json"
    theme_plan_path = run_dir / "theme_grouping_plan.json"
    smoke_path = run_dir / "smoke_result.json"
    adapter_path = run_dir / "adapter_report.json"
    report_path = run_dir / "tool_report.json"

    write_actions: dict[str, str] = {}
    write_actions[parent_plan_path.name] = _write_json(
        parent_plan_path,
        smoke.parent_plan.to_json_dict(),
    )
    if smoke.theme_plan is not None:
        write_actions[theme_plan_path.name] = _write_json(
            theme_plan_path,
            smoke.theme_plan.to_json_dict(),
        )
    write_actions[smoke_path.name] = _write_json(
        smoke_path,
        smoke.to_json_dict(),
    )

    report: dict[str, Any] = {
        "schema": TOOL_SCHEMA,
        "mode": "execute" if args.execute else "preview",
        "valid": smoke.valid,
        "issues": list(smoke.issues),
        "action": smoke.action,
        "smoke_ref": smoke.smoke_ref,
        "smoke_digest": smoke.smoke_digest,
        "history_ref": smoke.history_ref,
        "output_dir": str(run_dir.resolve()),
        "parent_plan_path": str(parent_plan_path.resolve()),
        "theme_plan_path": (
            str(theme_plan_path.resolve())
            if smoke.theme_plan is not None
            else ""
        ),
        "smoke_result_path": str(smoke_path.resolve()),
        "adapter_report_path": str(adapter_path.resolve()),
        "write_actions": write_actions,
        "github_mutation_performed": False,
        "partial_execution": False,
        "projects_repository_change_required": False,
        "boundaries": {
            "existing_r7_adapter_reused": True,
            "preview_is_default": True,
            "exact_smoke_digest_required_for_execution": True,
            "scheduler_modified": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
        },
    }

    if not smoke.valid:
        write_actions[report_path.name] = _write_json(
            report_path,
            report,
        )
        _emit(report, args.format)
        return 2

    if (
        args.execute
        and args.confirm_smoke_digest != smoke.smoke_digest
    ):
        report["execution_error"] = (
            "confirm-smoke-digest mismatch"
        )
        write_actions[report_path.name] = _write_json(
            report_path,
            report,
        )
        _emit(report, args.format)
        return 3

    adapter_args = [
        "--parent-plan",
        str(parent_plan_path),
        "--operator-decision",
        args.operator_decision,
        "--gh-command",
        args.gh_command,
        "--format",
        "json",
    ]
    if smoke.theme_plan is not None:
        adapter_args.extend(
            ["--theme-plan", str(theme_plan_path)]
        )
    if args.execute:
        adapter_args.extend(
            [
                "--execute",
                "--confirm-parent-plan-digest",
                smoke.parent_plan.plan_digest,
            ]
        )
        if smoke.theme_plan is not None:
            adapter_args.extend(
                [
                    "--confirm-theme-plan-digest",
                    smoke.theme_plan.plan_digest,
                ]
            )

    adapter_output = io.StringIO()
    with redirect_stdout(adapter_output):
        adapter_return_code = adapter_main(adapter_args)

    adapter_text = adapter_output.getvalue().strip()
    try:
        adapter_report = json.loads(adapter_text)
    except json.JSONDecodeError:
        adapter_report = {
            "schema": "invalid-adapter-output",
            "raw_output": adapter_text,
        }
        if adapter_return_code == 0:
            adapter_return_code = 4

    write_actions[adapter_path.name] = _write_json(
        adapter_path,
        adapter_report,
    )
    report["adapter_return_code"] = adapter_return_code
    report["adapter_report"] = adapter_report
    report["github_mutation_performed"] = bool(
        _mapping(adapter_report).get(
            "github_mutation_performed",
            False,
        )
    )
    report["partial_execution"] = bool(
        _mapping(adapter_report).get(
            "partial_execution",
            False,
        )
    )
    report["valid"] = adapter_return_code == 0

    write_actions[report_path.name] = _write_json(
        report_path,
        report,
    )
    _emit(report, args.format)
    return adapter_return_code


def _load_history(
    path: Path,
) -> GitHubProjectV2AppendOnlyCycleHistoryResult:
    payload = _read_object(path)
    if payload.get("schema") != CYCLE_HISTORY_RESULT_SCHEMA:
        raise SystemExit(f"{path}: unexpected history schema")

    entries = tuple(
        GitHubProjectV2CycleHistoryEntry(
            entry_ref=str(entry["entry_ref"]),
            entry_digest=str(entry["entry_digest"]),
            cycle_ref=str(entry["cycle_ref"]),
            lineage_digest=str(entry["lineage_digest"]),
            cycle_ordinal=int(entry["cycle_ordinal"]),
            repository=str(entry["repository"]),
            project_id=str(entry["project_id"]),
            project_item_ref=str(entry["project_item_ref"]),
            issue_ref=str(entry["issue_ref"]),
            root_issue_ref=str(entry["root_issue_ref"]),
            parent_issue_ref=str(
                entry.get("parent_issue_ref", "")
            ),
            previous_cycle_ref=str(
                entry.get("previous_cycle_ref", "")
            ),
            status_revision_ref=str(
                entry["status_revision_ref"]
            ),
            status_name=str(entry["status_name"]),
            sub_issue_refs=tuple(
                str(value)
                for value in entry.get("sub_issue_refs", [])
            ),
            theme_refs=tuple(
                str(value)
                for value in entry.get("theme_refs", [])
            ),
            theme_values=tuple(
                str(value)
                for value in entry.get("theme_values", [])
            ),
            result_issue_ref=str(
                entry.get("result_issue_ref", "")
            ),
            source_artifact_refs=tuple(
                str(value)
                for value in entry.get(
                    "source_artifact_refs",
                    [],
                )
            ),
            decision_refs=tuple(
                str(value)
                for value in entry.get("decision_refs", [])
            ),
        )
        for entry in _sequence(payload.get("entries"))
    )
    return GitHubProjectV2AppendOnlyCycleHistoryResult(
        valid=bool(payload.get("valid")),
        action=str(payload.get("action", "")),
        issues=tuple(
            str(value)
            for value in _sequence(payload.get("issues"))
        ),
        history_ref=str(payload.get("history_ref", "")),
        history_digest=str(payload.get("history_digest", "")),
        appended_entry_ref=str(
            payload.get("appended_entry_ref", "")
        ),
        root_issue_ref=str(payload.get("root_issue_ref", "")),
        entries=entries,
        boundaries=tuple(
            sorted(
                (str(key), bool(value))
                for key, value in _mapping(
                    payload.get("boundaries")
                ).items()
            )
        ),
    )


def _load_issue_snapshots(
    path: Path,
) -> tuple[GitHubProjectV2IssueSnapshot, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_issues = (
        payload.get("issues", [])
        if isinstance(payload, Mapping)
        else payload
    )
    return tuple(
        GitHubProjectV2IssueSnapshot(
            issue_ref=str(issue["issue_ref"]),
            issue_number=int(issue["issue_number"]),
            title=str(issue["title"]),
            body=str(issue.get("body", "")),
            parent_issue_ref=str(
                issue.get("parent_issue_ref", "")
            ),
            sub_issue_refs=tuple(
                str(value)
                for value in issue.get("sub_issue_refs", [])
            ),
            state=str(issue.get("state", "OPEN")),
            html_url=str(issue.get("html_url", "")),
        )
        for issue in _sequence(raw_issues)
    )


def _load_theme_command(
    path: Path,
) -> GitHubProjectV2ThemeGroupingDeploymentCommand:
    payload = _read_object(path)
    return GitHubProjectV2ThemeGroupingDeploymentCommand(
        owner_kind=str(payload["owner_kind"]),
        owner_login=str(payload["owner_login"]),
        project_number=int(payload["project_number"]),
        project_id=str(payload["project_id"]),
        field_name=str(payload["field_name"]),
        desired_options=tuple(
            GitHubProjectV2ThemeOptionSpec(
                name=str(option["name"]),
                color=str(option.get("color", "GRAY")),
                description=str(
                    option.get("description", "")
                ),
            )
            for option in _sequence(
                payload.get("desired_options")
            )
        ),
        existing_fields=tuple(
            GitHubProjectV2ThemeFieldSnapshot(
                field_id=str(field["field_id"]),
                name=str(field["name"]),
                data_type=str(field["data_type"]),
                options=tuple(
                    GitHubProjectV2ThemeOptionSnapshot(
                        option_id=str(option["option_id"]),
                        name=str(option["name"]),
                        color=str(option["color"]),
                        description=str(
                            option.get("description", "")
                        ),
                    )
                    for option in _sequence(
                        field.get("options")
                    )
                ),
            )
            for field in _sequence(
                payload.get("existing_fields")
            )
        ),
        assignments=tuple(
            GitHubProjectV2ThemeAssignmentSpec(
                project_item_ref=str(
                    assignment["project_item_ref"]
                ),
                theme_name=str(assignment["theme_name"]),
            )
            for assignment in _sequence(
                payload.get("assignments")
            )
        ),
        views=tuple(
            GitHubProjectV2ViewGroupingSnapshot(
                view_number=int(view["view_number"]),
                view_name=str(view["view_name"]),
                grouped_field_id=str(
                    view.get("grouped_field_id", "")
                ),
            )
            for view in _sequence(payload.get("views"))
        ),
        target_view_number=int(
            payload.get("target_view_number", 0)
        ),
    )


def _write_json(path: Path, payload: Mapping[str, Any]) -> str:
    rendered = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if current == rendered:
            return "unchanged"
        action = "updated"
    else:
        action = "created"
    path.write_text(rendered, encoding="utf-8")
    return action


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise SystemExit(f"{path}: JSON must be an object")
    return dict(payload)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return value
    return ()


def _emit(report: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return
    print(f"mode: {report['mode']}")
    print(f"valid: {report['valid']}")
    print(f"action: {report['action']}")
    print(f"smoke_digest: {report['smoke_digest']}")
    print(
        "github_mutation_performed: "
        f"{report['github_mutation_performed']}"
    )
    print(f"output_dir: {report['output_dir']}")


if __name__ == "__main__":
    raise SystemExit(main())
