from __future__ import annotations

from context.cell_snapshot import CELL_SNAPSHOT_SCHEMA, CellSnapshot
from context.cell_snapshot_synthetic import (
    CELL_SYNTHETIC_POPULATION_SCHEMA,
    SyntheticCellPopulationConfig,
    build_synthetic_cell_seeds,
    generate_synthetic_cell_snapshots,
)


def test_synthetic_population_config_declares_versioned_schema() -> None:
    config = SyntheticCellPopulationConfig(population_size=4, tick_count=3)

    assert config.schema == CELL_SYNTHETIC_POPULATION_SCHEMA
    assert config.schema == "missipy.cell_synthetic_population.v1"


def test_synthetic_population_generation_is_deterministic() -> None:
    config = SyntheticCellPopulationConfig(population_size=8, tick_count=4, seed=123)

    first = tuple(generate_synthetic_cell_snapshots(config))
    second = tuple(generate_synthetic_cell_snapshots(config))

    assert first == second


def test_synthetic_population_outputs_cell_snapshot_contract() -> None:
    config = SyntheticCellPopulationConfig(population_size=4, tick_count=4, seed=7)

    snapshots = tuple(generate_synthetic_cell_snapshots(config))

    assert snapshots
    assert all(isinstance(snapshot, CellSnapshot) for snapshot in snapshots)
    assert {snapshot.schema for snapshot in snapshots} == {CELL_SNAPSHOT_SCHEMA}


def test_synthetic_population_uses_expected_lifetime_classes() -> None:
    config = SyntheticCellPopulationConfig(population_size=8, tick_count=8, seed=3)
    snapshots = tuple(generate_synthetic_cell_snapshots(config))

    source_classes = {snapshot.source_class for snapshot in snapshots}

    assert "scheduler.short_task" in source_classes
    assert "llm.answer" in source_classes
    assert "ingest.batch" in source_classes
    assert "recorder.write" in source_classes


def test_synthetic_population_seeds_are_stable() -> None:
    config = SyntheticCellPopulationConfig(population_size=5, tick_count=5, seed=99)

    seeds = build_synthetic_cell_seeds(config)

    assert [seed.cell_id for seed in seeds] == [
        "synthetic-cell-0000",
        "synthetic-cell-0001",
        "synthetic-cell-0002",
        "synthetic-cell-0003",
        "synthetic-cell-0004",
    ]


def test_synthetic_population_age_and_cost_are_non_negative() -> None:
    config = SyntheticCellPopulationConfig(population_size=16, tick_count=10, seed=12)

    snapshots = tuple(generate_synthetic_cell_snapshots(config))

    assert all(snapshot.age >= 0 for snapshot in snapshots)
    assert all(snapshot.cost >= 0 for snapshot in snapshots)
    assert all(0 <= snapshot.score <= 1 for snapshot in snapshots)
