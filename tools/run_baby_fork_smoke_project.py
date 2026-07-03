#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from context.baby_fork_smoke_project import run_baby_fork_smoke_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the real minimal baby-fork context smoke project.")
    parser.add_argument("--output-dir", default=".var/baby_fork_smoke")
    args = parser.parse_args()
    result = run_baby_fork_smoke_project(Path(args.output_dir))
    print(json.dumps(result.to_json_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
