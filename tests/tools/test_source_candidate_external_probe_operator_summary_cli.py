from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from source_candidate_external_probe_operator_summary_cli import main  # noqa: E402


def _write_index(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.external_probe_artifact_index.v1",
                "root": "/tmp/repo",
                "scan_root": "/tmp/repo/bundles",
                "bundle_count": 1,
                "total_artifact_count": 3,
                "total_byte_count": 123,
                "entries": [
                    {
                        "schema": "missipy.source_candidate.external_probe_artifact_index_entry.v1",
                        "bundle_path": "bundles/one",
                        "manifest_path": "bundles/one/manifest.json",
                        "repository": "newicody/autodoc",
                        "read_only": True,
                        "external_call_performed": False,
                        "probe_allowed": True,
                        "artifact_count": 3,
                        "byte_count": 123,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_external_probe_operator_summary_cli_writes_summary(tmp_path: Path, capsys) -> None:
    index = tmp_path / "index.json"
    output = tmp_path / "summary.json"
    _write_index(index)

    exit_code = main(["--index", str(index), "--output", str(output)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "external probe operator summary" in captured.out
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["ready_count"] == 1


def test_external_probe_operator_summary_cli_prints_json(tmp_path: Path, capsys) -> None:
    index = tmp_path / "index.json"
    output = tmp_path / "summary.json"
    _write_index(index)

    exit_code = main(["--index", str(index), "--output", str(output), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema"] == "missipy.source_candidate.external_probe_operator_summary.v1"
    assert payload["bundle_count"] == 1
