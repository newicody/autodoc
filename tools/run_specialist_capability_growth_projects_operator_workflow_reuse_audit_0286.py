#!/usr/bin/env python3
"""Run the source-only 0286-r1 Projects operator workflow reuse audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from context.specialist_capability_growth_projects_operator_workflow_reuse_audit_0286 import (
    audit_specialist_capability_growth_projects_operator_workflow_reuse,
    load_audit_sources,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = audit_specialist_capability_growth_projects_operator_workflow_reuse(
        load_audit_sources(args.root)
    )
    mapping = result.to_mapping()
    if args.format == "json":
        print(json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"valid={str(result.valid).lower()}")
        print(f"next_recommended_patch={result.next_recommended_patch}")
        print(f"completed_phases={len(result.completed_phases)}")
        print(f"dedicated_growth_issue_form_present={str(result.dedicated_growth_issue_form_present).lower()}")
        print(f"specialist_revision_fields_present={str(result.specialist_revision_fields_present).lower()}")
        print(f"operator_decision_view_present={str(result.operator_decision_view_present).lower()}")
        print(f"workflow_is_read_only_for_issues={str(result.workflow_is_read_only_for_issues).lower()}")
        print(f"installation_reviewed={str(result.installation_reviewed).lower()}")
        print(f"source_digest={result.source_digest}")
        for path in result.missing_reuse_surfaces:
            print(f"missing={path}")
        for path in result.incomplete_reuse_surfaces:
            print(f"incomplete={path}")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
