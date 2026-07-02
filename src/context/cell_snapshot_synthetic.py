from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import random
from typing import Iterator

from context.cell_snapshot import CellSnapshot


CELL_SYNTHETIC_POPULATION_SCHEMA = "missipy.cell_synthetic_population.v1"


@dataclass(frozen=True, slots=True)
class SyntheticCellClassProfile:
    """Expected behavior profile for synthetic cell generation."""

    source_class: str
    expected_lifetime: float
    base_cost: float
    score_bias: float

    def __post_init__(self) -> None:
        if not self.source_class:
            raise ValueError("source_class must be non-empty")
        if self.expected_lifetime <= 0:
            raise ValueError("expected_lifetime must be > 0")
        if self.base_cost < 0:
            raise ValueError("base_cost must be >= 0")


DEFAULT_SYNTHETIC_CELL_PROFILES = (
    SyntheticCellClassProfile(
        source_class="scheduler.short_task",
        expected_lifetime=2.0,
        base_cost=1.0,
        score_bias=0.90,
    ),
    SyntheticCellClassProfile(
        source_class="llm.answer",
        expected_lifetime=45.0,
        base_cost=12.0,
        score_bias=0.70,
    ),
    SyntheticCellClassProfile(
        source_class="ingest.batch",
        expected_lifetime=120.0,
        base_cost=30.0,
        score_bias=0.80,
    ),
    SyntheticCellClassProfile(
        source_class="recorder.write",
        expected_lifetime=5.0,
        base_cost=2.0,
        score_bias=0.95,
    ),
)


@dataclass(frozen=True, slots=True)
class SyntheticCellPopulationConfig:
    """Deterministic configuration for synthetic cell snapshot production."""

    population_size: int = 32
    tick_count: int = 10
    tick_seconds: float = 1.0
    seed: int = 42
    base_observed_at: str = "2026-07-03T10:00:00Z"
    profiles: tuple[SyntheticCellClassProfile, ...] = DEFAULT_SYNTHETIC_CELL_PROFILES
    schema: str = CELL_SYNTHETIC_POPULATION_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != CELL_SYNTHETIC_POPULATION_SCHEMA:
            raise ValueError(f"unsupported synthetic population schema: {self.schema!r}")
        if self.population_size <= 0:
            raise ValueError("population_size must be > 0")
        if self.tick_count < 0:
            raise ValueError("tick_count must be >= 0")
        if self.tick_seconds <= 0:
            raise ValueError("tick_seconds must be > 0")
        if not self.profiles:
            raise ValueError("profiles must not be empty")


@dataclass(frozen=True, slots=True)
class SyntheticCellSeed:
    """Stable synthetic cell identity and behavior seed."""

    cell_id: str
    source_task_id: str
    source_component_id: str
    profile: SyntheticCellClassProfile
    birth_tick: int
    lifetime_factor: float
    cost_factor: float
    score_noise: float


def build_synthetic_cell_seeds(config: SyntheticCellPopulationConfig) -> tuple[SyntheticCellSeed, ...]:
    rng = random.Random(config.seed)
    seeds: list[SyntheticCellSeed] = []

    for index in range(config.population_size):
        profile = config.profiles[index % len(config.profiles)]
        birth_tick = rng.randint(0, max(config.tick_count, 1))
        lifetime_factor = rng.uniform(0.65, 1.65)
        cost_factor = rng.uniform(0.75, 1.75)
        score_noise = rng.uniform(-0.12, 0.12)

        seeds.append(
            SyntheticCellSeed(
                cell_id=f"synthetic-cell-{index:04d}",
                source_task_id=f"synthetic-task-{index:04d}",
                source_component_id=f"synthetic-component-{index % len(config.profiles):02d}",
                profile=profile,
                birth_tick=birth_tick,
                lifetime_factor=lifetime_factor,
                cost_factor=cost_factor,
                score_noise=score_noise,
            )
        )

    return tuple(seeds)


def generate_synthetic_cell_snapshots(config: SyntheticCellPopulationConfig) -> Iterator[CellSnapshot]:
    """Generate deterministic synthetic cell snapshots.

    The generator emits the same `missipy.cell.v1` contract that the real
    observation recorder consumer will later emit. It is therefore useful for
    developing replay readers and visualization without connecting to the live system.
    """

    base_time = _parse_utc_timestamp(config.base_observed_at)
    seeds = build_synthetic_cell_seeds(config)

    for tick in range(config.tick_count):
        observed_at = _format_utc_timestamp(base_time + timedelta(seconds=tick * config.tick_seconds))

        for seed in seeds:
            if tick < seed.birth_tick:
                continue

            age = (tick - seed.birth_tick) * config.tick_seconds
            expected_lifetime = seed.profile.expected_lifetime * seed.lifetime_factor
            state = _synthetic_lifecycle_state(age=age, expected_lifetime=expected_lifetime)
            score = _clamp(seed.profile.score_bias + seed.score_noise - _health_penalty(age, expected_lifetime), 0.0, 1.0)
            cost = seed.profile.base_cost * seed.cost_factor * (1.0 + age / expected_lifetime)

            yield CellSnapshot(
                cell_id=seed.cell_id,
                source_task_id=seed.source_task_id,
                source_component_id=seed.source_component_id,
                source_class=seed.profile.source_class,
                score=round(score, 6),
                age=round(age, 6),
                cost=round(cost, 6),
                lifecycle_state=state,
                observed_at=observed_at,
            )


def _synthetic_lifecycle_state(*, age: float, expected_lifetime: float) -> str:
    ratio = age / expected_lifetime
    if age == 0:
        return "created"
    if ratio < 0.15:
        return "queued"
    if ratio < 0.75:
        return "running"
    if ratio < 1.00:
        return "waiting"
    if ratio < 1.35:
        return "completed"
    return "dropped"


def _health_penalty(age: float, expected_lifetime: float) -> float:
    ratio = age / expected_lifetime
    if ratio <= 1.0:
        return 0.0
    return min(0.50, (ratio - 1.0) * 0.35)


def _parse_utc_timestamp(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError("base_observed_at must be a UTC timestamp ending with Z")
    parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    return parsed.astimezone(timezone.utc)


def _format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
