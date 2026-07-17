# 0287-r7-r15-r3-r1 — installed runtime factory composition

## Purpose

Select one canonical runtime factory for the r14/r15 imported Actions closed
loop and validate the existing Scheduler, SQL, OpenVINO/E5-384 and Qdrant ports
provided by the installed server composition.

The patch does **not** create a second Scheduler, a SQL backend, an OpenVINO
runtime, a Qdrant client or a laboratory manager. It has no dummy fallback.

## Dependency

Apply after:

- `0287-r7-r15-r2-r4-readable-copilot-publication-wiring`

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r1-installed-runtime-factory-composition \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r1-installed-runtime-factory-composition \
  --commit \
  --push \
  --allow-dirty
```

Suggested commit message:

```text
add canonical installed runtime factory composition
```

## One-time local configuration

After application:

```bash
mkdir -p .var/config

test -f .var/config/love_actions_closed_loop.ini || \
  cp config/love_actions_closed_loop.example.ini \
     .var/config/love_actions_closed_loop.ini

test -f .var/config/love_installed_runtime.ini || \
  cp config/love_installed_runtime.example.ini \
     .var/config/love_installed_runtime.ini
```

Configure `[provider] factory` in the second file with the installation-owned
composition function that returns the already-existing runtime ports. Do not
enter a fake placeholder: an empty, dummy, fake or stub provider fails closed.

## Validation performed while building the patch

- Python compilation: passed
- contract tests: 5 passed
- rule tests: 4 passed
- Graphviz DOT parsing: passed
- `git diff --check`: passed
- `git apply --check`: passed
- no `.pyc`, generated SVG or binary patch: verified

The global repository suite must still run through `apply_patch_queue.py` on the
real checkout.
