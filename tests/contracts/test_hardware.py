from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from contracts.hardware import (
    HARDWARE_CELL_SCHEMA,
    HARDWARE_SAMPLE_SCHEMA,
    HardwareAvailability,
    HardwareCell,
    HardwareCollectionError,
    HardwareCollectionStatus,
    HardwareContractError,
    HardwareFreshness,
    HardwareMetric,
    HardwareMetricUnit,
    HardwarePhysicalSnapshot,
    HardwareResourceKind,
    HardwareSample,
    HardwareSchedulerSnapshot,
)


NOW = "2026-11-26T10:00:00Z"


def metric(resource_ref: str = "resource:cpu") -> HardwareMetric:
    return HardwareMetric(
        metric="cpu.utilization",
        resource_ref=resource_ref,
        value=42.5,
        unit=HardwareMetricUnit.PERCENT,
        source_ref="hardware-source:proc-stat",
    )


def test_hardware_sample_is_versioned_immutable_and_round_trips() -> None:
    sample = HardwareSample(
        sample_id="hardware-sample:host-a-1",
        host_ref="host:host-a",
        source_ref="hardware-source:linux-collector",
        observed_at=NOW,
        metrics=(metric(),),
        status=HardwareCollectionStatus.COMPLETE,
    )

    assert sample.schema == HARDWARE_SAMPLE_SCHEMA
    assert HardwareSample.from_mapping(sample.to_dict()) == sample
    with pytest.raises(FrozenInstanceError):
        sample.status = HardwareCollectionStatus.ERROR  # type: ignore[misc]


def test_partial_sample_requires_both_data_and_errors() -> None:
    error = HardwareCollectionError(
        source_ref="hardware-source:sysfs",
        error_type="PermissionDenied",
        message="temperature sensor is not readable",
    )
    sample = HardwareSample(
        sample_id="hardware-sample:host-a-2",
        host_ref="host:host-a",
        source_ref="hardware-source:linux-collector",
        observed_at=NOW,
        metrics=(metric(),),
        errors=(error,),
        status=HardwareCollectionStatus.PARTIAL,
    )
    assert sample.status is HardwareCollectionStatus.PARTIAL


@pytest.mark.parametrize(
    "status,metrics,errors",
    [
        (HardwareCollectionStatus.PARTIAL, (), ()),
        (HardwareCollectionStatus.PARTIAL, (metric(),), ()),
        (HardwareCollectionStatus.ERROR, (), ()),
        (HardwareCollectionStatus.UNAVAILABLE, (metric(),), ()),
    ],
)
def test_sample_rejects_inconsistent_collection_status(status, metrics, errors) -> None:
    with pytest.raises(HardwareContractError):
        HardwareSample(
            sample_id="hardware-sample:host-a-invalid",
            host_ref="host:host-a",
            source_ref="hardware-source:linux-collector",
            observed_at=NOW,
            metrics=metrics,
            errors=errors,
            status=status,
        )


def test_metric_rejects_invalid_percentage_and_boolean() -> None:
    with pytest.raises(HardwareContractError):
        HardwareMetric(
            metric="cpu.utilization",
            resource_ref="resource:cpu",
            value=101,
            unit=HardwareMetricUnit.PERCENT,
            source_ref="hardware-source:proc-stat",
        )
    with pytest.raises(HardwareContractError):
        HardwareMetric(
            metric="cpu.utilization",
            resource_ref="resource:cpu",
            value=True,
            unit=HardwareMetricUnit.PERCENT,
            source_ref="hardware-source:proc-stat",
        )


def test_scheduler_snapshot_keeps_unknown_distinct_from_zero() -> None:
    unknown = HardwareSchedulerSnapshot(availability=HardwareAvailability.UNKNOWN)
    zero = HardwareSchedulerSnapshot(
        availability=HardwareAvailability.UNAVAILABLE,
        capacity=0,
        reserved=0,
        available=0,
    )
    assert unknown.capacity is None
    assert zero.capacity == 0


def test_scheduler_snapshot_checks_reservation_arithmetic() -> None:
    with pytest.raises(HardwareContractError, match="available must equal"):
        HardwareSchedulerSnapshot(
            availability=HardwareAvailability.AVAILABLE,
            capacity=8,
            reserved=3,
            available=6,
        )


def test_hardware_cell_rejects_metrics_for_another_resource() -> None:
    with pytest.raises(HardwareContractError, match="must belong"):
        HardwareCell(
            cell_id="hardware-cell:host-a-cpu",
            host_ref="host:host-a",
            resource_ref="resource:memory",
            resource_kind=HardwareResourceKind.MEMORY,
            observed_at=NOW,
            freshness=HardwareFreshness.FRESH,
            physical=HardwarePhysicalSnapshot(
                availability=HardwareAvailability.AVAILABLE,
                metrics=(metric("resource:cpu"),),
            ),
            scheduler=HardwareSchedulerSnapshot(
                availability=HardwareAvailability.UNKNOWN,
            ),
            source_refs=("hardware-sample:host-a-1",),
        )


def test_hardware_cell_round_trips_and_preserves_separate_planes() -> None:
    cell = HardwareCell(
        cell_id="hardware-cell:host-a-cpu",
        host_ref="host:host-a",
        resource_ref="resource:cpu",
        resource_kind=HardwareResourceKind.CPU,
        observed_at=NOW,
        freshness=HardwareFreshness.FRESH,
        physical=HardwarePhysicalSnapshot(
            availability=HardwareAvailability.AVAILABLE,
            metrics=(metric(),),
        ),
        scheduler=HardwareSchedulerSnapshot(
            availability=HardwareAvailability.CONSTRAINED,
            capacity=8,
            reserved=6,
            available=2,
        ),
        source_refs=("hardware-sample:host-a-1", "scheduler-inventory:host-a"),
    )

    assert cell.schema == HARDWARE_CELL_SCHEMA
    restored = HardwareCell.from_mapping(cell.to_dict())
    assert restored == cell
    assert restored.physical.metrics[0].value == 42.5
    assert restored.scheduler.available == 2
