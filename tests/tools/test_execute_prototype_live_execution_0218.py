from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import importlib.util
import json
import sys
import threading


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "execute_prototype_live_execution.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("execute_prototype_live_execution_tool", TOOL)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _FakeQdrantHandler(BaseHTTPRequestHandler):
    point: dict | None = None

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return

    def do_DELETE(self) -> None:
        if self.path.startswith("/collections/autodoc_prototype_live"):
            type(self).point = None
            self._json(200, {"result": True, "status": "ok"})
            return
        self._json(404, {"status": "not_found"})

    def do_PUT(self) -> None:
        body = self._body()
        if self.path == "/collections/autodoc_prototype_live":
            self._json(200, {"result": True, "status": "ok"})
            return
        if self.path == "/collections/autodoc_prototype_live/points?wait=true":
            payload = json.loads(body.decode("utf-8"))
            type(self).point = payload["points"][0]
            self._json(200, {"result": {"operation_id": 1, "status": "completed"}, "status": "ok"})
            return
        self._json(404, {"status": "not_found"})

    def do_POST(self) -> None:
        if self.path == "/collections/autodoc_prototype_live/points/search":
            point = type(self).point
            self._json(200, {"result": [{"id": point["id"], "score": 1.0, "payload": point["payload"]}], "status": "ok"})
            return
        self._json(404, {"status": "not_found"})

    def _body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class _Server:
    def __enter__(self):
        _FakeQdrantHandler.point = None
        self.server = HTTPServer(("127.0.0.1", 0), _FakeQdrantHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.url = f"http://{host}:{port}"
        return self

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.thread.join(timeout=3)


def _plan_fixture(tmp_path: Path, qdrant_url: str, *, ready: bool = True) -> dict:
    runtime = tmp_path / "runtime" / "dev-controlled"
    live = runtime / "prototype-live"
    sql_ref = "baseline:controlled-dev-routeproxy-write-read-v1:3195a2fcf10586d5"
    point = {
        "id": "088343f2-1aae-7f98-69a2-94e2588df496",
        "vector": [0.730469, 0.316406, 0.824219, 0.78125],
        "payload": {
            "sql_ref": sql_ref,
            "prototype_run_id": "6df6b4e543755462",
            "integration_digest": "integration-digest",
            "projection_digest": "projection-digest",
        },
    }
    return {
        "schema": "missipy.prototype.live_execution_plan.v1",
        "bloc": "H",
        "target_runtime_root": str(runtime),
        "target_isolated_runtime_root": str(runtime / "routeproxy-isolated"),
        "prototype_live_root": str(live),
        "accepted_baseline": "prototype-live-execution-plan-v1",
        "prototype_live_execution_plan_ready": ready,
        "p0218_may_execute_live_prototype": ready,
        "planned_next_patch": "0218-prototype_live_execution_acceptance",
        "target_path": "context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact",
        "sql_ref": sql_ref,
        "qdrant_payload": {"sql_ref": sql_ref},
        "projection_digest": "projection-digest",
        "integration_digest": "integration-digest",
        "source_entry_digest": "source-entry-digest",
        "issues": [] if ready else ["not ready"],
        "warnings": [],
        "existing_surfaces_reused": True,
        "prototype_run_id": "6df6b4e543755462",
        "qdrant_url": qdrant_url,
        "qdrant_collection": "autodoc_prototype_live",
        "qdrant_point": point,
        "sql_dev_store": str(live / "prototype_live_sql.jsonl"),
        "sql_record": {
            "schema": "missipy.prototype.live_sql_record.v1",
            "prototype_run_id": "6df6b4e543755462",
            "sql_ref": sql_ref,
            "kind": "prototype_live_record",
            "content": "Controlled prototype live record for context recall rehydrate.",
        },
        "response_artifact": str(live / "prototype_live_response.json"),
        "qdrant_requests": {"search_url": f"{qdrant_url}/collections/autodoc_prototype_live/points/search"},
        "prototype_expected_result": {
            "sql_written_by_0218": True,
            "qdrant_written_by_0218": True,
            "qdrant_queried_by_0218": True,
            "sql_record_read_by_0218": True,
            "rehydration_executed_by_0218": True,
            "response_artifact_written_by_0218": True,
            "prototype_success": True,
        },
        "p0218_required_true_flags": [
            "sql_written_by_0218",
            "qdrant_written_by_0218",
            "qdrant_queried_by_0218",
            "sql_record_read_by_0218",
            "rehydration_executed_by_0218",
            "response_artifact_written_by_0218",
            "prototype_success",
        ],
        "execution_allowed_by_0217": False,
        "runtime_imports_executed_by_0217": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0217": False,
        "routeproxy_prepared_by_0217": False,
        "read_route_frame_called_by_0217": False,
        "writer_permits_requested_by_0217": False,
        "frames_written_by_0217": False,
        "controlproxy_frames_written_by_0217": False,
        "eventbus_instantiated_by_0217": False,
        "network_used_by_0217": False,
        "external_network_used_by_0217": False,
        "live_qdrant_query_executed_by_0217": False,
        "qdrant_queried_by_0217": False,
        "sql_record_read_by_0217": False,
        "recall_executed_by_0217": False,
        "sql_write_allowed_by_0217": False,
        "qdrant_write_allowed_by_0217": False,
        "sql_written_by_0217": False,
        "qdrant_written_by_0217": False,
        "runtime_history_rewritten_by_0217": False,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_scheduler_added": False,
        "new_controlproxy_runtime_added": False,
        "new_routeproxy_runtime_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
        "new_graph_renderer_added": False,
        "new_inference_path_added": False,
    }


def test_0218_executes_live_controlled_prototype(tmp_path: Path) -> None:
    module = _load_tool_module()
    with _Server() as server:
        plan = _plan_fixture(tmp_path, server.url)
        runtime = Path(plan["target_runtime_root"])
        runtime.mkdir(parents=True)
        plan_path = runtime / "prototype_live_execution_plan.json"
        output = runtime / "prototype_live_execution_acceptance.json"
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

        acceptance = module.execute_prototype_live_execution(
            live_execution_plan_path=plan_path,
            output_path=output,
            timeout_seconds=3.0,
        )

    assert acceptance["prototype_live_execution_accepted"] is True
    assert acceptance["prototype_success"] is True
    assert acceptance["bloc_h_complete"] is True
    assert acceptance["cycle_complete"] is True
    assert acceptance["sql_written_by_0218"] is True
    assert acceptance["qdrant_collection_ready_by_0218"] is True
    assert acceptance["qdrant_written_by_0218"] is True
    assert acceptance["qdrant_queried_by_0218"] is True
    assert acceptance["sql_record_read_by_0218"] is True
    assert acceptance["rehydration_executed_by_0218"] is True
    assert acceptance["response_artifact_written_by_0218"] is True
    assert acceptance["external_network_used_by_0218"] is False
    assert acceptance["new_sql_backend_added"] is False
    assert acceptance["new_qdrant_backend_added"] is False
    assert Path(acceptance["sqlite_dev_store"]).exists()
    assert Path(acceptance["response_artifact_path"]).exists()
    response = json.loads(Path(acceptance["response_artifact_path"]).read_text(encoding="utf-8"))
    assert response["status"] == "prototype_live_success"
    assert response["sql_ref"] == plan["sql_ref"]
    assert output.exists()


def test_0218_rejects_non_local_qdrant_url(tmp_path: Path) -> None:
    module = _load_tool_module()
    plan = _plan_fixture(tmp_path, "https://example.com:6333")
    runtime = Path(plan["target_runtime_root"])
    runtime.mkdir(parents=True)
    plan_path = runtime / "prototype_live_execution_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    acceptance = module.execute_prototype_live_execution(live_execution_plan_path=plan_path)

    assert acceptance["prototype_success"] is False
    assert "qdrant_url must target localhost or 127.0.0.1" in acceptance["issues"]


def test_0218_rejects_unready_live_execution_plan(tmp_path: Path) -> None:
    module = _load_tool_module()
    plan = _plan_fixture(tmp_path, "http://127.0.0.1:6333", ready=False)
    runtime = Path(plan["target_runtime_root"])
    runtime.mkdir(parents=True)
    plan_path = runtime / "prototype_live_execution_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    acceptance = module.execute_prototype_live_execution(live_execution_plan_path=plan_path)

    assert acceptance["prototype_success"] is False
    assert "prototype_live_execution_plan_ready must be true" in acceptance["issues"]
    assert "p0218_may_execute_live_prototype must be true" in acceptance["issues"]
