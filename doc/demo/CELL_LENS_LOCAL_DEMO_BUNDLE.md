# Cell Lens Local Demo Bundle

```text
schema: missipy.cell_lens_local_demo_bundle.v1
```

This tool builds a local read-only demo bundle for the Cell Lens chain.

It does not start a server.

## Chain

```text
synthetic population
→ missipy.cell.v1 journal
→ replay check
→ SSE preview
→ report.json
```

## Files

```text
cells.jsonl
cells.sse
report.json
```

`cells.jsonl` is the same journal consumed by VisPy, replay/tail, the local SSE
endpoint, and the browser view.

`cells.sse` is an SSE preview file, not a live socket stream.

## Usage

```bash
PYTHONPATH=src:. python tools/cell_lens_local_demo_bundle.py \
  --output-dir .var/cell_lens_demo \
  --population-size 32 \
  --tick-count 20 \
  --seed 42 \
  --sse-limit 20
```

Then inspect:

```bash
head .var/cell_lens_demo/cells.jsonl
cat .var/cell_lens_demo/cells.sse
cat .var/cell_lens_demo/report.json
```

## Boundary

This is a demo artifact builder only. It does not command the system, does not
start a server, does not subscribe to a live source, and does not render.
