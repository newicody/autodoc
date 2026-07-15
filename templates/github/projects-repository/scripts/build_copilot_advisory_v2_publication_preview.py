#!/usr/bin/env python3
"""Build a v2 publication preview from correlated GitHub Actions artifacts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys
from typing import Any

_ADVISORY_SCHEMA = "missipy.github.copilot_advisory.v2"
_REQUEST_SCHEMA = "missipy.github.authoritative_request.v1"
_MANIFEST_SCHEMA = "missipy.github.dual_artifact_manifest.v1"
_PREVIEW_SCHEMA = "missipy.github.copilot_advisory_publication_preview.v2"


def build_copilot_advisory_v2_publication_preview(
    *,
    advisory_path: Path,
    request_path: Path,
    manifest_path: Path,
    run_id: str,
    repository: str,
    issue_number: int,
) -> dict[str, Any]:
    if not run_id.strip():
        raise ValueError("run_id must be non-empty")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must use owner/name")
    if issue_number <= 0:
        raise ValueError("issue_number must be positive")

    advisory = _load_mapping(advisory_path, _ADVISORY_SCHEMA, "Copilot advisory")
    request = _load_mapping(request_path, _REQUEST_SCHEMA, "authoritative request")
    manifest = _load_mapping(manifest_path, _MANIFEST_SCHEMA, "dual artifact manifest")
    _validate_correlation(advisory, request, manifest, advisory_path, request_path)

    if request.get("repository") != repository:
        raise ValueError("authoritative request repository mismatch")
    if int(request.get("issue_number") or 0) != issue_number:
        raise ValueError("authoritative request Issue mismatch")
    if request.get("authoritative") is not True:
        raise ValueError("authoritative request flag must remain true")

    forbidden = (
        "summary",
        "suggested_route",
        "assumptions",
        "questions",
        "risks",
        "confidence",
    )
    present_forbidden = [name for name in forbidden if name in advisory]
    if present_forbidden:
        raise ValueError(
            "Copilot advisory v2 contains v1 analytical fields: "
            + ", ".join(present_forbidden)
        )
    _sha256_text("prompt_digest", advisory.get("prompt_digest"))
    _sha256_text("response_digest", advisory.get("response_digest"))
    criteria = _string_list("success_criteria", advisory.get("success_criteria"))
    if not criteria:
        raise ValueError("success_criteria must not be empty")
    return {
        "schema": _PREVIEW_SCHEMA,
        "source_candidate_ref": _required_text(
            "request artifact ref",
            request.get("artifact_ref"),
        ),
        "advisory_artifact_ref": _required_text(
            "advisory artifact ref",
            advisory.get("artifact_ref"),
        ),
        "concrete_objective": _required_text(
            "concrete_objective",
            advisory.get("concrete_objective"),
        ),
        "expected_result": _required_text(
            "expected_result",
            advisory.get("expected_result"),
        ),
        "provided_constraints": _string_list(
            "provided_constraints",
            advisory.get("provided_constraints"),
        ),
        "success_criteria": criteria,
        "origin_frame_id": _required_text(
            "origin_frame_id",
            advisory.get("origin_frame_id"),
        ),
        "ticket_revision_id": _required_text(
            "ticket_revision_id",
            advisory.get("ticket_revision_id"),
        ),
        "prompt_digest": _sha256_text(
            "prompt_digest",
            advisory.get("prompt_digest"),
        ),
        "response_digest": _sha256_text(
            "response_digest",
            advisory.get("response_digest"),
        ),
        "workflow_run_ref": f"github-actions-run:{run_id.strip()}",
        "repository": repository,
        "issue_number": issue_number,
        "advisory_schema": _ADVISORY_SCHEMA,
        "advisory_is_authority": False,
        "request_authoritative": True,
        "operator_decision_required": True,
        "publication_gate_required": True,
        "github_mutation_performed": False,
        "remote_mutation_allowed": False,
    }


def render_projectv2_v2_summary(preview: Mapping[str, Any], limit: int = 1024) -> str:
    constraints = _string_list("provided_constraints", preview.get("provided_constraints"))
    criteria = _string_list("success_criteria", preview.get("success_criteria"))
    parts = [
        f"Objectif: {_required_text('concrete_objective', preview.get('concrete_objective'))}",
        f"Résultat attendu: {_required_text('expected_result', preview.get('expected_result'))}",
        "Contraintes: " + ("; ".join(constraints) if constraints else "aucune explicite"),
        "Critères: " + "; ".join(criteria),
    ]
    value = " | ".join(parts)
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 1)].rstrip() + "…"


def _validate_correlation(
    advisory: Mapping[str, Any],
    request: Mapping[str, Any],
    manifest: Mapping[str, Any],
    advisory_path: Path,
    request_path: Path,
) -> None:
    expected = {
        "origin_frame_id": request.get("origin_frame_id"),
        "ticket_revision_id": request.get("ticket_revision_id"),
        "request_artifact_ref": request.get("artifact_ref"),
    }
    for key, value in expected.items():
        if advisory.get(key) != value:
            raise ValueError(f"request/advisory correlation mismatch: {key}")
        if manifest.get(key) != value:
            raise ValueError(f"request/manifest correlation mismatch: {key}")
    if manifest.get("advisory_artifact_ref") != advisory.get("artifact_ref"):
        raise ValueError("manifest advisory_artifact_ref mismatch")
    if manifest.get("request_is_authority") is not True:
        raise ValueError("request_is_authority must remain true")
    if manifest.get("advisory_is_authority") is not False:
        raise ValueError("manifest advisory_is_authority must remain false")
    if advisory.get("usable_as_authority") is not False:
        raise ValueError("advisory usable_as_authority must remain false")
    if advisory.get("usable_as_hint") is not True:
        raise ValueError("advisory usable_as_hint must remain true")
    if advisory.get("trusted") is not False:
        raise ValueError("Copilot advisory must remain untrusted")
    if manifest.get("request_sha256") != _sha256(request_path):
        raise ValueError("authoritative request digest mismatch")
    if manifest.get("advisory_sha256") != _sha256(advisory_path):
        raise ValueError("Copilot advisory digest mismatch")


def _load_mapping(path: Path, schema: str, name: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    if payload.get("schema") != schema:
        raise ValueError(f"unexpected {name} schema")
    return dict(payload)


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value.strip()


def _sha256_text(name: str, value: object) -> str:
    text = _required_text(name, value)
    if not re.fullmatch(r"[0-9a-f]{64}", text):
        raise ValueError(f"{name} must be a lowercase sha256")
    return text


def _string_list(name: str, value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{name} must be a JSON string array")
    return [item.strip() for item in value if item.strip()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--advisory", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(tuple(sys.argv[1:] if argv is None else argv))
    preview = build_copilot_advisory_v2_publication_preview(
        advisory_path=args.advisory,
        request_path=args.request,
        manifest_path=args.manifest,
        run_id=args.run_id,
        repository=args.repository,
        issue_number=args.issue_number,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
