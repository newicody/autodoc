# GitHub Copilot advisory response extraction — 0279

## Problem

The GitHub Copilot CLI completed successfully in the controlled research
workflow, but the advisory script rejected its output as `invalid_response`.
The script assumed that stdout was directly the business JSON object, while the
CLI now exposes a structured JSONL transport with one JSON object per line.

## Decision

The existing advisory adapter now requests `--output-format=json` with
`--stream=off`. It scans the JSONL event tree for a response containing the
strict advisory contract. Direct JSON, fenced JSON, and a single JSON object
surrounded by short explanatory text remain accepted for compatibility.

The validated advisory contract remains:

```text
summary: string
suggested_route: string
assumptions: list[string]
questions: list[string]
risks: list[string]
confidence: number in [0, 1]
```

The response digest is computed from canonical validated advisory JSON rather
than transport metadata. Repeated JSONL event metadata therefore does not alter
the artifact identity.

## Security and authority boundaries

- the authoritative GitHub request remains the only authority;
- Copilot output remains `trusted=false` and `usable_as_authority=false`;
- read, write, shell, URL, and memory tools are denied;
- custom repository instructions are disabled for this bounded advisory;
- stdout and stderr content are not copied into failure artifacts;
- no Issue, ProjectV2, SQL, Qdrant, Scheduler, or `Scheduler.run()` mutation is
  introduced;
- no non-stdlib dependency is introduced.
