# Phase 3.2 — Test report

## Scope

Ajout d'un profil embedding OpenVINO configurable sans modèle local imposé, sans
tokenizer, sans post-processing réel et sans modification Scheduler.

## Validation commands

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Results

```text
compileall OK
91 passed in 1.00s
main.py exit code: 0
DOT_OK
```

Graphviz warnings about orthogonal edge labels were observed and are unchanged
from previous phases. They do not indicate invalid DOT sources.

## Rule checks

The existing rule audit still passes:

- no unapproved external import;
- no OpenVINO import outside `src/inference/openvino_runtime.py`;
- Scheduler has no domain/backend imports;
- contract dataclasses remain frozen.

## Notes

The new embedding profile configuration does not verify the model path exists.
This is intentional: the repository must remain independent from the user's
local model directory.
