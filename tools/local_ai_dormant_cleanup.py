#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


GENERATED_ARTIFACTS = (
    Path("doc/maintenance/roadmap_b_aider_prompt.md"),
    Path("doc/maintenance/roadmap_b_aider_orchestrator_run_report.json"),
)

LOCAL_ONLY_PATHS = (
    Path(".var"),
    Path(".env.aider312"),
)

PATCH_PREFIXES = (
    "0039-part8_roadmap_b_part8_1_local_data_contract",
)

GITIGNORE_BLOCK = """\
# Local AI / Aider generated operator artifacts
doc/maintenance/roadmap_b_aider_prompt.md
doc/maintenance/roadmap_b_aider_orchestrator_run_report.json
.var/
.env.aider312
.aider*
"""


@dataclass(frozen=True)
class CleanupPlan:
    files_to_remove: tuple[Path, ...]
    directories_to_remove: tuple[Path, ...]
    gitignore_needs_update: bool

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": "missipy.local_ai_dormant_cleanup.v1",
            "files_to_remove": [str(path) for path in self.files_to_remove],
            "directories_to_remove": [str(path) for path in self.directories_to_remove],
            "gitignore_needs_update": self.gitignore_needs_update,
        }


def build_cleanup_plan(root: Path, *, update_gitignore: bool = False) -> CleanupPlan:
    files = tuple(path for path in GENERATED_ARTIFACTS if (root / path).is_file())

    dirs: list[Path] = []
    for local_path in LOCAL_ONLY_PATHS:
        candidate = root / local_path
        if candidate.is_dir():
            dirs.append(local_path)

    patch_root = root / "patch"
    if patch_root.is_dir():
        for child in sorted(patch_root.iterdir()):
            if child.is_dir() and any(child.name.startswith(prefix) for prefix in PATCH_PREFIXES):
                dirs.append(Path("patch") / child.name)

    gitignore_needs_update = False
    if update_gitignore:
        gitignore = root / ".gitignore"
        current = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        gitignore_needs_update = "roadmap_b_aider_prompt.md" not in current

    return CleanupPlan(
        files_to_remove=files,
        directories_to_remove=tuple(dirs),
        gitignore_needs_update=gitignore_needs_update,
    )


def apply_cleanup_plan(root: Path, plan: CleanupPlan, *, update_gitignore: bool = False) -> None:
    for relative_path in plan.files_to_remove:
        target = root / relative_path
        if target.exists():
            target.unlink()

    for relative_path in plan.directories_to_remove:
        target = root / relative_path
        if target.is_dir():
            for child in sorted(target.rglob("*"), reverse=True):
                if child.is_file() or child.is_symlink():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            target.rmdir()
        elif target.exists():
            target.unlink()

    if update_gitignore and plan.gitignore_needs_update:
        gitignore = root / ".gitignore"
        current = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        separator = "\n" if current and not current.endswith("\n") else ""
        gitignore.write_text(current + separator + "\n" + GITIGNORE_BLOCK, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean local AI/Aider generated artifacts and put Aider in dormant mode.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--update-gitignore", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    plan = build_cleanup_plan(root, update_gitignore=args.update_gitignore)

    print(plan.to_json_dict())

    if args.apply:
        apply_cleanup_plan(root, plan, update_gitignore=args.update_gitignore)
        print("cleanup_applied: true")
    else:
        print("cleanup_applied: false")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
