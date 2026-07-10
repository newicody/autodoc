import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0268_tool_builds_readiness_report_and_script(tmp_path: Path) -> None:
    closed = tmp_path / "closed.json"
    handoff = tmp_path / "handoff.json"
    output = tmp_path / "readiness.json"
    script = tmp_path / "autodoc-local-runtime.openrc"

    closed.write_text(
        json.dumps(
            {
                "valid": True,
                "sql_ref": "sql:inference_context:tool",
                "embedding_ref": "embedding:passage:tool",
                "hydrated_count": 1,
                "missing_count": 0,
                "executes_runtime": False,
            }
        ),
        encoding="utf-8",
    )
    handoff.write_text(
        json.dumps(
            {
                "valid": True,
                "handoff_ref": "github-scan-once-handoff:tool",
                "scan_once": True,
                "remote_mutation_allowed": False,
                "request": {"repository": "newicody/autodoc"},
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/build_openrc_launcher_minimal_readiness_0268.py",
            "--closed-frame-report",
            str(closed),
            "--github-handoff",
            str(handoff),
            "--output",
            str(output),
            "--script-output",
            str(script),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "openrc_launcher_minimal_readiness_valid=True" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == "missipy.openrc_launcher_minimal_readiness.v1"
    assert payload["readiness_only"] is True
    assert payload["calls_rc_service"] is False
    assert script.read_text(encoding="utf-8").startswith("#!/sbin/openrc-run")
