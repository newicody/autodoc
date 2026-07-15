#!/usr/bin/env python3
"""Build a coherent local-only artifact set for the 0286-r7 verifier.

The generated files validate serialization, digest verification and query-only
readback correlation. They are fixtures, not evidence of a real GitHub
publication, and must never be passed to the r6 CLI with ``--execute``.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (_REPO_ROOT, _SRC_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from context.specialist_capability_growth_projects_operator_authorized_adapter_0286 import (  # noqa: E402
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_SCHEMA,
    SpecialistCapabilityGrowthProjectsOperatorExecutionResult,
)
from context.specialist_capability_growth_projects_publication_plan_0286 import (  # noqa: E402
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA,
    SpecialistCapabilityGrowthProjectV2FieldMutation,
    SpecialistCapabilityGrowthProjectsPublicationPlan,
)
from tools.apply_specialist_capability_growth_projects_projection_0286 import (  # noqa: E402
    ADAPTER_SCHEMA,
    recompute_plan_digest,
)

FIXTURE_SCHEMA = (
    "missipy.specialist.capability_growth.projects_readback_fixture.v1"
)

_FIELD_VALUES = (
    ("Spécialiste", "specialist:fixture"),
    ("Révision spécialiste", "revision:fixture:2"),
    ("Capacité proposée", "technical_review"),
    ("Action capacité", "add"),
    ("Décision capacité", "approve"),
    ("Statut révision", "approved_selected_observed"),
    ("Référence SQL", "sql:fixture:revision:2"),
    ("Digest décision", "d" * 64),
    ("Laboratoire", "laboratory:fixture-local"),
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Write a local-only r5/r6/readback fixture set. "
            "No GitHub call or mutation is performed."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".var/reports/0286-readback-fixture"),
    )
    parser.add_argument(
        "--repository",
        default="newicody/projects",
    )
    parser.add_argument("--issue-number", type=int, default=1)
    parser.add_argument("--project-id", default="PVT_fixture")
    parser.add_argument("--project-item-id", default="PVTI_fixture")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    marker = (
        "autodoc:specialist-capability-growth:"
        "fixture-local-readback-only"
    )
    comment_body = (
        f"<!-- {marker} -->\n"
        "## Autodoc fixture — specialist capability growth\n\n"
        "Local-only replay fixture. This is not real publication evidence.\n"
    )
    comment_digest = sha256(comment_body.encode("utf-8")).hexdigest()
    mutations = tuple(
        SpecialistCapabilityGrowthProjectV2FieldMutation(
            field_name=name,
            desired_value=value,
            current_value=value,
            action="replay",
        )
        for name, value in _FIELD_VALUES
    )

    provisional = SpecialistCapabilityGrowthProjectsPublicationPlan(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA,
        valid=True,
        action="replay",
        issues=(),
        repository=args.repository,
        issue_number=args.issue_number,
        project_id=args.project_id,
        project_item_id=args.project_item_id,
        policy_decision_id="policy:0286:r7:fixture",
        review_ref="projects-review:fixture",
        revision_ref="revision:fixture:2",
        sql_ref="sql:fixture:revision:2",
        decision_ref="decision:fixture:2",
        projection_digest_sha256="a" * 64,
        marker=marker,
        comment_action="replay",
        comment_body=comment_body,
        comment_body_sha256=comment_digest,
        existing_comment_id=999_999,
        existing_comment_url=(
            "https://example.invalid/autodoc-fixture-comment"
        ),
        projectv2_action="replay",
        projectv2_field_mutations=mutations,
        plan_digest="0" * 64,
    )
    plan = SpecialistCapabilityGrowthProjectsPublicationPlan(
        schema=provisional.schema,
        valid=provisional.valid,
        action=provisional.action,
        issues=provisional.issues,
        repository=provisional.repository,
        issue_number=provisional.issue_number,
        project_id=provisional.project_id,
        project_item_id=provisional.project_item_id,
        policy_decision_id=provisional.policy_decision_id,
        review_ref=provisional.review_ref,
        revision_ref=provisional.revision_ref,
        sql_ref=provisional.sql_ref,
        decision_ref=provisional.decision_ref,
        projection_digest_sha256=provisional.projection_digest_sha256,
        marker=provisional.marker,
        comment_action=provisional.comment_action,
        comment_body=provisional.comment_body,
        comment_body_sha256=provisional.comment_body_sha256,
        existing_comment_id=provisional.existing_comment_id,
        existing_comment_url=provisional.existing_comment_url,
        projectv2_action=provisional.projectv2_action,
        projectv2_field_mutations=provisional.projectv2_field_mutations,
        plan_digest=recompute_plan_digest(provisional),
    )

    execution = SpecialistCapabilityGrowthProjectsOperatorExecutionResult(
        schema=(
            SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_SCHEMA
        ),
        valid=True,
        mode="execute",
        action="replayed",
        issues=(),
        plan_digest=plan.plan_digest,
        repository=plan.repository,
        issue_number=plan.issue_number,
        project_id=plan.project_id,
        project_item_id=plan.project_item_id,
        comment_action="replayed",
        comment_id=plan.existing_comment_id,
        comment_url=plan.existing_comment_url,
        projectv2_action="replayed",
        changed_fields=(),
        operator_decision="approve",
        confirmed_plan_digest=plan.plan_digest,
        remote_mutation_allowed=True,
        github_mutation_performed=False,
        issue_comment_published=False,
        projectv2_mutation_performed=False,
    )

    paths = {
        "plan": args.output_dir / "capability-growth-plan.json",
        "execution": (
            args.output_dir / "capability-growth-execution.json"
        ),
        "comments": args.output_dir / "issue-comments.json",
        "fields": args.output_dir / "projectv2-fields.json",
        "manifest": args.output_dir / "fixture-manifest.json",
    }
    _write_json(
        paths["plan"],
        {
            **plan.to_mapping(),
            "fixture_only": True,
            "remote_execution_allowed": False,
        },
    )
    _write_json(
        paths["execution"],
        {
            "schema": ADAPTER_SCHEMA,
            "result": execution.to_mapping(),
            "performed_operations": [],
            "partial_execution": False,
            "fixture_only": True,
            "boundaries": {
                "real_github_publication_proven": False,
                "remote_execution_allowed": False,
            },
        },
    )
    _write_json(
        paths["comments"],
        {
            "fixture_only": True,
            "comments": [
                {
                    "id": plan.existing_comment_id,
                    "body": plan.comment_body,
                    "html_url": plan.existing_comment_url,
                }
            ],
        },
    )
    _write_json(
        paths["fields"],
        {
            "fixture_only": True,
            "field_values": dict(_FIELD_VALUES),
        },
    )
    _write_json(
        paths["manifest"],
        {
            "schema": FIXTURE_SCHEMA,
            "fixture_only": True,
            "real_github_publication_proven": False,
            "warning": (
                "Never pass these artifacts to the r6 CLI with --execute."
            ),
            "plan_digest": plan.plan_digest,
            "files": {
                key: str(path)
                for key, path in paths.items()
                if key != "manifest"
            },
        },
    )

    print(f"fixture_only: true")
    print(f"plan_digest: {plan.plan_digest}")
    for key, path in paths.items():
        print(f"{key}: {path}")
    return 0


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
