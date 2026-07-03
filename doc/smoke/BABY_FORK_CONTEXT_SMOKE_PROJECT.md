# Baby Fork Context Smoke Project

```text
schema: missipy.baby_fork_smoke_project.v1
```

This smoke project moves ahead of the generalized seven-vector-space plan.

Goal:

```text
prove retrieval replaces calculation for this single domain first
```

## Flow

```text
TaskContext
→ one RetrievalWorker
→ two VariantGeneratorStub variants
→ ContextGate
→ missipy.cell.v1 journal
→ cell-lens
```

The cell-lens is fed by this real flow, not the synthetic generator.

## Domain

```text
project: baby fork
domain: baby_utensil
food_contact: true
age_target: baby
```

The retrieval worker must reject off-domain documents such as an aerospace antenna.

## Retrieval

The first implementation uses stand-in stdlib retrieval.

It exists to prove the architecture before adding qdrant_core.

The future replacement is:

```text
stand-in stdlib retrieval
→ qdrant_core retrieval
```

Only after this smoke stays useful should the project generalize toward multiple vector spaces.

## VariantGeneratorStub

This is not the real MVTC.

The VariantGeneratorStub produces exactly two context variants:

```text
soft silicone baby fork
rounded stainless fork with soft baby handle
```

The stub does not command the Scheduler.

It proposes a context patch.

The future MVTC will replace this stub with real context variation, scoring, comparison, and reduction.

## ContextGate

The ContextGate accepts the patch only if the baby-utensil domain remains stable.

## Manual run

```bash
PYTHONPATH=src:. python tools/run_baby_fork_smoke_project.py \
  --output-dir .var/baby_fork_smoke
```

Then view:

```bash
VISPY_APP=pyqt6 QT_QPA_PLATFORM=wayland PYTHONPATH=src:. python tools/visualize_cell_population_vispy.py \
  --journal .var/baby_fork_smoke/baby_fork_cells.jsonl
```
