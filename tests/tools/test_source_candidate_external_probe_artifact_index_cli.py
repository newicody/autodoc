from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from source_candidate_external_probe_artifact_index_cli import main  # noqa: E402


def _write_bundle(path: Path) -> None:
    path.mkdir(parents=True)
    (path / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.external_probe_bundle.v1",
                "path": str(path),
                "manifest_path": str(path / "manifest.json"),
                "repository": "newicody/autodoc",
                "read_only": True,
                "external_call_performed": False,
                "probe_allowed": True,
                "artifact_count": 3,
                "byte_count": 123,
                "artifacts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_external_probe_artifact_index_cli_writes_index(tmp_path: Path, capsys) -> None:
    scan_root = tmp_path / "bundles"
    output = tmp_path / "index.json"
    _write_bundle(scan_root / "one")

    exit_code = main(["--root", str(tmp_path), "--scan-root", str(scan_root), "--output", str(output)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "external probe artifact index" in captured.out
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["bundle_count"] == 1


def test_external_probe_artifact_index_cli_prints_json(tmp_path: Path, capsys) -> None:
    scan_root = tmp_path / "bundles"
    output = tmp_path / "index.json"
    _write_bundle(scan_root / "one")

    exit_code = main(
        [
            "--root",
            str(tmp_path),
            "--scan-root",
            str(scan_root),
            "--output",
            str(output),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema"] == "missipy.source_candidate.external_probe_artifact_index.v1"
    assert payload["bundle_count"] == 1
