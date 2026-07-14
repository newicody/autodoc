from context.specialists_laboratories_reuse_audit_0284 import inspect_specialists_laboratories_reuse

def test_reuse_audit_selects_existing_chain():
    result = inspect_specialists_laboratories_reuse()
    assert result.valid is True
    assert len(result.surfaces) == 7
    assert all(surface.reuse for surface in result.surfaces)
    decisions = dict(result.decisions)
    assert decisions["scheduler_remains_only_orchestrator"] is True
    assert decisions["new_laboratory_manager_allowed"] is False
    assert decisions["new_scheduler_allowed"] is False
    assert decisions["new_parallel_queue_allowed"] is False
    assert decisions["new_parallel_bus_allowed"] is False

def test_audit_mapping_is_stable():
    payload = inspect_specialists_laboratories_reuse().to_mapping()
    assert payload["schema"] == "missipy.specialists_laboratories.reuse_audit.v1"
    refs = {item["ref"] for item in payload["surfaces"]}
    assert {"laboratory-contract-0273", "scheduler-smoke-0274", "dual-artifact-smoke-0275"} <= refs
