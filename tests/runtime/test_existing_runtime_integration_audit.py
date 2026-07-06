from __future__ import annotations

from pathlib import Path

from tools.audit_existing_runtime_integration import audit_existing_runtime_integration


def test_audit_detects_existing_runtime_surfaces(tmp_path: Path) -> None:
    (tmp_path / "src" / "runtime").mkdir(parents=True)
    (tmp_path / "src" / "runtime" / "route_proxy_runtime_minimal.py").write_text("class RouteProxyRuntime: pass\n", encoding="utf-8")
    (tmp_path / "src" / "kernel").mkdir(parents=True)
    (tmp_path / "src" / "kernel" / "scheduler.py").write_text("class Scheduler:\n    def run(self): pass\n", encoding="utf-8")
    (tmp_path / "doc" / "code-rules").mkdir(parents=True)
    (tmp_path / "doc" / "code-rules" / "code_rule.md").write_text("Do not mutate Scheduler.run.\n", encoding="utf-8")

    audit = audit_existing_runtime_integration(tmp_path)
    data = audit.to_mapping()

    assert data["new_module_default_allowed"] is False
    assert data["scheduler_run_mutation_allowed"] is False
    assert data["category_counts"]["route_runtime"] >= 1
    assert data["category_counts"]["scheduler"] >= 1
    assert data["category_counts"]["code_rules"] >= 1
    scheduler_decision = [decision for decision in audit.decisions if decision.category == "scheduler"][0]
    assert scheduler_decision.decision == "reuse_or_extend_existing"


def test_audit_marks_missing_surfaces_as_create_only_after_documented_gap(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("empty project\n", encoding="utf-8")
    audit = audit_existing_runtime_integration(tmp_path)
    missing = [decision for decision in audit.decisions if decision.category == "openvino_adapter"][0]
    assert missing.decision == "create_only_after_documented_gap"
    assert "documented no-reinvent justification" in missing.reason


def test_audit_markdown_contains_decisions(tmp_path: Path) -> None:
    (tmp_path / "src" / "inference").mkdir(parents=True)
    (tmp_path / "src" / "inference" / "openvino_embedding_adapter.py").write_text("OpenVINO EmbeddingAdapter\n", encoding="utf-8")
    audit = audit_existing_runtime_integration(tmp_path)
    markdown = audit.to_markdown()
    assert "Existing runtime integration audit" in markdown
    assert "openvino_adapter" in markdown
    assert "reuse_or_extend_existing" in markdown
