from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_github_real_closed_loop_smoke_0281.py"


def _load_tool():
    # Stub runtime-only imports before loading the CLI.
    class AnyClass:
        def __init__(self, *args, **kwargs):
            pass

    modules = {
        "context.github_project_v2_source_candidate_vector_projection_0272": {
            "EmbeddingSpaceProfile": AnyClass,
        },
        "context.scheduler_laboratory_visit_binding_0274": {
            "register_laboratory_visit_handler": lambda dispatcher: None,
        },
        "context.scheduler_managed_embedding_qdrant_projection_usage_0262": {
            "DemoQdrantProjectionExecutor": AnyClass,
        },
        "context.scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263": {
            "DemoQdrantRecallExecutor": AnyClass,
        },
        "context.scheduler_managed_sql_ref_openvino_embedding_usage_0261": {
            "build_embedding_mapping": lambda **kwargs: kwargs,
        },
        "context.sql_context_store": {
            "SQLiteSqlContextStore": AnyClass,
        },
        "kernel.dispatcher": {"Dispatcher": AnyClass},
        "kernel.event_bus": {"EventBus": AnyClass},
        "kernel.queue": {"PriorityQueue": AnyClass},
        "kernel.registry": {"Registry": AnyClass},
        "kernel.scheduler": {"Scheduler": AnyClass},
    }
    from types import ModuleType

    for name, attributes in modules.items():
        module = ModuleType(name)
        for key, value in attributes.items():
            setattr(module, key, value)
        sys.modules[name] = module

    spec = spec_from_file_location("real_smoke_tool_0281", TOOL)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_write_outputs_creates_then_replays(tmp_path: Path) -> None:
    tool = _load_tool()
    result = {
        "assembly": {"valid": True},
        "laboratory_projection": {"valid": True},
        "publication_preview": {"summary": "ok"},
        "publication_plan": {"action": "create"},
    }

    first = tool._write_outputs(tmp_path, result)
    second = tool._write_outputs(tmp_path, result)

    assert set(first.values()) == {"created"}
    assert set(second.values()) == {"replayed"}
    assert json.loads(
        (tmp_path / "publication_preview.json").read_text(
            encoding="utf-8"
        )
    ) == {"summary": "ok"}


def test_writer_refuses_different_existing_proof(tmp_path: Path) -> None:
    tool = _load_tool()
    path = tmp_path / "proof.json"

    assert tool._write_json_idempotent(path, {"value": 1}) == "created"
    try:
        tool._write_json_idempotent(path, {"value": 2})
    except RuntimeError as exc:
        assert "refusing to overwrite" in str(exc)
    else:
        raise AssertionError("different proof must collide")
