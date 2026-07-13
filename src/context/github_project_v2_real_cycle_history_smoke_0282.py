"""Real ProjectV2 cycle-history smoke composition for phase 0282-r8.

The pure composition combines:

* the valid append-only history from 0282-r4;
* the parent/sub-ticket mutation plan from 0282-r5;
* the theme-grouping deployment plan from 0282-r6.

It does not execute the operator-authorized adapter from 0282-r7. The CLI layer
performs that optional handoff only after an exact smoke-digest confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from context.github_project_v2_append_only_cycle_history_0282 import (
    GitHubProjectV2AppendOnlyCycleHistoryResult,
)
from context.github_project_v2_parent_sub_ticket_mutation_plan_0282 import (
    GitHubProjectV2IssueSnapshot,
    GitHubProjectV2ParentSubTicketMutationCommand,
    GitHubProjectV2ParentSubTicketMutationPlan,
    plan_github_project_v2_parent_sub_ticket_mutation,
)
from context.github_project_v2_theme_grouping_deployment_plan_0282 import (
    GitHubProjectV2ThemeGroupingDeploymentCommand,
    GitHubProjectV2ThemeGroupingDeploymentResult,
    plan_github_project_v2_theme_grouping_deployment,
)


REAL_CYCLE_HISTORY_SMOKE_SCHEMA = (
    "missipy.github.project_v2_real_cycle_history_smoke.v1"
)


@dataclass(frozen=True, slots=True)
class GitHubProjectV2RealCycleHistorySmokeCommand:
    history: GitHubProjectV2AppendOnlyCycleHistoryResult
    existing_issues: tuple[GitHubProjectV2IssueSnapshot, ...]
    next_cycle_title: str
    next_cycle_summary: str
    policy_decision_id: str
    operator_decision: str
    theme_command: (
        GitHubProjectV2ThemeGroupingDeploymentCommand | None
    ) = None
    source_artifact_refs: tuple[str, ...] = ()
    decision_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GitHubProjectV2RealCycleHistorySmokeResult:
    valid: bool
    issues: tuple[str, ...]
    action: str
    smoke_ref: str
    smoke_digest: str
    history_ref: str
    parent_plan: GitHubProjectV2ParentSubTicketMutationPlan
    theme_plan: (
        GitHubProjectV2ThemeGroupingDeploymentResult | None
    )
    boundaries: tuple[tuple[str, bool], ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": REAL_CYCLE_HISTORY_SMOKE_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "action": self.action,
            "smoke_ref": self.smoke_ref,
            "smoke_digest": self.smoke_digest,
            "history_ref": self.history_ref,
            "parent_plan": self.parent_plan.to_json_dict(),
            "theme_plan": (
                self.theme_plan.to_json_dict()
                if self.theme_plan is not None
                else {}
            ),
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"project_v2_real_cycle_smoke_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"action={self.action}",
                f"smoke_ref={self.smoke_ref or '-'}",
                f"parent_action={self.parent_plan.action}",
                "theme_action="
                + (
                    self.theme_plan.action
                    if self.theme_plan is not None
                    else "not_requested"
                ),
                "github_mutation_performed=False",
            )
        )


def build_github_project_v2_real_cycle_history_smoke(
    command: GitHubProjectV2RealCycleHistorySmokeCommand,
) -> GitHubProjectV2RealCycleHistorySmokeResult:
    parent_plan = plan_github_project_v2_parent_sub_ticket_mutation(
        GitHubProjectV2ParentSubTicketMutationCommand(
            history=command.history,
            policy_decision_id=command.policy_decision_id,
            operator_decision=command.operator_decision,
            next_cycle_title=command.next_cycle_title,
            next_cycle_summary=command.next_cycle_summary,
            existing_issues=command.existing_issues,
            source_artifact_refs=tuple(
                sorted(command.source_artifact_refs)
            ),
            decision_refs=tuple(sorted(command.decision_refs)),
        )
    )
    theme_plan = (
        plan_github_project_v2_theme_grouping_deployment(
            command.theme_command
        )
        if command.theme_command is not None
        else None
    )

    issues = list(parent_plan.issues)
    if not parent_plan.valid:
        issues.append("parent/sub-ticket plan is not executable")
    if theme_plan is not None:
        issues.extend(theme_plan.issues)
        if not theme_plan.valid:
            issues.append("theme grouping plan is not executable")

    canonical = {
        "history_ref": command.history.history_ref,
        "history_digest": command.history.history_digest,
        "parent_plan_digest": parent_plan.plan_digest,
        "theme_plan_digest": (
            theme_plan.plan_digest
            if theme_plan is not None
            else ""
        ),
        "policy_decision_id": command.policy_decision_id,
        "operator_decision": command.operator_decision,
        "source_artifact_refs": sorted(
            command.source_artifact_refs
        ),
        "decision_refs": sorted(command.decision_refs),
    }
    digest = hashlib.sha256(
        json.dumps(
            canonical,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    valid = not issues
    action = _smoke_action(parent_plan, theme_plan) if valid else "blocked"
    return GitHubProjectV2RealCycleHistorySmokeResult(
        valid=valid,
        issues=tuple(dict.fromkeys(issues)),
        action=action,
        smoke_ref=(
            f"github-project-v2-real-cycle-smoke:{digest[:16]}"
            if valid
            else ""
        ),
        smoke_digest=digest,
        history_ref=command.history.history_ref,
        parent_plan=parent_plan,
        theme_plan=theme_plan,
        boundaries=_boundaries(),
    )


def _smoke_action(
    parent_plan: GitHubProjectV2ParentSubTicketMutationPlan,
    theme_plan: (
        GitHubProjectV2ThemeGroupingDeploymentResult | None
    ),
) -> str:
    remote_operations = len(parent_plan.operations)
    if theme_plan is not None:
        remote_operations += len(theme_plan.operations)

    manual_steps = bool(
        theme_plan is not None
        and theme_plan.operator_steps
    )
    if remote_operations:
        return "ready_for_operator_authorized_execution"
    if manual_steps:
        return "manual_operator_step_required"
    return "replay"


def _boundaries() -> tuple[tuple[str, bool], ...]:
    return (
        ("composition_only", True),
        ("adapter_reused", True),
        ("preview_is_default", True),
        ("exact_smoke_digest_required_for_execution", True),
        ("external_call_performed", False),
        ("github_mutation_allowed", False),
        ("github_mutation_performed", False),
        ("sql_write_allowed", False),
        ("qdrant_write_allowed", False),
        ("scheduler_modified", False),
        ("projects_repository_change_required", False),
    )
