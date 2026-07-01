from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "apply_patch_queue.py"
SOURCE = SCRIPT.read_text(encoding="utf-8")


def test_patch_queue_has_status_command() -> None:
    assert "--status" in SOURCE
    assert "PatchQueueStatus" in SOURCE
    assert "missipy.patch_queue.status.v1" in SOURCE


def test_patch_queue_status_does_not_render_private_ssh_paths() -> None:
    render_section = SOURCE.split("def render_patch_queue_status", 1)[1]
    assert "ssh_key" not in render_section
    assert "key_file" not in render_section
    assert "cert_file" not in render_section
