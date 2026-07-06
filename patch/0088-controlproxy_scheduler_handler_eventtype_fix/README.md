# 0088 — ControlProxy Scheduler handler — EventType test fix

## Intention

Correction minimale du test runtime ajouté par 0088.

Le test utilisait `EventType.CONTEXT_UPDATED`, qui n'existe pas dans le contrat `contracts.event` actuel. Le handler 0088 ne dépend pas du type exact de l'événement : il extrait uniquement le payload Scheduler-authorized et délègue à l'adapter `handle_scheduler_route_request()`.

## Changement

- Remplace le type de fixture par `EventType.CONTEXT_REQUEST`, présent dans le contrat actuel.

## Scope volontairement limité

- Pas de CLI.
- Pas de daemon, service ou watcher.
- Pas de changement du loop noyau.
- Pas de contournement policy/zone/scope.
- Pas de nouvelle abstraction.
- Pas de changement de l'implémentation du handler.

## Validation attendue

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q tests/runtime/test_controlproxy_scheduler_handler.py
PYTHONPATH=src:. pytest -q
```

## code_rule review block

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: correction de fixture de test uniquement ; elle conserve le handler 0088 comme frontière Dispatcher importable et ne modifie pas le chemin noyau.
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
