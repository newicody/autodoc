# GitHub template script syntax gate — 0280

## Problem

The standard patch queue compiles `src` and `tests`, but standalone Python
scripts distributed under `templates/github/scripts/` are not part of that
compile target. A malformed newline literal in
`build_autodoc_ticket_artifact.py` therefore remained tracked while the normal
test suites stayed green.

## Repair

`write_json()` now appends the explicit string `"\n"` through a valid
multi-line `Path.write_text()` call. The JSON payload, key ordering and UTF-8
encoding contract remain unchanged.

## Permanent gate

The rule test recursively discovers every `*.py` file below
`templates/github/scripts/` and passes its source to Python's built-in
`compile()` function. It does not import or execute the scripts, so no CLI,
filesystem, network or GitHub effect is triggered.

The test aggregates syntax failures and reports their relative path, line,
column and message. Because it lives in `tests/rules`, the existing patch queue
gate executes it on every normal patch.

## Functional validation

A bounded subprocess test runs the repaired ticket builder with a local event
fixture and temporary output directory. It verifies that the two mandatory
artifacts are valid JSON, carry the expected schemas and end with exactly one
newline. The optional Copilot artifact remains absent when no preliminary
summary is supplied.

## Boundaries

- stdlib only;
- no Scheduler or `Scheduler.run()` change;
- no SQL or Qdrant access;
- no GitHub API or remote mutation;
- no change to ticket or bundle schema names;
- no generated artifact is committed.
