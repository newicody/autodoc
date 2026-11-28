# VisPy Cell Lens Viewer

The VisPy cell lens viewer is a desktop, observation-only renderer for the
`missipy.cell.v1` JSONL journal.

It is read-only.

It must not command the system.

## Input

```text
missipy.cell.v1 JSONL journal
```

The journal may come from:

```text
synthetic generator now
real observation recorder later
```

The viewer reads the same contract in both cases.

## Replay and tail

Replay mode reads existing journal lines.

Tail mode repeatedly reads new complete lines from a byte offset.

Live mode is replay that has caught up to the end of the journal and then keeps
tailing.

## Health

Health is derived by comparing age to the expected lifetime for the source
class.

```text
slow LLM answer within expected window: healthy
short task far beyond expected window: degraded or stale
```

Health is not a fitness function.

## Dependency boundary

VisPy is imported only by:

```text
tools/visualize_cell_population_vispy.py
```

Core contracts, journal writer, journal reader, Scheduler, and recorder code
must not import VisPy.

## Usage

Generate a synthetic journal:

```bash
PYTHONPATH=src:. python tools/generate_synthetic_cell_journal.py \
  --output /tmp/missipy_cells.jsonl \
  --population-size 64 \
  --tick-count 200 \
  --seed 42
```

Run the viewer after installing VisPy in the active environment:

```bash
PYTHONPATH=src:. python tools/visualize_cell_population_vispy.py \
  --journal /tmp/missipy_cells.jsonl
```

Follow a growing journal:

```bash
PYTHONPATH=src:. python tools/visualize_cell_population_vispy.py \
  --journal /tmp/missipy_cells.jsonl \
  --tail
```
