# Phase 3.1 — Test report

## Scope

Phase 3.1 adds a controlled factory for building executable OpenVINO backends from declarative profiles.

No Scheduler, Dispatcher, ComponentProxy, PolicyEngine or runtime command path change was introduced.

## Commands

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
find doc/docs/architecture -name '*.dot' | sort | xargs -I{} dot -Tsvg {} -o /tmp/...
```

## Results

```text
compileall OK
84 passed in 0.88s
main.py exit code: 0
DOT_OK
```

## Notes

- `OpenVINOBackendFactory` imports no `openvino` module.
- Runtime creation stays injected through `OpenVINORuntimeFactory`.
- `OpenVINOModelProfileRegistry` remains declarative.
- `BackendRegistry` remains the executable backend inventory.
- No tokenizer, Qdrant integration, or model-specific post-processing was added.
