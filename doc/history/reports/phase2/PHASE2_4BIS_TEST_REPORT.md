# Phase 2.4bis — Test report

## Commands

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc/docs/architecture
for f in $(find . -name '*.dot' | sort); do dot -Tsvg "$f" -o /tmp/dot_test.svg; done
```

## Results

```text
55 passed in 0.54s
main.py exit code: 0
DOT_OK
```

## Scope

This phase corrects the DOT navigation test and roadmap links only.
It does not change the scheduler, inference, replay, or runtime code.
