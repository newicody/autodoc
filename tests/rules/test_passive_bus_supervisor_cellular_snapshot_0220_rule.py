from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_0220_source_is_passive_stdlib_only_and_has_no_runtime_authority() -> None:
    source = _read("src/context/passive_bus_supervisor_cellular_snapshot.py")
    tool = _read("tools/run_passive_bus_supervisor_cellular_snapshot_0220.py")
    combined = source + "\n" + tool

    forbidden_imports = [
        "requests",
        "httpx",
        "github",
        "qdrant",
        "sqlite3",
        "psycopg",
        "vispy",
        "openvino",
    ]
    for forbidden in forbidden_imports:
        assert f"import {forbidden}" not in combined
        assert f"from {forbidden}" not in combined

    forbidden_calls = [
        "Scheduler.run(",
        "run_scheduler(",
        "upsert(",
        "execute(",
        "mutate(",
        "download_artifact(",
        "pushback(",
    ]
    for forbidden in forbidden_calls:
        assert forbidden not in combined

    assert '"observation_only": True' in source
    assert '"allows_scheduler_run": False' in source
    assert '"allows_sql_write": False' in source
    assert '"allows_qdrant_write": False' in source
    assert '"allows_github_mutation": False' in source
    assert '"allows_proxy_control": False' in source


def test_0220_traceability_docs_are_present() -> None:
    required_paths = [
        "doc/architecture/PASSIVE_BUS_SUPERVISOR_CELLULAR_SNAPSHOT_0220.md",
        "doc/code-rules/0220_passive_bus_supervisor_cellular_snapshot_rule.md",
        "doc/docs/architecture/runtime/220_passive_bus_supervisor_cellular_snapshot.dot",
        "doc/CHANGELOG_0220_PASSIVE_BUS_SUPERVISOR_CELLULAR_SNAPSHOT.md",
        "doc/manifests/MANIFEST_0220_CHANGED_FILES.md",
        "PHASE0220_TEST_REPORT.md",
    ]
    for relative_path in required_paths:
        assert (ROOT / relative_path).exists(), relative_path


def test_0220_changelog_and_rule_keep_vispy_as_optional_view_only() -> None:
    changelog = _read("doc/CHANGELOG_0220_PASSIVE_BUS_SUPERVISOR_CELLULAR_SNAPSHOT.md")
    rule = _read("doc/code-rules/0220_passive_bus_supervisor_cellular_snapshot_rule.md")

    assert "VisPy is not introduced by this patch" in changelog
    assert "view adapter only" in rule
    assert "observation-only" in rule
    assert "must not call Scheduler.run" in rule
