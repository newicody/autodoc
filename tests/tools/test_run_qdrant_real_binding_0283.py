from __future__ import annotations

import importlib.util
import json
import sys
from types import ModuleType
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools/run_qdrant_real_binding_0283.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location(
        "run_qdrant_real_binding_0283",
        TOOL_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeReadiness:
    def __init__(
        self,
        *,
        valid=True,
        local_ready=True,
        operational_ready=False,
        projection_ready=False,
        recall_ready=False,
        issues=(),
        warnings=(),
    ):
        self.valid = valid
        self.local_ready = local_ready
        self.operational_ready = operational_ready
        self.projection_ready = projection_ready
        self.recall_ready = recall_ready
        self.issues = tuple(issues)
        self.warnings = tuple(warnings)

    def to_json_dict(self):
        return {
            "schema": "fake-readiness",
            "valid": self.valid,
            "issues": list(self.issues),
            "warnings": list(self.warnings),
            "local_ready": self.local_ready,
            "operational_ready": self.operational_ready,
            "projection_ready": self.projection_ready,
            "recall_ready": self.recall_ready,
        }


class FakeAction:
    def __init__(
        self,
        *,
        valid=True,
        issues=(),
        write=False,
        search=False,
    ):
        self.valid = valid
        self.issues = tuple(issues)
        self.qdrant_write_performed = write
        self.qdrant_search_performed = search

    def to_json_dict(self):
        return {
            "schema": "fake-action",
            "valid": self.valid,
            "issues": list(self.issues),
            "qdrant_write_performed": (
                self.qdrant_write_performed
            ),
            "qdrant_search_performed": (
                self.qdrant_search_performed
            ),
        }


def _embedding_file(tmp_path):
    path = tmp_path / "embedding.json"
    path.write_text(
        json.dumps(
            {
                "embedding": {
                    "embedding_ref": "embedding:e5:test",
                    "sql_ref": "sql:context:test",
                    "source_ref": (
                        "ctx-fragment:sql:context:test"
                    ),
                    "vector": [1.0] + [0.0] * 383,
                    "dimension": 384,
                    "normalized": True,
                    "role": "query",
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def test_tool_import_ignores_preexisting_sql_store_stub(monkeypatch):
    stub = ModuleType("context.sql_context_store")
    monkeypatch.setitem(
        sys.modules,
        "context.sql_context_store",
        stub,
    )

    tool = _load_tool()

    assert tool.CLI_REPORT_SCHEMA == (
        "missipy.qdrant.real_binding_preview_first_cli.v1"
    )


def test_default_is_local_readiness_only():
    tool = _load_tool()
    calls = []

    args = tool.parse_args(())
    payload = tool.run_cli(
        args,
        readiness_runner=lambda command: (
            calls.append(command)
            or FakeReadiness()
        ),
        projection_runner=lambda command: (
            (_ for _ in ()).throw(
                AssertionError("projection must not run")
            )
        ),
        recall_runner=lambda command: (
            (_ for _ in ()).throw(
                AssertionError("recall must not run")
            )
        ),
    )

    assert payload["valid"] is True
    assert payload["operation"] == "readiness"
    assert payload["execute_requested"] is False
    assert payload["live_readiness_requested"] is False
    assert payload["data_effect_performed"] is False
    assert len(calls) == 1
    assert calls[0].live_probe is False
    assert (
        payload["configuration"]["requested_operations"]
        == []
    )


def test_projection_preview_needs_no_live_probe_or_authorization(
    tmp_path,
):
    tool = _load_tool()
    action_calls = []
    args = tool.parse_args(
        (
            "--operation",
            "projection",
            "--embedding-report",
            str(_embedding_file(tmp_path)),
        )
    )

    payload = tool.run_cli(
        args,
        readiness_runner=lambda command: FakeReadiness(),
        projection_runner=lambda command: (
            action_calls.append(command)
            or FakeAction()
        ),
    )

    assert payload["valid"] is True
    assert len(action_calls) == 1
    assert action_calls[0].execute is False
    assert payload["data_effect_performed"] is False


def test_projection_execute_requires_live_and_specific_authorization(
    tmp_path,
):
    tool = _load_tool()
    args = tool.parse_args(
        (
            "--operation",
            "projection",
            "--embedding-report",
            str(_embedding_file(tmp_path)),
            "--execute",
            "--policy-decision-id",
            "policy:test",
        )
    )

    payload = tool.run_cli(
        args,
        readiness_runner=lambda command: (
            (_ for _ in ()).throw(
                AssertionError("gate must stop before readiness")
            )
        ),
    )

    assert payload["valid"] is False
    assert "--execute requires --live-readiness" in payload["issues"]
    assert (
        "projection execute requires --authorize-projection"
        in payload["issues"]
    )


def test_authorized_projection_executes_only_after_readiness(
    tmp_path,
):
    tool = _load_tool()
    readiness_calls = []
    action_calls = []
    args = tool.parse_args(
        (
            "--operation",
            "projection",
            "--embedding-report",
            str(_embedding_file(tmp_path)),
            "--execute",
            "--live-readiness",
            "--authorize-projection",
            "--policy-decision-id",
            "policy:test:projection",
        )
    )

    payload = tool.run_cli(
        args,
        readiness_runner=lambda command: (
            readiness_calls.append(command)
            or FakeReadiness(
                operational_ready=True,
                projection_ready=True,
            )
        ),
        projection_runner=lambda command: (
            action_calls.append(command)
            or FakeAction(write=True)
        ),
    )

    assert payload["valid"] is True
    assert len(readiness_calls) == 1
    assert readiness_calls[0].live_probe is True
    assert len(action_calls) == 1
    assert action_calls[0].execute is True
    assert payload["data_effect_performed"] is True


def test_operational_readiness_blocks_projection_effect(
    tmp_path,
):
    tool = _load_tool()
    action_calls = []
    args = tool.parse_args(
        (
            "--operation",
            "projection",
            "--embedding-report",
            str(_embedding_file(tmp_path)),
            "--execute",
            "--live-readiness",
            "--authorize-projection",
            "--policy-decision-id",
            "policy:test:projection",
        )
    )

    payload = tool.run_cli(
        args,
        readiness_runner=lambda command: FakeReadiness(
            operational_ready=False,
            projection_ready=False,
        ),
        projection_runner=lambda command: (
            action_calls.append(command)
            or FakeAction(write=True)
        ),
    )

    assert payload["valid"] is False
    assert action_calls == []
    assert "projection is not operationally ready" in payload["issues"]


def test_recall_execute_uses_read_only_store_and_closes_it(
    tmp_path,
):
    tool = _load_tool()
    store = SimpleNamespace(close_count=0)

    def close():
        store.close_count += 1

    store.close = close
    recall_calls = []
    args = tool.parse_args(
        (
            "--operation",
            "recall",
            "--embedding-report",
            str(_embedding_file(tmp_path)),
            "--execute",
            "--live-readiness",
            "--authorize-recall",
            "--policy-decision-id",
            "policy:test:recall",
            "--db-path",
            str(tmp_path / "authority.sqlite3"),
        )
    )

    payload = tool.run_cli(
        args,
        readiness_runner=lambda command: FakeReadiness(
            operational_ready=True,
            recall_ready=True,
        ),
        recall_runner=lambda command: (
            recall_calls.append(command)
            or FakeAction(search=True)
        ),
        store_builder=lambda path: store,
    )

    assert payload["valid"] is True
    assert len(recall_calls) == 1
    assert recall_calls[0].execute is True
    assert recall_calls[0].store is store
    assert store.close_count == 1
    assert payload["sql_store"] == {
        "opened": True,
        "closed": True,
        "read_only_when_opened": True,
    }
    assert payload["data_effect_performed"] is True


def test_wrong_authorization_flag_is_rejected(tmp_path):
    tool = _load_tool()
    args = tool.parse_args(
        (
            "--operation",
            "recall",
            "--embedding-report",
            str(_embedding_file(tmp_path)),
            "--execute",
            "--live-readiness",
            "--authorize-projection",
            "--policy-decision-id",
            "policy:test:recall",
        )
    )

    payload = tool.run_cli(args)

    assert payload["valid"] is False
    assert (
        "recall execute requires --authorize-recall"
        in payload["issues"]
    )
    assert (
        "--authorize-projection is invalid for recall"
        in payload["issues"]
    )


def test_authorization_flags_are_invalid_in_preview(tmp_path):
    tool = _load_tool()
    args = tool.parse_args(
        (
            "--operation",
            "projection",
            "--embedding-report",
            str(_embedding_file(tmp_path)),
            "--authorize-projection",
        )
    )

    payload = tool.run_cli(args)

    assert payload["valid"] is False
    assert (
        "authorization flags require --execute"
        in payload["issues"]
    )


def test_recall_limit_is_bounded_before_configuration(tmp_path):
    tool = _load_tool()
    args = tool.parse_args(
        (
            "--operation",
            "recall",
            "--embedding-report",
            str(_embedding_file(tmp_path)),
            "--recall-limit",
            "33",
            "--max-recall-hits",
            "32",
        )
    )

    payload = tool.run_cli(args)

    assert payload["valid"] is False
    assert (
        "--recall-limit must not exceed --max-recall-hits"
        in payload["issues"]
    )


def test_main_writes_atomic_json_report(tmp_path, monkeypatch):
    tool = _load_tool()
    output = tmp_path / "reports" / "result.json"

    monkeypatch.setattr(
        tool,
        "run_cli",
        lambda args: {
            "schema": tool.CLI_REPORT_SCHEMA,
            "valid": True,
            "issues": [],
            "warnings": [],
            "operation": "readiness",
            "execute_requested": False,
            "live_readiness_requested": False,
            "data_effect_performed": False,
            "readiness": {},
        },
    )

    exit_code = tool.main(
        (
            "--output",
            str(output),
            "--format",
            "json",
        )
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert not output.with_suffix(".json.tmp").exists()
