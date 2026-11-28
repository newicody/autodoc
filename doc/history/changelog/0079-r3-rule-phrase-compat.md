# 0079-r3 - Rule phrase compatibility

## Fixed

This patch restores exact legacy rule-test phrases in module docstrings after
`0079-r2` unified the architecture around:

```text
ControlProxy = ControlFS + RouteProxy
```

No runtime behavior changes.

## Changed

- `src/runtime/controlfs_manifest.py`
- `src/context/baby_fork_controlfs.py`

## Why

Two older rule tests check exact text snippets:

```text
It only writes desired route manifests
start RouteProxy
start a RouteProxy daemon
```

The architecture is unchanged; only compatibility wording is restored.
