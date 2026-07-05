from __future__ import annotations

import pytest

from runtime.controlproxy_compatibility_wrappers import (
    CONTROLPROXY_COMPATIBILITY_WRAPPERS_SCHEMA,
    ControlProxyCompatibilityWrapperError,
    controlproxy_compatibility_wrapper_map,
    list_controlproxy_compatibility_wrappers,
    require_controlproxy_compatibility_wrapper,
)


def test_registry_marks_0085_and_0086_as_compatibility_wrappers() -> None:
    wrappers = list_controlproxy_compatibility_wrappers()
    symbols = {wrapper.legacy_symbol for wrapper in wrappers}

    assert symbols == {"prepare_route_for_scheduler", "handle_scheduler_route_request"}
    for wrapper in wrappers:
        assert wrapper.schema == CONTROLPROXY_COMPATIBILITY_WRAPPERS_SCHEMA
        assert wrapper.current_boundary == "compatibility_wrapper"
        assert wrapper.replacement_boundary == "Handler -> RouteRuntimeManager"
        assert wrapper.status == "do_not_extend"
        assert wrapper.replacement_module == "runtime.controlproxy_route_runtime_handler"


def test_registry_mapping_is_stable_and_read_only() -> None:
    registry = controlproxy_compatibility_wrapper_map()

    assert registry["prepare_route_for_scheduler"]["replacement_symbol"] == (
        "build_controlproxy_route_runtime_request_handler"
    )
    assert registry["handle_scheduler_route_request"]["replacement_symbol"] == (
        "handle_controlproxy_route_runtime_request"
    )
    with pytest.raises(TypeError):
        registry["new"] = {}  # type: ignore[index]


def test_require_controlproxy_compatibility_wrapper_reports_unknown_symbol() -> None:
    wrapper = require_controlproxy_compatibility_wrapper("handle_scheduler_route_request")

    assert wrapper.legacy_symbol == "handle_scheduler_route_request"
    assert "0104 thin handler binding" in wrapper.reason
    with pytest.raises(ControlProxyCompatibilityWrapperError, match="unknown ControlProxy"):
        require_controlproxy_compatibility_wrapper("not_a_controlproxy_wrapper")
