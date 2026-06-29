# PHASE 3.11 — Test report

## Scope

Phase 3.11 adds a local E5 ranking CLI before Qdrant.

## Commands executed

```bash
PYTHONPATH=src python3 -m compileall -q src tests tools
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
./tools/rank_e5.py --help
```

## Results

```text
compileall OK
153 passed, 1 skipped in 0.76s
main.py exit code: 0
DOT_OK
rank_e5.py --help OK
```

## Notes

The test suite remains portable: the new CLI tests use a fake pipeline and do not require OpenVINO, Transformers, or a local model.

The real local E5/OpenVINO validation remains optional and must be run on the user's machine with:

```bash
MISSIPY_RUN_OPENVINO_LOCAL=1 \
MISSIPY_E5_SMALL_DIR=/home/eric/model/openvino/multilingual-e5-small \
pytest -q tests/integration/test_openvino_e5_local.py
```

## Constraints

- No Scheduler change.
- No Qdrant.
- No new OpenVINO import site.
- No SVG generated or included.
- No patch script.
