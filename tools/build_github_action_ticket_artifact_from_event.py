#!/usr/bin/env python3
"""Build local GitHub Action ticket artifacts from a GitHub event payload.

This helper is designed for the external idea repository workflow template. It
uses only the event payload file and explicit arguments. It performs no GitHub
API call and no remote mutation.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))


from context.github_action_ticket_artifact import (  # noqa: E402
    GitHubActionProducer,
    build_copilot_preliminary_opinion_for_ticket_artifact,
    build_github_action_ticket_artifact,
    build_github_action_ticket_artifact_bundle,
    validate_github_action_ticket_artifact_bundle,
)
from context.github_project_push_frame import ProjectPushContextOptions  # noqa: E402


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build ticket and optional Copilot advisory artifacts from a GitHub event file."
    )
    parser.add_argument("--event-path", type=Path, default=None)
    parser.add_argument("--repository", default="")
    parser.add_argument("--project-url", required=True)
    parser.add_argument("--workflow-name", default="autodoc-ticket-artifact.yml")
    parser.add_argument("--column-name", default="")
    parser.add_argument("--output-dir", type=Path, default=Path("out/autodoc-artifacts"))
    parser.add_argument("--copilot-summary", default="")
    parser.add_argument("--copilot-route", default="orientation_review")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    event_path = args.event_path or Path(os.environ.get("GITHUB_EVENT_PATH", ""))
    if not event_path:
        raise SystemExit("event path missing: pass --event-path or set GITHUB_EVENT_PATH")

    event = json.loads(event_path.read_text(encoding="utf-8"))
    issue = event.get("issue") if isinstance(event.get("issue"), Mapping) else {}
    repository = args.repository or _repository_full_name(event)

    body = _normalize_issue_body(str(issue.get("body", "") or ""))
    column_name = args.column_name or _extract_column_name(body) or "Backlog"
    options = _extract_context_options(body)

    ticket_artifact = build_github_action_ticket_artifact(
        repository=repository,
        project_url=args.project_url,
        ticket_kind="issue",
        ticket_number=int(issue.get("number", 0)),
        ticket_title=str(issue.get("title", "")),
        ticket_body=body,
        ticket_url=str(issue.get("html_url", "")),
        column_name=column_name,
        context_options=options,
        producer=GitHubActionProducer(
            repository=repository,
            workflow_name=args.workflow_name,
            run_id=os.environ.get("GITHUB_RUN_ID", ""),
            run_attempt=os.environ.get("GITHUB_RUN_ATTEMPT", ""),
            event_name=str(event.get("action", os.environ.get("GITHUB_EVENT_NAME", ""))),
        ),
        revision_token=os.environ.get("GITHUB_SHA", "") or str(issue.get("updated_at", "")),
    )

    copilot = None
    if args.copilot_summary:
        copilot = build_copilot_preliminary_opinion_for_ticket_artifact(
            ticket_artifact,
            summary=args.copilot_summary,
            suggested_route=args.copilot_route,
            confidence=0.0,
            risks=("external advisory artifact; requires local validation",),
        )

    bundle = build_github_action_ticket_artifact_bundle(ticket_artifact, copilot)
    validation = validate_github_action_ticket_artifact_bundle(bundle)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ticket_path = args.output_dir / "ticket_artifact.json"
    bundle_path = args.output_dir / "artifact_bundle.json"
    copilot_path = args.output_dir / "copilot_preliminary_opinion.json"

    ticket_path.write_text(
        json.dumps(ticket_artifact.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    bundle_path.write_text(
        json.dumps(bundle.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if copilot is not None:
        copilot_path.write_text(
            json.dumps(copilot.to_json_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    report = {
        "schema": "missipy.github_action.ticket_artifact_build_report.v1",
        "status": "ok" if validation["allowed"] else "blocked",
        "validation": validation,
        "outputs": {
            "ticket_artifact": str(ticket_path),
            "artifact_bundle": str(bundle_path),
            "copilot_preliminary_opinion": str(copilot_path) if copilot is not None else None,
        },
        "boundary": [
            "event payload file only",
            "ticket + column name + options",
            "Copilot opinion is advisory only",
            "no GitHub API call",
            "no remote mutation",
        ],
    }

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))

    if not validation["allowed"]:
        issue_codes = ", ".join(issue["code"] for issue in validation["issues"])
        raise SystemExit(f"github action ticket artifact rejected: {issue_codes}")

    if args.format == "text":
        print(f"status: {report['status']}")
        print(f"ticket_artifact: {ticket_path}")
        print(f"artifact_bundle: {bundle_path}")
        if copilot is not None:
            print(f"copilot_preliminary_opinion: {copilot_path}")

    return 0


def _normalize_issue_body(body: str) -> str:
    return body.replace("\\r\\n", "\n").replace("\\n", "\n")


def _repository_full_name(event: Mapping[str, Any]) -> str:
    repository = event.get("repository")
    if isinstance(repository, Mapping):
        full_name = repository.get("full_name")
        if full_name:
            return str(full_name)
    return ""


def _extract_column_name(body: str) -> str:
    lines = [line.strip() for line in body.splitlines()]
    labels = {"column", "column name", "colonne", "colonne workflow", "workflow column"}

    for index, line in enumerate(lines):
        normalized = line.strip("#*:- ").lower()
        if normalized in labels:
            for candidate in lines[index + 1 :]:
                value = candidate.strip("#*:- `")
                if value:
                    return value

        lowered = line.lower()
        for prefix in ("column:", "column_name:", "colonne:", "colonne workflow:"):
            if lowered.startswith(prefix):
                return line.split(":", 1)[1].strip()

    return ""


def _extract_context_options(body: str) -> ProjectPushContextOptions:
    lowered = body.lower()
    return ProjectPushContextOptions(
        include_total_project=_contains_any(lowered, ("include_total_project", "ajouter le projet total")),
        include_current_ticket=not _contains_any(lowered, ("include_current_ticket: false", "ne pas ajouter ce ticket")),
        include_repository_context=_contains_any(
            lowered,
            ("include_repository_context", "ajouter ce repository", "ajouter le repository"),
        ),
        include_linked_tickets=_contains_any(lowered, ("include_linked_tickets", "tickets liés", "tickets lies")),
        include_recent_artifacts=_contains_any(lowered, ("include_recent_artifacts", "artefacts récents", "artefacts recents")),
        requested_depth=_extract_depth(lowered),
    )


def _extract_depth(body: str) -> str:
    for value in ("light", "normal", "deep"):
        if f"requested_depth: {value}" in body or f"profondeur: {value}" in body:
            return value
    return "normal"


def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
    return any(needle in value for needle in needles)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
