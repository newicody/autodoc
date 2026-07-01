#!/usr/bin/env python3
"""Apply one or more versioned Git patch directories, clean artifacts, and run tests.

Patch layout is intentionally directory-based:

    patch/
      0001-phase6_3_patch_queue_workflow/
        patch.diff
        README.md
        metadata.json

The script is stdlib-only. It does not require ssh-agent. For network Git
operations such as fetch/push, it can build a temporary GIT_SSH_COMMAND from a
private key and optional OpenSSH user certificate supplied outside the repo.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


PATCH_SUFFIXES = (".patch", ".diff")
DEFAULT_PATCH_FILENAMES = ("patch.diff", "patch.patch", "changes.diff", "changes.patch")
IGNORED_PATCH_DIRS = {"_applied", "_rejected", "_scratch", "__pycache__"}
GENERATED_FILE_SUFFIXES = (".svg", ".pyo")
GENERATED_DIR_NAMES = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")
LOCAL_CONFIG = ".patchqueue.local.json"

DEFAULT_TEST_COMMANDS: tuple[tuple[str, ...], ...] = (
    (sys.executable, "-m", "compileall", "-q", "src", "tests"),
    (sys.executable, "-m", "pytest", "-q", "tests/rules"),
    (sys.executable, "-m", "pytest", "-q"),
)


@dataclass(frozen=True, slots=True)
class PatchQueueItem:
    name: str
    root: Path
    patch_file: Path
    metadata: Mapping[str, object]

    @property
    def commit_subject(self) -> str:
        raw = self.metadata.get("commit_subject")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        return commit_subject_from_name(self.name)


@dataclass(frozen=True, slots=True)
class SshOptions:
    key_file: Path | None = None
    cert_file: Path | None = None
    known_hosts_file: Path | None = None
    strict_host_key_checking: str | None = None
    disable_agent: bool = True
    batch_mode: bool = True


@dataclass(frozen=True, slots=True)
class PatchQueueOptions:
    root: Path
    patch_root: Path
    patch_name: str | None = None
    all_patches: bool = False
    dry_run: bool = False
    skip_tests: bool = False
    skip_clean: bool = False
    allow_dirty: bool = False
    commit: bool = False
    include_patch_artifact: bool = False
    archive_applied: bool = False
    fetch_before: bool = False
    push: bool = False
    remote: str = "origin"
    branch: str | None = None
    ssh: SshOptions = SshOptions()


def repo_root(start: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return Path(result.stdout.strip()).resolve()


def relative_to_root(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def load_json_file(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return payload


def local_config(root: Path) -> dict[str, object]:
    return load_json_file(root / LOCAL_CONFIG)


def patch_metadata(patch_dir: Path) -> dict[str, object]:
    return load_json_file(patch_dir / "metadata.json")


def discover_patch_file(patch_dir: Path, metadata: Mapping[str, object]) -> Path:
    configured = metadata.get("patch_file")
    if isinstance(configured, str) and configured.strip():
        candidate = patch_dir / configured.strip()
        if not candidate.is_file():
            raise SystemExit(f"configured patch file does not exist: {candidate}")
        return candidate

    for filename in DEFAULT_PATCH_FILENAMES:
        candidate = patch_dir / filename
        if candidate.is_file():
            return candidate

    candidates = sorted(
        path
        for path in patch_dir.iterdir()
        if path.is_file() and path.suffix in PATCH_SUFFIXES
    )
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise SystemExit(f"no patch file found in {patch_dir}; expected patch.diff or metadata.json")
    names = ", ".join(path.name for path in candidates)
    raise SystemExit(f"multiple patch files in {patch_dir}; set metadata.json patch_file: {names}")


def discover_patch_items(patch_root: Path) -> tuple[PatchQueueItem, ...]:
    if not patch_root.exists():
        return ()

    flat = sorted(
        path
        for path in patch_root.iterdir()
        if path.is_file() and path.suffix in PATCH_SUFFIXES
    )
    if flat:
        names = ", ".join(path.name for path in flat)
        raise SystemExit(
            "flat patch files are no longer accepted; use patch/<patch-id>/patch.diff: " + names
        )

    items: list[PatchQueueItem] = []
    for patch_dir in sorted(path for path in patch_root.iterdir() if path.is_dir()):
        if patch_dir.name in IGNORED_PATCH_DIRS or patch_dir.name.startswith("_"):
            continue
        metadata = patch_metadata(patch_dir)
        items.append(
            PatchQueueItem(
                name=patch_dir.name,
                root=patch_dir,
                patch_file=discover_patch_file(patch_dir, metadata),
                metadata=metadata,
            )
        )
    return tuple(items)


def select_patch_items(items: Sequence[PatchQueueItem], *, patch_name: str | None, all_patches: bool) -> tuple[PatchQueueItem, ...]:
    if patch_name:
        selected = tuple(item for item in items if item.name == patch_name)
        if not selected:
            known = ", ".join(item.name for item in items) or "<none>"
            raise SystemExit(f"unknown patch {patch_name}; available: {known}")
        return selected
    if all_patches:
        return tuple(items)
    if len(items) == 1:
        return (items[0],)
    if not items:
        return ()
    known = ", ".join(item.name for item in items)
    raise SystemExit(f"multiple patches found; use --patch NAME or --all: {known}")


def commit_subject_from_name(name: str) -> str:
    stem = name
    if len(stem) > 5 and stem[:4].isdigit() and stem[4] in {"-", "_"}:
        stem = stem[5:]
    return stem.replace("_", "-")


def run(command: Sequence[str], *, root: Path, env: Mapping[str, str] | None = None) -> None:
    print("+ " + " ".join(shlex.quote(part) for part in command))
    subprocess.run(command, cwd=root, env=dict(env) if env is not None else None, check=True)


def run_capture(command: Sequence[str], *, root: Path, env: Mapping[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=root,
        env=dict(env) if env is not None else None,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def git_env(root: Path, ssh: SshOptions) -> dict[str, str]:
    env = dict(os.environ)
    command = build_git_ssh_command(ssh)
    if command:
        env["GIT_SSH_COMMAND"] = command
    return env


def run_git(args: Sequence[str], *, root: Path, ssh: SshOptions | None = None) -> None:
    run(("git", *args), root=root, env=git_env(root, ssh or SshOptions()))


def git_capture(args: Sequence[str], *, root: Path, ssh: SshOptions | None = None) -> str:
    return run_capture(("git", *args), root=root, env=git_env(root, ssh or SshOptions()))


def git_status(root: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        text=True,
        check=True,
        stdout=subprocess.PIPE,
    )
    return tuple(line for line in result.stdout.splitlines() if line.strip())


def is_allowed_preapply_status_line(line: str) -> bool:
    path = line[3:] if len(line) > 3 else ""
    return line.startswith("?? patch/") or path == LOCAL_CONFIG


def assert_clean_worktree(root: Path, *, allow_dirty: bool) -> None:
    if allow_dirty:
        return
    dirty = tuple(line for line in git_status(root) if not is_allowed_preapply_status_line(line))
    if dirty:
        details = "\n".join(dirty)
        raise SystemExit(
            "working tree is not clean outside patch queue/local config; commit/stash first or use --allow-dirty\n"
            + details
        )


def is_tracked(root: Path, path: Path) -> bool:
    rel = relative_to_root(root, path)
    return (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def clean_generated(root: Path) -> None:
    makefile = root / "doc" / "Makefile"
    if makefile.exists():
        subprocess.run(["make", "-C", "doc", "clean"], cwd=root, check=False)

    for directory_name in GENERATED_DIR_NAMES:
        for path in root.rglob(directory_name):
            if ".git" in path.parts:
                continue
            if path.exists() and path.is_dir():
                shutil.rmtree(path)

    tracked_generated: list[str] = []
    for suffix in GENERATED_FILE_SUFFIXES:
        for path in root.rglob(f"*{suffix}"):
            if ".git" in path.parts:
                continue
            if is_tracked(root, path):
                tracked_generated.append(relative_to_root(root, path))
                continue
            path.unlink(missing_ok=True)

    if tracked_generated:
        joined = "\n".join(tracked_generated)
        raise SystemExit("generated artifacts are tracked and must be removed from git:\n" + joined)


def apply_patch(root: Path, item: PatchQueueItem, *, dry_run: bool, ssh: SshOptions) -> None:
    rel = relative_to_root(root, item.patch_file)
    check = subprocess.run(["git", "apply", "--check", rel], cwd=root, env=git_env(root, ssh))
    if check.returncode == 0:
        if dry_run:
            print(f"check ok: {rel}")
            return
        run_git(("apply", rel), root=root, ssh=ssh)
        return

    reverse_check = subprocess.run(
        ["git", "apply", "--reverse", "--check", rel],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=git_env(root, ssh),
    )
    if reverse_check.returncode == 0:
        print(f"already applied, skipping: {rel}")
        return

    run_git(("apply", "--check", rel), root=root, ssh=ssh)


def test_environment(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    src = str(root / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def run_tests(root: Path) -> None:
    env = test_environment(root)
    for command in DEFAULT_TEST_COMMANDS:
        run(command, root=root, env=env)


def changed_files_for_commit(root: Path, *, include_patch_artifact: bool) -> tuple[str, ...]:
    tracked = git_capture(("diff", "--name-only"), root=root).splitlines()
    staged = git_capture(("diff", "--cached", "--name-only"), root=root).splitlines()
    untracked = git_capture(("ls-files", "--others", "--exclude-standard"), root=root).splitlines()
    names = sorted(set(tracked + staged + untracked))
    if include_patch_artifact:
        return tuple(names)
    return tuple(name for name in names if not name.startswith("patch/"))


def create_commit(root: Path, item: PatchQueueItem, *, include_patch_artifact: bool, ssh: SshOptions) -> None:
    files = changed_files_for_commit(root, include_patch_artifact=include_patch_artifact)
    if not files:
        print("no file to commit")
        return
    run_git(("add", "--", *files), root=root, ssh=ssh)
    run_git(("commit", "-m", item.commit_subject), root=root, ssh=ssh)


def current_branch(root: Path) -> str:
    return git_capture(("branch", "--show-current"), root=root).strip()


def fetch_before(root: Path, *, remote: str, branch: str | None, ssh: SshOptions) -> None:
    args: tuple[str, ...]
    if branch:
        args = ("fetch", remote, branch)
    else:
        args = ("fetch", remote)
    run_git(args, root=root, ssh=ssh)


def push_after(root: Path, *, remote: str, branch: str | None, ssh: SshOptions) -> None:
    target_branch = branch or current_branch(root)
    if not target_branch:
        raise SystemExit("cannot determine current branch; pass --branch")
    run_git(("push", remote, f"HEAD:{target_branch}"), root=root, ssh=ssh)


def archive_applied_patch(root: Path, item: PatchQueueItem) -> None:
    archive_dir = root / "patch" / "_applied"
    archive_dir.mkdir(parents=True, exist_ok=True)
    destination = archive_dir / item.root.name
    if destination.exists():
        raise SystemExit(f"cannot archive {item.root}: {destination} already exists")
    item.root.rename(destination)


def check_private_key_permissions(path: Path) -> None:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        raise SystemExit(f"ssh key does not exist: {path}") from None
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise SystemExit(f"ssh key is too permissive; run chmod 600 {path}")


def auto_cert_for_key(key_file: Path) -> Path | None:
    candidate = key_file.parent / f"{key_file.name}-cert.pub"
    return candidate if candidate.exists() else None


def normalize_ssh_options(ssh: SshOptions) -> SshOptions:
    key = ssh.key_file.expanduser().resolve() if ssh.key_file else None
    cert = ssh.cert_file.expanduser().resolve() if ssh.cert_file else None
    known_hosts = ssh.known_hosts_file.expanduser().resolve() if ssh.known_hosts_file else None
    if key:
        check_private_key_permissions(key)
        if cert is None:
            cert = auto_cert_for_key(key)
    if cert and not cert.exists():
        raise SystemExit(f"ssh certificate does not exist: {cert}")
    if known_hosts and not known_hosts.exists():
        raise SystemExit(f"known_hosts file does not exist: {known_hosts}")
    return SshOptions(
        key_file=key,
        cert_file=cert,
        known_hosts_file=known_hosts,
        strict_host_key_checking=ssh.strict_host_key_checking,
        disable_agent=ssh.disable_agent,
        batch_mode=ssh.batch_mode,
    )


def build_git_ssh_command(ssh: SshOptions) -> str:
    if not any((ssh.key_file, ssh.cert_file, ssh.known_hosts_file, ssh.strict_host_key_checking, ssh.disable_agent)):
        return ""
    command = ["ssh"]
    if ssh.batch_mode:
        command.extend(["-o", "BatchMode=yes"])
    if ssh.disable_agent:
        command.extend(["-o", "IdentityAgent=none"])
    if ssh.key_file:
        command.extend(["-i", str(ssh.key_file)])
        command.extend(["-o", "IdentitiesOnly=yes"])
    if ssh.cert_file:
        command.extend(["-o", f"CertificateFile={ssh.cert_file}"])
    if ssh.known_hosts_file:
        command.extend(["-o", f"UserKnownHostsFile={ssh.known_hosts_file}"])
    if ssh.strict_host_key_checking:
        command.extend(["-o", f"StrictHostKeyChecking={ssh.strict_host_key_checking}"])
    return shlex.join(command)


def config_string(config: Mapping[str, object], key: str) -> str | None:
    value = config.get(key)
    return value if isinstance(value, str) and value else None


def config_bool(config: Mapping[str, object], key: str, default: bool) -> bool:
    value = config.get(key)
    return value if isinstance(value, bool) else default


def path_from_optional(raw: str | None) -> Path | None:
    return Path(raw).expanduser() if raw else None


def build_ssh_options(args: argparse.Namespace, config: Mapping[str, object]) -> SshOptions:
    key = args.ssh_key or os.environ.get("AUTODOC_SSH_KEY") or config_string(config, "ssh_key")
    cert = args.ssh_cert or os.environ.get("AUTODOC_SSH_CERT") or config_string(config, "ssh_cert")
    known_hosts = (
        args.ssh_known_hosts
        or os.environ.get("AUTODOC_SSH_KNOWN_HOSTS")
        or config_string(config, "ssh_known_hosts")
    )
    strict = args.ssh_strict_host_key_checking or config_string(config, "ssh_strict_host_key_checking")
    disable_agent = not args.allow_ssh_agent and config_bool(config, "disable_ssh_agent", True)
    return normalize_ssh_options(
        SshOptions(
            key_file=path_from_optional(key),
            cert_file=path_from_optional(cert),
            known_hosts_file=path_from_optional(known_hosts),
            strict_host_key_checking=strict,
            disable_agent=disable_agent,
            batch_mode=True,
        )
    )


def execute(options: PatchQueueOptions) -> int:
    items = discover_patch_items(options.patch_root)
    selected = select_patch_items(items, patch_name=options.patch_name, all_patches=options.all_patches)
    if not selected:
        print(f"no patch found in {options.patch_root}")
        return 0

    assert_clean_worktree(options.root, allow_dirty=options.allow_dirty)

    if options.fetch_before:
        fetch_before(options.root, remote=options.remote, branch=options.branch, ssh=options.ssh)

    for item in selected:
        print(f"\n==> {item.name}")
        if not options.skip_clean:
            clean_generated(options.root)

        print(f"applying {relative_to_root(options.root, item.patch_file)}")
        apply_patch(options.root, item, dry_run=options.dry_run, ssh=options.ssh)
        if options.dry_run:
            continue

        if not options.skip_clean:
            clean_generated(options.root)
        if not options.skip_tests:
            run_tests(options.root)
        if not options.skip_clean:
            clean_generated(options.root)

        if options.commit:
            create_commit(
                options.root,
                item,
                include_patch_artifact=options.include_patch_artifact,
                ssh=options.ssh,
            )

        if options.push:
            push_after(options.root, remote=options.remote, branch=options.branch, ssh=options.ssh)

        if options.archive_applied:
            archive_applied_patch(options.root, item)

        print(f"suggested commit: git commit -m {shlex.quote(item.commit_subject)}")

    if options.dry_run:
        print("dry-run complete; no patch applied")
    else:
        print("\npatch queue green")
    return 0


def parse_args(argv: Sequence[str]) -> PatchQueueOptions:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch-root", default="patch", help="root directory containing one directory per patch")
    parser.add_argument("--patch", dest="patch_name", help="patch directory name to apply")
    parser.add_argument("--all", dest="all_patches", action="store_true", help="apply every patch directory in lexical order")
    parser.add_argument("--dry-run", action="store_true", help="check patches without applying them")
    parser.add_argument("--skip-tests", action="store_true", help="apply patches without running the test gate")
    parser.add_argument("--skip-clean", action="store_true", help="do not remove generated artifacts")
    parser.add_argument("--allow-dirty", action="store_true", help="allow a dirty worktree before applying patches")
    parser.add_argument("--commit", action="store_true", help="create a Git commit after each green patch")
    parser.add_argument("--include-patch-artifact", action="store_true", help="include patch/<id>/ files in auto-commit")
    parser.add_argument("--archive-applied", action="store_true", help="move applied patch directories to patch/_applied")
    parser.add_argument("--fetch-before", action="store_true", help="run git fetch before applying patches")
    parser.add_argument("--push", action="store_true", help="run git push after a successful commit or apply")
    parser.add_argument("--remote", default=None, help="Git remote for fetch/push; default from config or origin")
    parser.add_argument("--branch", default=None, help="remote branch for fetch/push; default current branch for push")
    parser.add_argument("--ssh-key", help="private SSH key file for Git network operations")
    parser.add_argument("--ssh-cert", help="OpenSSH user certificate file, usually <key>-cert.pub")
    parser.add_argument("--ssh-known-hosts", help="known_hosts file to use for Git SSH")
    parser.add_argument(
        "--ssh-strict-host-key-checking",
        choices=("yes", "accept-new", "no"),
        help="StrictHostKeyChecking value for Git SSH",
    )
    parser.add_argument("--allow-ssh-agent", action="store_true", help="do not force IdentityAgent=none")
    args = parser.parse_args(argv)

    root = repo_root(Path.cwd())
    config = local_config(root)
    ssh = build_ssh_options(args, config)
    remote = args.remote or config_string(config, "remote") or "origin"
    branch = args.branch or config_string(config, "branch")

    return PatchQueueOptions(
        root=root,
        patch_root=(root / args.patch_root).resolve(),
        patch_name=args.patch_name,
        all_patches=args.all_patches,
        dry_run=args.dry_run,
        skip_tests=args.skip_tests,
        skip_clean=args.skip_clean,
        allow_dirty=args.allow_dirty,
        commit=args.commit,
        include_patch_artifact=args.include_patch_artifact,
        archive_applied=args.archive_applied,
        fetch_before=args.fetch_before,
        push=args.push,
        remote=remote,
        branch=branch,
        ssh=ssh,
    )


def main(argv: Sequence[str] | None = None) -> int:
    return execute(parse_args(tuple(sys.argv[1:] if argv is None else argv)))


if __name__ == "__main__":
    raise SystemExit(main())
