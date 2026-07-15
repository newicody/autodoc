# Phase 0287-r7-r2 — Copilot first-opinion advisory v2

## Status

Implemented as a narrow versioned correction of the existing optional Copilot
runner. The rejected `first_opinion`-inside-v1 design is not part of this patch.

## Reuse audit

Reused:

- `templates/github/scripts/run_autodoc_copilot_advisory.py`;
- its existing CLI invocation, tool-denial flags and unavailable-result path;
- its historical v1 parser for migration compatibility;
- the existing artifact filename and correlation/provenance metadata;
- the cumulative `newicody/projects` source bundle.

Not added:

- no second Copilot runner;
- no prompt manager, agent framework, provider registry or new queue;
- no Scheduler, laboratory or backend change;
- no direct GitHub or ProjectV2 mutation;
- no external Python dependency.

## Public versioning decision

`missipy.github.copilot_advisory.v1` is not extended or reinterpreted. New runs
produce `missipy.github.copilot_advisory.v2` with exactly four analytical fields:

- `concrete_objective`;
- `expected_result`;
- `provided_constraints`;
- `success_criteria`.

The v1 parser remains in place only so migration tests and later consumers can
continue to read historical artifacts. The active producer uses the new v2
parser and emits no v1 analysis fields.

## Validation

The v2 response parser:

- accepts a direct JSON object, a fenced object or an object embedded in Copilot
  JSON event output;
- requires the exact four-field set and rejects extra fields;
- requires non-empty objective and expected result;
- accepts an empty supplied-constraints array;
- requires at least one observable success criterion;
- trims every accepted string;
- fails closed without leaving an advisory artifact.

The deterministic execution test replaces only the external Copilot process. It
proves prompt wiring, response extraction, digesting and final artifact writing.
It is not evidence of the deployed GitHub Actions or real Copilot service.

## Roadmap correction

The product-specific Chalouf phase is removed. The locked roadmap now ends with
generic end-to-end operational closure: consumer migration, preview bridge,
full local smoke, controlled publication/readback, real Actions evidence,
negative-path/recovery matrix and installation closure.

## Projects installation review

`templates/github/projects-repository/INSTALLATION.md` is aligned to
`0287-r7-r2` and links `COPILOT_ADVISORY_V2.md`. Preview-first synchronization,
`git diff`, no `rsync --delete`, disabled-by-default Copilot and secret hygiene
remain unchanged.

## Code-rule review

code_rule_review: done
code_rule_update_required: false
code_rule_reason: the existing rule already requires a new version when a public
meaning changes; this patch follows that rule with a top-level v2 artifact.

No external library was added.

## Live-path status

live_path_status: transition

The producer path is executable through a deterministic fake process, but the
complete v2 consumer and remote publication chain is intentionally assigned to
the following end-to-end patches. No operational closure is claimed here.
