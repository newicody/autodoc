# Règle 0272-r6 — handoff ProjectV2 local et borné

## Invariants

1. Un change set ProjectV2 est converti en réutilisant `SourceCandidate`.
2. Le nombre de handoffs est borné par `max_handoffs > 0`.
3. Une baseline ne produit aucun handoff par défaut.
4. Un item retiré produit au plus une information advisory ; il ne supprime
   jamais une donnée locale.
5. Chaque handoff exige une gate opérateur avant ingestion durable.
6. Le module et sa CLI n'effectuent aucun appel réseau, aucune mutation GitHub,
   aucune écriture SQL et aucune projection Qdrant.
7. `Scheduler.run()`, SHM, RouteProxy et ControlProxy restent inchangés.
8. Le lot de handoffs est immuable et adressé par le contenu.
9. Aucune bibliothèque hors bibliothèque standard n'est ajoutée.

## Revue code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing typed-command, policy, immutable-result, bounded-work and IO-boundary rules are sufficient
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
non_stdlib_dependency_added: false
```
