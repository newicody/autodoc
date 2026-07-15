from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = (
    ROOT
    / "tools/check_specialist_capability_growth_projects_readback_0286.py"
)


def _load_tool():
    spec = importlib.util.spec_from_file_location("readback_0286", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_graphql_guard_accepts_query() -> None:
    module = _load_tool()
    module._assert_query_only_graphql("query { viewer { login } }")


def test_graphql_guard_rejects_non_query() -> None:
    module = _load_tool()
    try:
        module._assert_query_only_graphql(
            "mutation { deleteProjectV2(input: {}) { clientMutationId } }"
        )
    except ValueError as exc:
        assert "query" in str(exc) or "mutation" in str(exc)
    else:
        raise AssertionError("mutation must be rejected")


def test_cli_is_live_query_only_when_execute_is_used() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert '"--method",' in text
    assert '"GET",' in text
    assert "_PROJECT_ITEM_READBACK_QUERY" in text
    assert "_assert_query_only_graphql" in text
    assert "updateProjectV2ItemFieldValue" not in text
    assert "/comments" in text
