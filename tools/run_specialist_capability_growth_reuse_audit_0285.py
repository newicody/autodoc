#!/usr/bin/env python3
"""Thin local adapter for the 0285-r1 source-only reuse audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.specialist_capability_growth_reuse_audit_0285 import (  # noqa: E402
    REQUIRED_REUSE_SURFACES,
    audit_specialist_capability_growth_reuse,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit reuse boundaries for controlled specialist capability growth."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser


def _load_sources(root: Path) -> dict[str, str]:
    sources: dict[str, str] = {}
    for surface in REQUIRED_REUSE_SURFACES:
        path = root / surface.path
        if path.is_file():
            sources[surface.path] = path.read_text(encoding="utf-8")

    context_dir = root / "src/context"
    if context_dir.is_dir():
        for path in sorted(context_dir.glob("*capability_growth*0285.py")):
            relative = path.relative_to(root).as_posix()
            sources.setdefault(relative, path.read_text(encoding="utf-8"))
    return sources


def _summary(mapping: dict[str, object]) -> str:
    return "\n".join(
        (
            f"valid: {str(mapping['valid']).lower()}",
            f"inspected_paths: {len(mapping['inspected_paths'])}",
            f"completed_patch_ids: {', '.join(mapping['completed_patch_ids']) or 'none'}",
            f"next_recommended_patch: {mapping['next_recommended_patch']}",
            f"source_digest: {mapping['source_digest']}",
            "installation_reviewed: true",
            "installation_modified: false",
        )
    )


def main(argv: tuple[str, ...] | None = None) -> int:
    options = _parser().parse_args(argv)
    result = audit_specialist_capability_growth_reuse(_load_sources(options.root))
    mapping = result.to_mapping()
    if options.format == "json":
        print(json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_summary(mapping))
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
