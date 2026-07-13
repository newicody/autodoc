#!/usr/bin/env python3
"""Standalone external-repository ticket artifact builder.

Copy this file to `scripts/build_autodoc_ticket_artifact.py` in the external
idea repository. It intentionally has no Autodoc import and no GitHub API call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-path", type=Path, required=True)
    parser.add_argument("--project-url", required=True)
    parser.add_argument("--workflow-name", default="autodoc-ticket-artifact.yml")
    parser.add_argument("--output-dir", type=Path, default=Path("out/autodoc-artifacts"))
    parser.add_argument("--column-name", default="")
    parser.add_argument("--copilot-summary", default=os.environ.get("AUTODOC_COPILOT_PRELIMINARY_SUMMARY", ""))
    parser.add_argument("--copilot-route", default=os.environ.get("AUTODOC_COPILOT_PRELIMINARY_ROUTE", "orientation_review"))
    args = parser.parse_args()
    event = json.loads(args.event_path.read_text(encoding="utf-8"))
    issue = event.get("issue") or {}
    repository = (event.get("repository") or {}).get("full_name", "")
    body = issue.get("body") or ""
    column_name = args.column_name or extract_column_name(body) or "Backlog"
    origin_frame_id = f"github-frame:{repository}/issues/{issue.get('number', 0)}"
    revision_token = os.environ.get("GITHUB_SHA") or issue.get("updated_at", "") or body
    ticket_revision_id = f"github-ticket-revision:{digest(origin_frame_id + ':' + revision_token)}"
    ticket_artifact = {
        "schema": "missipy.github_action.ticket_artifact.v1",
        "origin_frame_id": origin_frame_id,
        "ticket_revision_id": ticket_revision_id,
        "artifact_ref": f"github-action-ticket-artifact:{digest(origin_frame_id + ':' + ticket_revision_id)}",
        "producer": {"kind": "github_action", "repository": repository, "workflow_name": args.workflow_name, "run_id": os.environ.get("GITHUB_RUN_ID", ""), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""), "event_name": event.get("action", os.environ.get("GITHUB_EVENT_NAME", ""))},
        "repository": repository,
        "project": {"url": args.project_url},
        "ticket": {"kind": "issue", "number": issue.get("number", 0), "title": issue.get("title", ""), "body": body, "url": issue.get("html_url", "")},
        "workflow": {"column_name": column_name, "column_source": "ticket_artifact"},
        "context_options": extract_context_options(body),
        "safety": {"remote_mutation_requested": False, "usable_as_authority": True},
    }
    copilot = None
    if args.copilot_summary:
        copilot = {
            "schema": "missipy.github_project.copilot_preliminary_opinion.v1",
            "origin_frame_id": origin_frame_id,
            "ticket_revision_id": ticket_revision_id,
            "artifact_ref": f"github-action-copilot-opinion:{digest(ticket_artifact['artifact_ref'] + ':copilot')}",
            "producer": {"kind": "github_action_copilot", "trusted": False},
            "opinion": {"summary": args.copilot_summary, "suggested_route": args.copilot_route, "risks": ["external advisory artifact; requires local validation"], "confidence": 0.0},
            "server_use_policy": {"usable_as_hint": True, "usable_as_authority": False, "requires_local_validation": True},
        }
    bundle = {
        "schema": "missipy.github_action.ticket_artifact_bundle.v1",
        "origin_frame_id": origin_frame_id,
        "ticket_revision_id": ticket_revision_id,
        "artifacts": {"ticket": ticket_artifact, "copilot_preliminary_opinion": copilot},
        "server_use_policy": {"ticket_artifact_usable_as_authority": True, "copilot_usable_as_hint_only": True, "requires_local_validation": True},
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "ticket_artifact.json", ticket_artifact)
    write_json(args.output_dir / "artifact_bundle.json", bundle)
    if copilot is not None:
        write_json(args.output_dir / "copilot_preliminary_opinion.json", copilot)
    return 0


def extract_column_name(body: str) -> str:
    lines = [line.strip() for line in body.splitlines()]
    labels = {"column", "column name", "colonne", "colonne workflow", "workflow column"}
    for index, line in enumerate(lines):
        normalized = line.strip("#*:- ").lower()
        if normalized in labels:
            for candidate in lines[index + 1:]:
                value = candidate.strip("#*:- `")
                if value:
                    return value
        lowered = line.lower()
        for prefix in ("column:", "column_name:", "colonne:", "colonne workflow:"):
            if lowered.startswith(prefix):
                return line.split(":", 1)[1].strip()
    return ""


def extract_context_options(body: str) -> dict:
    lowered = body.lower()
    return {
        "include_total_project": contains_any(lowered, ("include_total_project", "ajouter le projet total")),
        "include_current_ticket": not contains_any(lowered, ("include_current_ticket: false", "ne pas ajouter ce ticket")),
        "include_repository_context": contains_any(lowered, ("include_repository_context", "ajouter ce repository", "ajouter le repository")),
        "include_linked_tickets": contains_any(lowered, ("include_linked_tickets", "tickets liés", "tickets lies")),
        "include_recent_artifacts": contains_any(lowered, ("include_recent_artifacts", "artefacts récents", "artefacts recents")),
        "requested_depth": extract_depth(lowered),
    }


def extract_depth(body: str) -> str:
    for value in ("light", "normal", "deep"):
        if f"requested_depth: {value}" in body or f"profondeur: {value}" in body:
            return value
    return "normal"


def contains_any(value: str, needles: tuple[str, ...]) -> bool:
    return any(needle in value for needle in needles)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
