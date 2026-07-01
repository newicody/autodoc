# Phase 5.13 — Local context loop CLI

This archive adds a thin manual CLI boundary for the local context loop described in Phase 5.12.

The command consumes an existing Phase 4 E5 artifact directory, attaches it explicitly to a local `ContextEngine`, inspects the E5 status, and renders a text/json report.

It does not rebuild/search E5, does not call OpenVINO, and does not apply any operator decision.

## Usage

```bash
PYTHONPATH=src python3 -m context.local_context_loop_cli /tmp/autodoc_e5_dry_run
PYTHONPATH=src python3 -m context.local_context_loop_cli --format json /tmp/autodoc_e5_dry_run
PYTHONPATH=src python3 -m context.local_context_loop_cli --report-file /tmp/local_context_loop.json /tmp/autodoc_e5_dry_run
```

Optional operator next-action, recorded only in the payload:

```bash
PYTHONPATH=src python3 -m context.local_context_loop_cli \
  --next-action archive \
  --report-file /tmp/local_context_loop.json \
  /tmp/autodoc_e5_dry_run
```

Allowed values:

```text
inspect
relaunch
reject
archive
promote
merge
```

## Boundaries

```text
no E5/OpenVINO execution
no Scheduler living loop
no daemon
no server
no watcher
no network
no GitHub API
no token
no Qdrant
no LLM
no persistent storage
no decision mutation
```

## Dependency policy

No non-stdlib Python dependency was added.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.13 ajoute une CLI manuelle mince au-dessus des contrats existants ; aucune règle de programmation nouvelle n'est nécessaire.
```
