import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_production_prototype_smoke_composition_0269.py"


def _load_tool_module():
    spec = importlib.util.spec_from_file_location("production_prototype_cli_0269_r6", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_report_loader_preserves_sql_authority_reference(tmp_path: Path) -> None:
    module = _load_tool_module()
    report = tmp_path / "projection.json"
    report.write_text(
        json.dumps(
            {
                "valid": True,
                "result": {
                    "sql_authority_ref": "sql-authority:sqlite:test",
                    "qdrant_projection_live": True,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    valid, references, checks = module._load_report(report)

    assert valid is True
    assert dict(references)["sql_authority_ref"] == "sql-authority:sqlite:test"
    assert dict(checks)["qdrant_projection_live"] is True


def test_summary_surfaces_common_sql_authority_reference() -> None:
    module = _load_tool_module()
    summary = module._summary(
        {
            "valid": True,
            "issues": [],
            "execute": True,
            "qdrant_mode": "live",
            "valid_step_count": 9,
            "planned_step_count": 9,
            "references": {
                "sql_ref": "sql:inference_context:test",
                "sql_authority_ref": "sql-authority:sqlite:test",
                "embedding_ref": "embedding:passage:test",
                "handoff_ref": "github-scan-once-handoff:test",
                "readiness_ref": "openrc-launcher-readiness:test",
            },
            "checks": {"remote_mutation_allowed": False},
            "boundaries": {"scheduler_starts_external_services": False},
        }
    )

    assert "sql_authority_ref=sql-authority:sqlite:test" in summary
    assert "steps=9/9" in summary
