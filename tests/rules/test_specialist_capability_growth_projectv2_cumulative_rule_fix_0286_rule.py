from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "templates/github/projects-repository/projectv2_views.json"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
VIEWS_RULE = (
    ROOT
    / "tests/rules/test_projects_bundle_views_and_copilot_projection_0284_rule.py"
)
AUDIT_RULE = (
    ROOT
    / "tests/rules/"
    "test_specialist_capability_growth_projects_operator_workflow_reuse_audit_0286_rule.py"
)
REPORT = (
    ROOT
    / "PHASE0286_R4_R1_SPECIALIST_CAPABILITY_GROWTH_PROJECTV2_"
    "CUMULATIVE_RULE_FIX_REPORT.md"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTV2_CUMULATIVE_RULE_FIX_0286.md"
)
GRAPH = (
    ROOT
    / "doc/architecture/"
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTV2_CUMULATIVE_RULE_FIX_0286.dot"
)
CHANGELOG = (
    ROOT
    / "doc/CHANGELOG_0286_R4_R1_SPECIALIST_CAPABILITY_GROWTH_"
    "PROJECTV2_CUMULATIVE_RULE_FIX.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0286_R4_R1_SPECIALIST_CAPABILITY_GROWTH_"
    "PROJECTV2_CUMULATIVE_RULE_FIX.md"
)


def test_historical_view_rule_accepts_additive_views() -> None:
    text = VIEWS_RULE.read_text(encoding="utf-8")
    assert "organized_view_names.issubset(names)" in text
    assert "assert names ==" not in text


def test_historical_audit_rule_accepts_absent_or_complete_r4_surface() -> None:
    text = AUDIT_RULE.read_text(encoding="utf-8")
    assert "assert not present or present == specialist_fields" in text
    assert 'assert "Révision spécialiste" not in text' not in text
    assert 'assert "Décision capacité" not in text' not in text


def test_current_project_configuration_keeps_base_and_r4_surfaces() -> None:
    configuration = json.loads(CONFIG.read_text(encoding="utf-8"))
    view_names = {view["name"] for view in configuration["views"]}
    assert {
        "Recherches",
        "Résultats",
        "Copilot",
        "Connaissances serveur",
        "Boîtes de thèmes",
        "Historique",
        "Tous",
        "Révisions spécialistes",
    }.issubset(view_names)

    field_names = {field["name"] for field in configuration["fields"]}
    assert {
        "Spécialiste",
        "Révision spécialiste",
        "Capacité proposée",
        "Action capacité",
        "Décision capacité",
        "Statut révision",
        "Référence SQL",
        "Digest décision",
        "Laboratoire",
    }.issubset(field_names)


def test_installation_guide_remains_cumulative_without_bundle_change() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "0286-r4" in text
    assert "0286-r3" in text
    assert "0284-r9" in text
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in text
    assert "Ne pas utiliser `--delete`" in text


def test_systematic_deliverables_exist() -> None:
    for path in (REPORT, ARCHITECTURE, GRAPH, CHANGELOG, MANIFEST):
        assert path.is_file(), path
