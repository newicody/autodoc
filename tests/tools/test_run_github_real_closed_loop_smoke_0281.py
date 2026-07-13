from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_github_real_closed_loop_smoke_0281.py"


def _load_tool():
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
        "context.sql_context_store": {"SQLiteSqlContextStore": AnyClass},
        "kernel.dispatcher": {"Dispatcher": AnyClass},
        "kernel.event_bus": {"EventBus": AnyClass},
        "kernel.queue": {"PriorityQueue": AnyClass},
        "kernel.registry": {"Registry": AnyClass},
        "kernel.scheduler": {"Scheduler": AnyClass},
    }
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


def test_cli_requires_config_and_has_no_manual_paths() -> None:
    tool = _load_tool()
    args = tool.parse_args(
        (
            "--config", "/tmp/fetch.ini",
            "--run-id", "42",
            "--issue-number", "15",
        )
    )
    assert str(args.config) == "/tmp/fetch.ini"
    assert not hasattr(args, "run_root")
    assert not hasattr(args, "output_root")
    assert not hasattr(args, "repository")


def test_write_outputs_creates_then_replays(tmp_path: Path) -> None:
    tool = _load_tool()
    result = {
        "assembly": {"valid": True},
        "laboratory_projection": {"valid": True},
        "publication_preview": {"summary": "ok"},
        "publication_plan": {"action": "create"},
    }
    assert set(tool._write_outputs(tmp_path, result).values()) == {"created"}
    assert set(tool._write_outputs(tmp_path, result).values()) == {"replayed"}
    assert json.loads(
        (tmp_path / "publication_preview.json").read_text(encoding="utf-8")
    ) == {"summary": "ok"}
