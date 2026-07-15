# Copilot first-opinion advisory v2 — 0287-r7-r2

## Purpose

Version the public advisory meaning instead of placing new mandatory semantics
inside `missipy.github.copilot_advisory.v1`.

## Producer flow

```text
GitHub Issue title/body/labels
-> authoritative request artifact
-> existing optional Copilot CLI runner
-> exact four-field response validation
-> missipy.github.copilot_advisory.v2
-> correlated dual-artifact manifest
```

The analytical payload is:

```json
{
  "concrete_objective": "...",
  "expected_result": "...",
  "provided_constraints": ["..."],
  "success_criteria": ["..."]
}
```

Provenance fields are added by the runner after validation. They do not extend
the analytical contract.

## Compatibility boundary

The historical `extract_advisory()` v1 helper remains unchanged. New production
uses `extract_first_opinion()` and writes v2 only. Durable consumers must be
migrated explicitly in the next patch to accept both historical v1 and active
v2 artifacts.

## Authority boundary

The runner denies read, write, shell, URL and memory tools. The generated
artifact is an untrusted hint. It cannot select a development route, make an
operator decision or authorize a remote mutation.

## Operational destination

No product-specific integrator follows this work. The destination is a generic,
fully tested closed loop from Issue intake through controlled readback and
replay.
