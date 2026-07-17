#!/usr/bin/env python3
"""Read-only local drift audit for the Autodoc Projects bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from projects_bundle_manifest_contract import (
    ProjectsBundleDriftAuditCommand,
    ProjectsBundleDriftAuditPolicy,
    ProjectsBundleManifestError,
    audit_projects_bundle_drift,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare the managed Autodoc bundle with a local "
            "newicody/projects checkout without changing either tree."
        )
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Return status 2 when the managed bundle is not exact.",
    )
    return parser


def execute(argv: tuple[str, ...]) -> int:
    namespace = build_parser().parse_args(argv)
    source = namespace.source.resolve()
    manifest = (
        namespace.manifest.resolve()
        if namespace.manifest is not None
        else source / "projects_bundle_manifest.json"
    )
    command = ProjectsBundleDriftAuditCommand(
        source_root=source,
        destination_root=namespace.destination.resolve(),
        manifest_path=manifest,
    )
    result = audit_projects_bundle_drift(
        command,
        policy=ProjectsBundleDriftAuditPolicy(),
    )
    if namespace.format == "json":
        print(
            json.dumps(
                result.to_mapping(),
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    else:
        print(result.to_summary())
    if namespace.fail_on_drift and not result.managed_exact:
        return 2
    return 0


def main() -> int:
    try:
        return execute(tuple(sys.argv[1:]))
    except ProjectsBundleManifestError as exc:
        print(f"bundle audit error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
