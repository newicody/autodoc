#!/usr/bin/env python3
"""Build readable Actions artifact names and expose them through GITHUB_OUTPUT."""

from __future__ import annotations

from pathlib import Path
import json
import os
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.human_readable_artifact_identity_0287 import (  # noqa: E402
    build_human_readable_artifact_identity_bundle,
)


def _load(path: Path, name: str) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{name} must be a JSON object")
    return payload


def _write_output(path: Path, key: str, value: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{key}={value}\n")


def main() -> int:
    issue_path = Path(os.environ.get("AUTODOC_ISSUE_JSON", "out/issue.json"))
    request_path = Path(
        os.environ.get("AUTODOC_REQUEST", "out/authoritative_request.json")
    )
    advisory_path = Path(
        os.environ.get("AUTODOC_ADVISORY", "out/copilot_advisory.json")
    )
    manifest_path = Path(
        os.environ.get("AUTODOC_MANIFEST", "out/dual_artifact_manifest.json")
    )
    output_path = Path(
        os.environ.get("AUTODOC_ARTIFACT_IDENTITY", "out/artifact_identity.json")
    )
    bundle = build_human_readable_artifact_identity_bundle(
        repository=os.environ["GITHUB_REPOSITORY"],
        workflow_run_id=os.environ.get("GITHUB_RUN_ID", "local-preview"),
        issue=_load(issue_path, "Issue"),
        request=_load(request_path, "authoritative request"),
        advisory=(
            _load(advisory_path, "Copilot advisory")
            if advisory_path.is_file()
            else None
        ),
        manifest=_load(manifest_path, "dual-artifact manifest"),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(bundle.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    github_output = os.environ.get("GITHUB_OUTPUT", "").strip()
    if github_output:
        output = Path(github_output)
        _write_output(
            output,
            "request_name",
            bundle.identity("authoritative_request").actions_name,
        )
        advisory = tuple(
            item for item in bundle.identities if item.artifact_kind == "copilot_advisory"
        )
        if advisory:
            _write_output(output, "advisory_name", advisory[0].actions_name)
        _write_output(
            output,
            "manifest_name",
            bundle.identity("run_manifest").actions_name,
        )
        _write_output(output, "bundle_digest", bundle.bundle_digest)
    print(json.dumps(bundle.to_mapping(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
