from context.specialist_capability_growth_reuse_audit_0285 import (
    CAPABILITY_GROWTH_PHASES,
    REQUIRED_REUSE_SURFACES,
    audit_specialist_capability_growth_reuse,
)


def _required_sources() -> dict[str, str]:
    sources: dict[str, str] = {}
    for surface in REQUIRED_REUSE_SURFACES:
        lines = ["# synthetic source"]
        for marker in surface.markers:
            if marker.startswith("class "):
                lines.append(f"{marker}:\n    pass")
            else:
                lines.append(f"{marker} = True")
        sources[surface.path] = "\n".join(lines) + "\n"
    return sources


def _add_classes(sources: dict[str, str], *names: str) -> None:
    sources["src/context/future_capability_growth_0285.py"] = "\n".join(
        f"class {name}:\n    pass" for name in names
    )


def test_reuse_audit_is_valid_and_starts_with_proposal_contract() -> None:
    result = audit_specialist_capability_growth_reuse(_required_sources())

    assert result.valid is True
    assert result.issues == ()
    assert result.completed_patch_ids == ()
    assert result.next_recommended_patch == (
        "0285-r2-specialist-capability-growth-proposal-contract"
    )
    mapping = result.to_mapping()
    assert mapping["existing_scheduler_remains_only_orchestrator"] is True
    assert mapping["specialist_self_authorization_allowed"] is False
    assert mapping["new_global_specialist_registry_added"] is False


def test_completed_phases_advance_in_declared_order() -> None:
    sources = _required_sources()
    first = CAPABILITY_GROWTH_PHASES[0]
    _add_classes(sources, *first.required_classes)

    result = audit_specialist_capability_growth_reuse(sources)

    assert result.valid is True
    assert result.completed_patch_ids == (first.patch_id,)
    assert result.next_recommended_patch == CAPABILITY_GROWTH_PHASES[1].patch_id


def test_audit_reports_complete_when_all_planned_surfaces_exist() -> None:
    sources = _required_sources()
    _add_classes(
        sources,
        *(name for phase in CAPABILITY_GROWTH_PHASES for name in phase.required_classes),
    )

    result = audit_specialist_capability_growth_reuse(sources)

    assert result.valid is True
    assert result.completed_patch_ids == tuple(
        phase.patch_id for phase in CAPABILITY_GROWTH_PHASES
    )
    assert result.next_recommended_patch == "0285-complete"


def test_missing_existing_surface_invalidates_the_reuse_audit() -> None:
    sources = _required_sources()
    missing = REQUIRED_REUSE_SURFACES[0].path
    del sources[missing]

    result = audit_specialist_capability_growth_reuse(sources)

    assert result.valid is False
    assert f"missing required reuse surface: {missing}" in result.issues


def test_missing_stable_marker_is_reported_without_importing_sources() -> None:
    sources = _required_sources()
    path = "src/context/portable_specialist_contract_0284.py"
    sources[path] = sources[path].replace("specialist_version = True\n", "")

    result = audit_specialist_capability_growth_reuse(sources)

    assert result.valid is False
    assert any("specialist_version" in issue for issue in result.issues)


def test_source_digest_is_deterministic_and_order_independent() -> None:
    sources = _required_sources()
    reversed_sources = dict(reversed(tuple(sources.items())))

    first = audit_specialist_capability_growth_reuse(sources)
    second = audit_specialist_capability_growth_reuse(reversed_sources)

    assert first.source_digest == second.source_digest
    assert first.to_mapping() == second.to_mapping()


def test_syntax_error_in_additional_future_source_does_not_execute_it() -> None:
    sources = _required_sources()
    sources["src/context/broken_future_capability_growth_0285.py"] = "raise SystemExit(9\n"

    result = audit_specialist_capability_growth_reuse(sources)

    assert result.valid is True
    assert result.next_recommended_patch == CAPABILITY_GROWTH_PHASES[0].patch_id
