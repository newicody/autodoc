# 0273-r2 — Laboratory framework contract

This release adds `missipy.laboratory.v1` contracts only.

The first laboratory provider remains inactive. The binding plan targets the
existing Scheduler-owned runtime registry and refuses parallel authorities.
Every visit carries an explicit resource budget and returns an immutable,
JSON-compatible result.

0273-r3 will add the deterministic fake provider behind the existing Handler
and registry boundaries.
