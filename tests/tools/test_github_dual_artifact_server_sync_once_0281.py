from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools/run_github_dual_artifact_server_sync_once_0281.py"


def _load_tool():
    spec = spec_from_file_location("dual_artifact_sync_0281", TOOL_PATH)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_member(run_root: Path, artifact_id: str, filename: str, payload: object) -> None:
    target = run_root / artifact_id / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, bytes):
        target.write_bytes(payload)
    else:
        target.write_text(json.dumps(payload), encoding="utf-8")


def test_run_group_waits_until_manifest_declared_advisory_is_present(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tool = _load_tool()
    run_root = tmp_path / "run"
    _write_member(run_root, "1", "authoritative_request.json", {"schema": "request"})
    _write_member(
        run_root,
        "2",
        "dual_artifact_manifest.json",
        {
            "schema": "manifest",
            "advisory_filename": "copilot_advisory.json",
            "advisory_sha256": "a" * 64,
        },
    )

    called = False

    def fail_if_called(command):
        nonlocal called
        called = True
        raise AssertionError("assembly must wait for the advisory")

    monkeypatch.setattr(tool, "run_github_dual_artifact_run_assembly", fail_if_called)
    result = tool._build_run_group(
        repository="newicody/projects",
        run_id="42",
        run_root=run_root,
    )

    assert result["status"] == "pending"
    assert result["issues"] == ["waiting for copilot_advisory.json"]
    assert called is False


def test_run_group_collects_three_artifacts_and_delegates_to_0281_r2(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tool = _load_tool()
    run_root = tmp_path / "run"
    _write_member(run_root, "10", "authoritative_request.json", b'{"schema":"request"}')
    _write_member(
        run_root,
        "20",
        "dual_artifact_manifest.json",
        {
            "schema": "manifest",
            "advisory_filename": "copilot_advisory.json",
        },
    )
    _write_member(
        run_root,
        "30",
        "copilot_advisory.json",
        b'{"summary":"Copilot content retained"}',
    )

    captured = {}

    def fake_assembly(command):
        captured["command"] = command
        return SimpleNamespace(
            valid=True,
            issues=(),
            to_mapping=lambda: {
                "schema": "missipy.github.dual_artifact_run_assembly.v1",
                "valid": True,
                "intake": {
                    "advisory": {"summary": "Copilot content retained"},
                    "source_candidate": {"title": "authoritative only"},
                },
            },
        )

    monkeypatch.setattr(tool, "run_github_dual_artifact_run_assembly", fake_assembly)
    result = tool._build_run_group(
        repository="newicody/projects",
        run_id="42",
        run_root=run_root,
    )

    assert result["status"] == "ready"
    assert result["advisory_payload_retained"] is True
    assert result["advisory_content_authoritative"] is False
    assert result["github_mutation_performed"] is False

    command = captured["command"]
    assert command.repository == "newicody/projects"
    assert command.run_id == "42"
    assert {
        (member.artifact_name, member.filename)
        for member in command.members
    } == {
        ("autodoc-authoritative-request", "authoritative_request.json"),
        ("autodoc-copilot-advisory", "copilot_advisory.json"),
        ("autodoc-dual-artifact-manifest", "dual_artifact_manifest.json"),
    }


def test_ready_run_report_is_replay_safe_and_collision_guarded(
    tmp_path: Path,
) -> None:
    tool = _load_tool()
    path = tmp_path / "report.json"
    ready = {
        "schema": "missipy.github.dual_artifact_fetch_run_group.v1",
        "status": "ready",
        "repository": "newicody/projects",
        "run_id": "42",
        "assembly": {"valid": True},
    }

    action, effective = tool._persist_run_report(path, ready)
    assert action == "created"
    assert effective == ready

    action, effective = tool._persist_run_report(path, ready)
    assert action == "replayed"
    assert effective == ready

    changed = dict(ready)
    changed["assembly"] = {"valid": True, "different": True}
    action, effective = tool._persist_run_report(path, changed)
    assert action == "collision"
    assert effective == ready
    assert json.loads(path.read_text(encoding="utf-8")) == ready


def test_pending_report_can_progress_to_ready(tmp_path: Path) -> None:
    tool = _load_tool()
    path = tmp_path / "report.json"
    pending = {"schema": "x", "status": "pending", "issues": ["waiting"]}
    ready = {"schema": "x", "status": "ready", "issues": []}

    assert tool._persist_run_report(path, pending)[0] == "created"
    action, effective = tool._persist_run_report(path, ready)

    assert action == "updated"
    assert effective == ready
    assert json.loads(path.read_text(encoding="utf-8")) == ready


def test_base_sync_is_called_through_existing_cli_contract(tmp_path: Path) -> None:
    tool = _load_tool()
    fake_sync = tmp_path / "fake_sync.py"
    fake_sync.write_text(
        """
import json
print(json.dumps({
    "status": "ok",
    "vispy_event_path": "/tmp/observation.json"
}))
""".lstrip(),
        encoding="utf-8",
    )
    config = tmp_path / "fetch.ini"
    config.write_text("[artifact_source]\nrepositories=newicody/projects\n", encoding="utf-8")
    artifact_dir = tmp_path / "run" / "artifact"
    artifact_dir.mkdir(parents=True)

    result = tool._run_base_sync(
        fake_sync,
        config,
        artifact_dir,
        "42",
        "100",
    )

    assert result["status"] == "ok"
    assert result["vispy_event_path"] == "/tmp/observation.json"
