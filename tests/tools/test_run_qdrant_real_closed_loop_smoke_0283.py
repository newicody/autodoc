from __future__ import annotations

import importlib.util
import json
import sys
from types import ModuleType
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = (
    ROOT
    / "tools/run_qdrant_real_closed_loop_smoke_0283.py"
)


def _load_tool():
    spec = importlib.util.spec_from_file_location(
        "run_qdrant_real_closed_loop_smoke_0283",
        TOOL_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeEmbeddingResult:
    def __init__(self, role, execute, fixture, *, demo=False):
        self.valid = True
        self.issues = ()
        self.execute = execute
        self.dry_run = not execute
        self.embedding_text = (
            f"{role}: {fixture['title']}\n{fixture['body']}"
        )
        model = (
            "demo.openvino.embedding.e5-small"
            if demo
            else "openvino.embedding.e5-small"
        )
        self.embedding = (
            {
                "embedding_ref": f"embedding:{role}:fixture",
                "source_ref": (
                    f"ctx-fragment:{fixture['context_ref']}"
                ),
                "sql_ref": fixture["context_ref"],
                "backend_ref": (
                    "openvino:model:multilingual-e5-small"
                ),
                "role": role,
                "dimension": 384,
                "normalized": True,
                "l2_norm": 1.0,
                "metadata": {
                    "context_ref": fixture["context_ref"],
                    "model": model,
                    "tokenizer": (
                        "transformers.multilingual-e5-small"
                    ),
                    "model_path": "/model",
                    "device": "CPU",
                },
                "vector": [1.0] + [0.0] * 383,
            }
            if execute
            else {}
        )
        self._fixture = fixture
        self._role = role

    def to_mapping(self):
        return {
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "dry_run": self.dry_run,
            "record": dict(self._fixture),
            "embedding_text": self.embedding_text,
            "embedding": dict(self.embedding),
            "request": {"role": self._role},
        }


class FakeReadiness:
    def __init__(self, *, live, operation):
        self.valid = True
        self.issues = ()
        self.warnings = (
            ()
            if live
            else ("live collection probe not requested",)
        )
        self.local_ready = True
        self.operational_ready = live
        self.projection_ready = (
            live and operation == "projection"
        )
        self.recall_ready = live and operation == "recall"

    def to_json_dict(self):
        return {
            "valid": self.valid,
            "issues": [],
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
        kind,
        fixture,
        execute,
        valid=True,
    ):
        self.kind = kind
        self.valid = valid
        self.issues = ()
        self.qdrant_write_performed = (
            kind == "projection" and execute and valid
        )
        self.qdrant_search_performed = (
            kind == "recall" and execute and valid
        )
        self._fixture = fixture
        self._execute = execute

    def to_json_dict(self):
        if self.kind == "projection":
            usage = {
                "write_result": {
                    "point_ids": (
                        ["qdrant-point:smoke"]
                        if self._execute
                        else []
                    ),
                    "acknowledged": self._execute,
                }
            }
        else:
            usage = {
                "sql_refs": (
                    [self._fixture["context_ref"]]
                    if self._execute
                    else []
                ),
                "hydrated_records": (
                    [dict(self._fixture)]
                    if self._execute
                    else []
                ),
                "recall": {
                    "planned": not self._execute,
                },
            }
        return {
            "valid": self.valid,
            "issues": [],
            "execute": self._execute,
            "usage_result": usage,
            "qdrant_write_performed": (
                self.qdrant_write_performed
            ),
            "qdrant_search_performed": (
                self.qdrant_search_performed
            ),
        }


class FakeSession:
    def __init__(self, fixture):
        self.fixture = dict(fixture)
        self.store = SimpleNamespace(
            get_record=lambda ref: (
                dict(self.fixture)
                if ref == self.fixture["context_ref"]
                else None
            )
        )
        self.write_result = {
            "inserted": True,
            "replaced": False,
            "context_ref": fixture["context_ref"],
        }
        self.close_count = 0

    def close(self):
        self.close_count += 1


def _request_builder(**values):
    return SimpleNamespace(**values)


def _demo_embedding_builder(
    text,
    sql_ref,
    model_dir=None,
    device="CPU",
    *,
    role="passage",
    dimension=384,
):
    return {
        "embedding_ref": f"embedding:{role}:demo",
        "source_ref": f"ctx-fragment:{sql_ref}",
        "sql_ref": sql_ref,
        "backend_ref": "openvino:model:multilingual-e5-small",
        "role": role,
        "dimension": dimension,
        "normalized": True,
        "l2_norm": 1.0,
        "metadata": {
            "context_ref": sql_ref,
            "model": "demo.openvino.embedding.e5-small",
            "tokenizer": "demo.tokenizer",
            "model_path": model_dir or "",
            "device": device,
        },
        "vector": [1.0] + [0.0] * (dimension - 1),
    }


def _runners(tool, fixture_holder, calls):
    def embedding_runner(store, request, *, execute=False):
        fixture = fixture_holder["fixture"]
        calls.append(("embedding", request.role, execute))
        return FakeEmbeddingResult(
            request.role,
            execute,
            fixture,
        )

    def readiness_runner(command):
        operation = (
            command.configuration.requested_operations[0]
        )
        calls.append(
            ("readiness", operation, command.live_probe)
        )
        return FakeReadiness(
            live=command.live_probe,
            operation=operation,
        )

    def projection_runner(command):
        fixture = fixture_holder["fixture"]
        calls.append(("projection", command.execute))
        return FakeAction(
            kind="projection",
            fixture=fixture,
            execute=command.execute,
        )

    def recall_runner(command):
        fixture = fixture_holder["fixture"]
        calls.append(("recall", command.execute))
        return FakeAction(
            kind="recall",
            fixture=fixture,
            execute=command.execute,
        )

    return (
        embedding_runner,
        readiness_runner,
        projection_runner,
        recall_runner,
    )


def test_tool_import_ignores_preexisting_0261_stub(
    monkeypatch,
):
    stub = ModuleType(
        "context.scheduler_managed_sql_ref_openvino_embedding_usage_0261"
    )
    monkeypatch.setitem(
        sys.modules,
        (
            "context."
            "scheduler_managed_sql_ref_openvino_embedding_usage_0261"
        ),
        stub,
    )

    tool = _load_tool()

    assert tool.SMOKE_REPORT_SCHEMA == (
        "missipy.qdrant.real_closed_loop_smoke.v1"
    )


def test_default_preview_has_no_sql_openvino_or_qdrant_effect(
    tmp_path,
):
    tool = _load_tool()
    args = tool.parse_args(
        (
            "--db-path",
            str(tmp_path / "smoke.sqlite3"),
            "--model-dir",
            str(tmp_path / "missing-model-is-ok-in-preview"),
        )
    )
    holder = {"fixture": tool._fixture_mapping(args)}
    calls = []
    runners = _runners(tool, holder, calls)
    sql_calls = []

    payload = tool.run_smoke(
        args,
        sql_session_builder=lambda *items: sql_calls.append(items),
        embedding_runner=runners[0],
        embedding_request_builder=_request_builder,
        demo_embedding_builder=_demo_embedding_builder,
        readiness_runner=runners[1],
        projection_runner=runners[2],
        recall_runner=runners[3],
    )

    assert payload["valid"] is True
    assert payload["execute_requested"] is False
    assert sql_calls == []
    assert ("embedding", "passage", False) in calls
    assert ("embedding", "query", False) in calls
    assert ("readiness", "projection", False) in calls
    assert ("readiness", "recall", False) in calls
    assert ("projection", False) in calls
    assert ("recall", False) in calls
    assert payload["embedding"]["demo_vectors_used"] is True
    assert payload["cleanup"] == {}


def test_execute_requires_both_authorizations_and_decision(
    tmp_path,
):
    tool = _load_tool()
    model = tmp_path / "model"
    model.mkdir()
    args = tool.parse_args(
        (
            "--execute",
            "--model-dir",
            str(model),
        )
    )

    payload = tool.run_smoke(args)

    assert payload["valid"] is False
    assert "--execute requires --authorize-smoke" in payload["issues"]
    assert any(
        "--authorize-persistent-smoke-point" in issue
        for issue in payload["issues"]
    )
    assert (
        "--execute requires --policy-decision-id"
        in payload["issues"]
    )


def test_execute_runs_sql_e5_projection_recall_and_verifies(
    tmp_path,
):
    tool = _load_tool()
    model = tmp_path / "model"
    model.mkdir()
    args = tool.parse_args(
        (
            "--execute",
            "--authorize-smoke",
            "--authorize-persistent-smoke-point",
            "--policy-decision-id",
            "policy:0283:r8:smoke",
            "--model-dir",
            str(model),
            "--db-path",
            str(tmp_path / "smoke.sqlite3"),
        )
    )
    fixture = tool._fixture_mapping(args)
    holder = {"fixture": fixture}
    calls = []
    runners = _runners(tool, holder, calls)
    session = FakeSession(fixture)

    payload = tool.run_smoke(
        args,
        sql_session_builder=lambda *items: session,
        embedding_runner=runners[0],
        embedding_request_builder=_request_builder,
        demo_embedding_builder=_demo_embedding_builder,
        readiness_runner=runners[1],
        projection_runner=runners[2],
        recall_runner=runners[3],
    )

    assert payload["valid"] is True
    assert payload["verification"]["closed_loop_verified"] is True
    assert payload["verification"]["fixture_rehydrated"] is True
    assert payload["verification"]["authority_body_matches"] is True
    assert payload["cleanup"]["required"] is True
    assert payload["cleanup"]["automatic_cleanup_performed"] is False
    assert payload["cleanup"]["qdrant_point_ids"] == [
        "qdrant-point:smoke"
    ]
    assert session.close_count == 1
    assert ("embedding", "passage", True) in calls
    assert ("embedding", "query", True) in calls
    assert ("readiness", "projection", True) in calls
    assert ("readiness", "recall", True) in calls
    assert ("projection", True) in calls
    assert ("recall", True) in calls


def test_execute_stops_before_projection_when_readiness_fails(
    tmp_path,
):
    tool = _load_tool()
    model = tmp_path / "model"
    model.mkdir()
    args = tool.parse_args(
        (
            "--execute",
            "--authorize-smoke",
            "--authorize-persistent-smoke-point",
            "--policy-decision-id",
            "policy:0283:r8:smoke",
            "--model-dir",
            str(model),
            "--db-path",
            str(tmp_path / "smoke.sqlite3"),
        )
    )
    fixture = tool._fixture_mapping(args)
    session = FakeSession(fixture)
    action_calls = []

    def embedding_runner(store, request, *, execute=False):
        return FakeEmbeddingResult(
            request.role,
            execute,
            fixture,
        )

    class NotReady(FakeReadiness):
        def __init__(self, operation):
            super().__init__(live=True, operation=operation)
            self.operational_ready = False
            self.projection_ready = False
            self.recall_ready = False
            self.valid = False
            self.issues = ("collection unavailable",)

    payload = tool.run_smoke(
        args,
        sql_session_builder=lambda *items: session,
        embedding_runner=embedding_runner,
        embedding_request_builder=_request_builder,
        demo_embedding_builder=_demo_embedding_builder,
        readiness_runner=lambda command: NotReady(
            command.configuration.requested_operations[0]
        ),
        projection_runner=lambda command: action_calls.append(command),
        recall_runner=lambda command: action_calls.append(command),
    )

    assert payload["valid"] is False
    assert action_calls == []
    assert payload["cleanup"]["sql_fixture_written"] is True
    assert payload["cleanup"]["qdrant_point_written"] is False
    assert session.close_count == 1


def test_demo_embedding_is_rejected_in_execute(tmp_path):
    tool = _load_tool()
    model = tmp_path / "model"
    model.mkdir()
    args = tool.parse_args(
        (
            "--execute",
            "--authorize-smoke",
            "--authorize-persistent-smoke-point",
            "--policy-decision-id",
            "policy:0283:r8:smoke",
            "--model-dir",
            str(model),
        )
    )
    fixture = tool._fixture_mapping(args)
    session = FakeSession(fixture)

    def demo_runner(store, request, *, execute=False):
        result = FakeEmbeddingResult(
            request.role,
            execute,
            fixture,
        )
        result.embedding["metadata"]["model"] = (
            "demo.openvino.embedding.e5-small"
        )
        return result

    payload = tool.run_smoke(
        args,
        sql_session_builder=lambda *items: session,
        embedding_runner=demo_runner,
        embedding_request_builder=_request_builder,
        demo_embedding_builder=_demo_embedding_builder,
    )

    assert payload["valid"] is False
    assert any(
        "must not use demo model" in issue
        for issue in payload["issues"]
    )
    assert session.close_count == 1


def test_dimension_is_locked_to_multilingual_e5_small():
    tool = _load_tool()
    args = tool.parse_args(
        ("--vector-dimension", "385")
    )

    payload = tool.run_smoke(args)

    assert payload["valid"] is False
    assert (
        "--vector-dimension must be 384 for multilingual-e5-small"
        in payload["issues"]
    )


def test_main_writes_atomic_report(tmp_path, monkeypatch):
    tool = _load_tool()
    output = tmp_path / "reports" / "smoke.json"
    monkeypatch.setattr(
        tool,
        "run_smoke",
        lambda args: {
            "schema": tool.SMOKE_REPORT_SCHEMA,
            "valid": True,
            "issues": [],
            "execute_requested": False,
            "verification": {},
            "cleanup": {},
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
    assert json.loads(
        output.read_text(encoding="utf-8")
    )["valid"] is True
    assert not output.with_suffix(".json.tmp").exists()
