#!/usr/bin/env python3
"""Run the source-only specialists/laboratories reuse audit for 0284-r1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for _path in (str(SRC), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.specialists_laboratories_chain_reuse_audit_0284 import (  # noqa: E402
    REQUIRED_SURFACES,
    audit_specialists_laboratories_chain_reuse,
)


DEFAULT_OUTPUT = (
    ROOT
    / ".var/reports/"
    "specialists_laboratories_chain_reuse_audit_0284.json"
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
    )
    return parser.parse_args(argv)


def load_required_sources(root: Path) -> dict[str, str]:
    resolved = root.expanduser().resolve()
    sources: dict[str, str] = {}
    for relative in REQUIRED_SURFACES:
        path = resolved / relative
        if path.is_file():
            sources[relative] = path.read_text(encoding="utf-8")
    return sources


def run_audit(root: Path) -> Mapping[str, object]:
    result = audit_specialists_laboratories_chain_reuse(
        load_required_sources(root)
    )
    return result.to_mapping()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(
        tuple(sys.argv[1:] if argv is None else argv)
    )
    payload = run_audit(args.root)
    _write_json_atomic(args.output, payload)
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_summary(payload))
    return 0 if payload["valid"] else 2


def _summary(payload: Mapping[str, object]) -> str:
    return " ".join(
        (
            f"specialists_laboratories_audit_valid={payload['valid']}",
            f"issues={len(payload['issues'])}",
            (
                "portable_specialist_contract_needed="
                f"{payload['portable_specialist_contract_needed']}"
            ),
            (
                "new_laboratory_manager_justified="
                f"{payload['new_laboratory_manager_justified']}"
            ),
            (
                "next="
                f"{payload['next_recommended_patch']}"
            ),
        )
    )


def _write_json_atomic(
    path: Path,
    payload: Mapping[str, object],
) -> None:
    output = path.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
