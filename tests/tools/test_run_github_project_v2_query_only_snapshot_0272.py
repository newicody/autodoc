import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_github_project_v2_query_only_snapshot_0272.py"
BASE_CONFIG = ROOT / "config/github_project_v2_query_only.example.ini"


def _config(tmp_path: Path) -> Path:
    text = BASE_CONFIG.read_text(encoding="utf-8")
    text = text.replace(
        "output_dir = .var/github/project_v2/snapshots",
        f"output_dir = {tmp_path / 'snapshots'}",
    )
    path = tmp_path / "project.ini"
    path.write_text(text, encoding="utf-8")
    return path


def _fixture(tmp_path: Path) -> Path:
    payload = {
        "project": {
            "id": "PVT_kwHOA3ouXM4Ba3Ar",
            "number": 2,
            "title": "idea",
            "url": "https://github.com/users/newicody/projects/2",
            "closed": False,
        },
        "fields": [
            {"id": "PVTSSF_status", "name": "Status", "dataType": "SINGLE_SELECT"}
        ],
        "items": [
            {
                "id": "PVTI_item",
                "type": "DRAFT_ISSUE",
                "content": {"id": "DI_item", "title": "Test", "body": "No effect"},
                "fieldValues": {"nodes": []},
            }
        ],
    }
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_0272_r3_cli_plan_only(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--config",
            str(_config(tmp_path)),
            "--output",
            str(report),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "execute=False" in completed.stdout
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["external_call_performed"] is False


def test_0272_r3_cli_fixture_writes_immutable_snapshot(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--config",
            str(_config(tmp_path)),
            "--execute",
            "--policy-decision-id",
            "policy:0272:fixture",
            "--fixture-json",
            str(_fixture(tmp_path)),
            "--output",
            str(report),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["counts"]["item_count"] == 1
    assert payload["external_call_performed"] is False
    snapshot_path = Path(payload["snapshot_path"])
    assert snapshot_path.exists()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["project"]["id"] == "PVT_kwHOA3ouXM4Ba3Ar"
    assert "GITHUB_TOKEN" not in snapshot_path.read_text(encoding="utf-8")
