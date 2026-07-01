from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True)


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "tracked.txt").write_text("ok\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-q", "-m", "baseline")


def test_status_json_reports_patch_queue_without_secret_paths(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    patch_dir = repo / "patch" / "0002-demo"
    patch_dir.mkdir(parents=True)
    (patch_dir / "patch.diff").write_text("", encoding="utf-8")
    key = tmp_path / "id_ed25519_autodoc"
    cert = tmp_path / "id_ed25519_autodoc-cert.pub"
    key.write_text("not-a-real-key\n", encoding="utf-8")
    cert.write_text("not-a-real-cert\n", encoding="utf-8")
    key.chmod(0o600)
    (repo / ".patchqueue.local.json").write_text(
        json.dumps(
            {
                "ssh_key": str(key),
                "ssh_cert": str(cert),
                "remote": "origin",
            }
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["PYTHONPATH"] = os.getcwd()
    result = subprocess.run(
        [sys.executable, str(Path(os.getcwd()) / "apply_patch_queue.py"), "--status", "--status-format", "json"],
        cwd=repo,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )

    payload = json.loads(result.stdout)
    assert payload["schema"] == "missipy.patch_queue.status.v1"
    assert payload["patches"] == ["0002-demo"]
    assert payload["local_config_present"] is True
    assert payload["ssh_configured"] is True
    assert payload["ssh_cert_configured"] is True
    assert str(key) not in result.stdout
    assert str(cert) not in result.stdout


def test_status_text_reports_flat_patch_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    patch_root = repo / "patch"
    patch_root.mkdir()
    (patch_root / "bad.patch").write_text("", encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONPATH"] = os.getcwd()
    result = subprocess.run(
        [sys.executable, str(Path(os.getcwd()) / "apply_patch_queue.py"), "--status"],
        cwd=repo,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )

    assert "Patch queue status" in result.stdout
    assert "flat_patches_forbidden: bad.patch" in result.stdout
