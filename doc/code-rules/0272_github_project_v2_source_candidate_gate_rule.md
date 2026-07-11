# Règle 0272-r7 — gate locale des SourceCandidate ProjectV2

## Invariants

1. La gate réutilise `SourceCandidateDecision` et
   `apply_source_candidate_decision`.
2. Une décision porte sur une candidate explicitement identifiée dans un lot r6.
3. Le mode execute exige un `policy_decision_id` non vide.
4. `merge` exige un `target_context_id`.
5. Un retrait ProjectV2 est advisory et ne peut être promu ou fusionné.
6. Seuls `promote` et `merge` autorisent un futur consommateur durable.
7. R7 n'effectue pourtant aucune écriture SQL ou Qdrant.
8. Le gate record est immuable et adressé par son contenu.
9. La gate n'effectue aucun appel GitHub et aucune mutation distante.
10. Le mode ProjectV2 natif ne dépend pas du pont Actions optionnel.
11. `Scheduler.run()`, SHM, RouteProxy et ControlProxy restent inchangés.
12. Aucune bibliothèque hors bibliothèque standard n'est ajoutée.

## Revue code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing typed decision, immutable result, gate and IO boundary rules are sufficient
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
non_stdlib_dependency_added: false
```
