# Phase 0156 test report — surface status inventory

## Intended commands

```bash
env -u AUTODOC_SQL_CONTEXT_DB PYTHONPATH=src:. pytest -q tests/docs/test_dot_links.py
while IFS= read -r f; do dot -Tsvg "$f" -o /tmp/dotcheck.svg; done < <(find doc/docs/architecture -name '*.dot' | sort)
env -u AUTODOC_SQL_CONTEXT_DB PYTHONPATH=src:. pytest -q tests/rules
env -u AUTODOC_SQL_CONTEXT_DB PYTHONPATH=src:. pytest -q
```

## Expected result

The previous local run showed docs DOT links passing and full tests failing only
because generated `.svg` files existed under `doc/docs/architecture/context/`.
`apply_patch_queue.py` cleans untracked generated `.svg` files before tests.

## Boundary

0156 is documentation, DOT status inventory, and generated artifact hygiene only.
No runtime Python surface is created.
